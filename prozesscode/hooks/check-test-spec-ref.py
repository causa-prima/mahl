#!/usr/bin/env python3
"""PreToolUse-Pflichtfeld (blockierend): Ein neuer Komponenten-/Integrationstest nennt seine Spec.

Warum (CM-S070-1, Review-Fix-Pfad): In einem Review-Fix entstanden Tests für Verhalten, das
kein Szenario-Beispiel nannte – einer davon eine Verhaltensänderung. Die Regel
„Szenario vor dem Fix" stand im Skill und wurde übergangen. Der Test-Freigabe-Audit sieht so
etwas nicht: Ein Review-Fix läuft über einen eigenen Test-Review und bekommt einen eigenen
Freigabe-Anker. Deshalb setzt dieser Hook dort an, wo der Test entsteht.

Jeder NEUE Testfall (Name kommt im Nachzustand vor, im Vorzustand nicht) in
`Client/src/**/*.test.ts(x)` oder `Server.Tests/**/*.cs` trägt im Kommentarblock direkt darüber:

- `// Szenario: <Titel>` – der Titel existiert wörtlich in `features/`;
- bei einem Szenariogrundriss zusätzlich `// Beispiel: <Zeile>` – eine Zeile der Beispieltabelle
  dieses Grundrisses (Zellen mit `|` getrennt, äußere Striche optional) oder `alle`;
- oder, nur ohne US-Tag im Namen, `// ADR-SNNN-N` auf eine existierende ADR (Querschnitts- und
  Invarianten-Tests, ADR-S106-3).

**Grenze, bewusst benannt:** Der Hook prüft, DASS eine existierende Spec genannt ist, nicht ob
sie den Fall inhaltlich deckt. Ein einfaches Szenario, das den Fall nicht erwähnt, kommt durch.
Er ersetzt das Urteil des Test-Reviews nicht, er gibt ihm einen Anker: Ob dieser Test zu genau
dieser Zeile passt, ist nachprüfbar; welche Spec ein Test ohne Verweis meint, war es nicht.

Bestandstests bleiben ungeprüft – nur neue Namen zählen; ein umbenannter Test gilt als neu.
Umbenennen eines Szenarios in `features/` prüft dieser Hook nicht (anders als
`check-e2e-scenario-ref` für E2E-Specs). Fail-open liegt beim Dispatcher.
"""
import re
from pathlib import Path

from .._feature import parse_feature
from .._test_inventory import parse_csharp, parse_typescript
from ._hook_io import edit_zustand

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_DIR = _REPO_ROOT / "features"
_ADR_FILE = _REPO_ROOT / "docs" / "history" / "adr.md"

_TS_TEST_RE = re.compile(r"Client[/\\]src[/\\].*\.test\.tsx?$")
_CS_TEST_RE = re.compile(r"Server\.Tests[/\\].*\.cs$")
_US_TAG_RE = re.compile(r"^US\d+_")
_SZENARIO_RE = re.compile(r"^//\s*Szenario:\s*(.+?)\s*$")
_BEISPIEL_RE = re.compile(r"^//\s*Beispiel:\s*(.+?)\s*$")
_ADR_RE = re.compile(r"^//\s*(ADR-S\d{3}-\d+)\b")
_ADR_KOPF_RE = re.compile(r"^### (ADR-S\d{3}-\d+)", re.MULTILINE)
_CS_ATTRIBUT_RE = re.compile(r"^\[.*\]$")
ALLE = "alle"


def betrifft(file_path: str) -> bool:
    return bool(_TS_TEST_RE.search(file_path) or _CS_TEST_RE.search(file_path))


def _testfaelle(file_path: str, text: str) -> dict[str, int]:
    """Testname → Startzeile (0-basiert); Suiten zählen nicht."""
    lines = text.splitlines()
    parser = parse_csharp if _CS_TEST_RE.search(file_path) else parse_typescript
    return {e.name: e.start - 1 for e in parser(lines) if not e.ist_suite}


def _kommentarblock(lines: list[str], start: int) -> list[str]:
    """Kommentarzeilen direkt über `start`, in Lesereihenfolge; Leerzeilen und C#-Attribute
    werden übersprungen, die erste andere Zeile beendet den Block (ein `describe` darüber gilt
    nicht)."""
    block: list[str] = []
    for zeile in reversed(lines[:start]):
        s = zeile.strip()
        if s.startswith("//"):
            block.append(s)
        elif s and not _CS_ATTRIBUT_RE.match(s):
            break
    return block[::-1]


def _zellen(zeile: str) -> tuple[str, ...]:
    return tuple(z.strip() for z in zeile.strip().strip("|").split("|"))


def _szenarien(features: list[str]) -> dict[str, set[tuple[str, ...]] | None]:
    """Titel → Beispielzeilen (ohne Kopfzeile) bei einem Grundriss, None bei einem Szenario."""
    ergebnis: dict[str, set[tuple[str, ...]] | None] = {}
    for text in features:
        for s in parse_feature(text)[2]:
            if not s["lines"][0].strip().startswith("Scenario Outline:"):
                ergebnis[s["title"]] = None
                continue
            tabelle = [z for z in s["lines"] if z.strip().startswith("|")]
            ergebnis[s["title"]] = {_zellen(z) for z in tabelle[1:]}
    return ergebnis


def _pruefe_testfall(name: str, block: list[str], szenarien: dict, adrs: set[str]) -> list[str]:
    titel = [m.group(1) for z in block if (m := _SZENARIO_RE.match(z))]
    beispiele = [m.group(1) for z in block if (m := _BEISPIEL_RE.match(z))]
    adr = next((m.group(1) for z in block if (m := _ADR_RE.match(z))), None)
    if not titel:
        if adr is None:
            return [OHNE_VERWEIS.format(test=name)]
        if _US_TAG_RE.match(name):
            return [US_TAG_OHNE_SZENARIO.format(test=name)]
        return [] if adr in adrs else [ADR_UNBEKANNT.format(test=name, adr=adr)]
    meldungen = []
    for t in titel:
        if t not in szenarien:
            meldungen.append(SZENARIO_FEHLT.format(test=name, titel=t))
            continue
        zeilen = szenarien[t]
        if zeilen is None:
            continue
        if not beispiele:
            meldungen.append(BEISPIEL_FEHLT.format(test=name, titel=t))
        meldungen += [BEISPIEL_UNBEKANNT.format(test=name, beispiel=b, titel=t)
                      for b in beispiele if b != ALLE and _zellen(b) not in zeilen]
    return meldungen


def verstoesse(file_path: str, pre: str, post: str, features: list[str], adrs: set[str]) -> list[str]:
    """Meldungen für jeden neuen Testfall im Nachzustand ohne gültigen Spec-Verweis."""
    alt = _testfaelle(file_path, pre)
    neu = {n: i for n, i in _testfaelle(file_path, post).items() if n not in alt}
    if not neu:
        return []
    lines = post.splitlines()
    szenarien = _szenarien(features)
    return [m for name, start in neu.items()
            for m in _pruefe_testfall(name, _kommentarblock(lines, start), szenarien, adrs)]


def _features() -> list[str]:
    return [p.read_text(encoding="utf-8") for p in sorted(_FEATURES_DIR.glob("**/*.feature"))]


def _adrs() -> set[str]:
    return set(_ADR_KOPF_RE.findall(_ADR_FILE.read_text(encoding="utf-8")))


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    zustand = edit_zustand(data, betrifft)
    if zustand is None:
        return None
    file_path, pre, post = zustand
    meldungen = verstoesse(file_path, pre, post, _features(), _adrs())
    if not meldungen:
        return None
    return KOPF + "\n".join(f"  - {m}" for m in meldungen) + "\n" + AUSWEG


OHNE_VERWEIS = ("Test „{test}“ nennt keine Spec – darüber fehlt `// Szenario: <Titel>` "
                "(bzw. ohne US-Tag `// ADR-SNNN-N`).")
SZENARIO_FEHLT = "Test „{test}“: `// Szenario: {titel}` – kein Szenario dieses Titels in features/."
BEISPIEL_FEHLT = ("Test „{test}“: „{titel}“ ist ein Szenariogrundriss – `// Beispiel: <Zeile>` "
                  "(oder `alle`) fehlt.")
BEISPIEL_UNBEKANNT = ("Test „{test}“: `// Beispiel: {beispiel}` steht nicht in der Beispieltabelle "
                      "von „{titel}“.")
US_TAG_OHNE_SZENARIO = ("Test „{test}“ trägt einen US-Tag, nennt aber nur eine ADR – ein US-Tag "
                        "braucht ein Szenario (ADR-Verweis gilt nur für Querschnittstests ohne Tag).")
ADR_UNBEKANNT = "Test „{test}“: `// {adr}` – diese ADR gibt es nicht (docs/history/adr.md)."
KOPF = "❌ Neuer Test ohne gültige Spec (CM-S070-1):\n"
AUSWEG = (
    "  Deckt kein Szenario-Beispiel den Fall, gehört es VOR dem Test ins Feature-File – mit "
    "User-Freigabe (gherkin-workshop, Freigabestufe); ist das zu groß für diesen Lauf, den Test "
    "zurückstellen. Querschnitts-/Invarianten-Tests ohne Szenario: ohne US-Tag, mit "
    "`// ADR-SNNN-N` (ADR-S106-3). Format: docs/process/tdd-process.md#TDD-spec-verweis."
)
