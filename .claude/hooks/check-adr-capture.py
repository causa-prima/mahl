#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): kein Aufschub in einer neu erfassten ADR.

Eine ADR hält eine **entschiedene** Sache fest, von der nach Behebung oder Ablösung ein
terminaler Rest bleibt – etwas, das ohne den Eintrag unverständlich wäre. Ein *Aufschub*
(„machen wir später", „vorerst minimal", „bis zur Erweiterung") ist das Gegenteil: Er
verschwindet mit der Erledigung ersatzlos und gehört deshalb nach `docs/tech-debt.md`.

Der Bestand belegt, dass Lese-Disziplin hier nicht reicht: ADR-S083-1 („Read-Pfad mappt
DB→DTO direkt, ToDomain **aufgeschoben**") und ADR-S083-2 („minimale Modellierung, volle
Union **aufgeschoben**") waren beide Hybride ohne terminalen Rest und mussten in S119 nach
`tech-debt.md` umgehängt werden – ADR-S083-2 hatte sich bis dahin über zwei Addenda
weiterentwickelt und war aus dem TD-Header heraus sogar als Vorbild zitiert worden.

Die Regel ist kanonisch in `CLAUDE.md`, Sektion „Ablage: ADR, TD oder offene Frage?"
(Hybrid-Regel) und in der Aufnahmebedingung im Header von `docs/history/adr.md`.

Scope:
- **Nur** `docs/history/adr.md`; jede andere Datei passiert ungeprüft.
- Geprüft werden **nur neu hinzukommende** ADR-IDs (im Post-Inhalt, nicht im Pre-Inhalt).
  Bestehende Einträge bleiben frei änderbar: Der Bestand trägt Aufschub-Vokabular an Stellen,
  die bewusst so stehen (z.B. Statusverweise auf einen TD-Eintrag), und ein Hook, der jede
  Bearbeitung alter Einträge blockiert, macht das Aufräumen unmöglich.
- **Eintrags-Ausnahme:** ein `adr-ok`-Marker irgendwo im Eintrag hebt die Prüfung für den
  **gesamten** Eintrag auf (bewusste Einzelfälle – z.B. eine ADR, die den Aufschub eines
  *anderen* Artefakts nur zitiert). Bewusst gröber als das zeilenweise `ref-ok`/`dangling-ok`
  der Schwesterhooks: Aufschub-Vokabular verteilt sich über den Fließtext eines Eintrags,
  eine Zeilenausnahme träfe hier regelmäßig daneben. Preis: ein gesetzter Marker deckt auch
  später ergänztes, unbeabsichtigtes Vokabular im selben Eintrag mit ab.

Bewusst NICHT im Vokabular: `YAGNI` und `minimal`. Beide begründen häufig eine **dauerhafte**
Entscheidung („wir bauen X nicht") und wären als Aufschub-Marker Fehlalarm-Quellen. Der
Unterschied liegt nicht im Sparsamkeits-Argument, sondern in der Zeitaussage.

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hook_io import compute_post_content, read_file_text  # noqa: E402

ADR_FILE = "docs/history/adr.md"

_ENTRY_SPLIT_RE = re.compile(r"^### (ADR-S\d+-\d+)", re.M)
_ADR_OK = "adr-ok"

# Aufschub-Vokabular: explizite Zeitaussagen „nicht jetzt, aber später".
# Jeder Eintrag ist eine Wendung, die im Bestand tatsächlich einen Hybrid markiert hat
# oder die Hybrid-Regel in CLAUDE.md wörtlich nennt.
#
# `re.IGNORECASE`, weil deutsche Sätze satzinitial großschreiben: „Zunächst wird X verschoben."
# hätte die rein kleingeschriebenen Muster sonst passiert – genau die Formulierung, in der ein
# Aufschub in Entscheidungsprosa typischerweise auftritt.
#
# Bewusst NICHT im Vokabular:
#   - `YAGNI`, `minimal` – begründen häufig eine **dauerhafte** Entscheidung („wir bauen X nicht").
#   - `zunächst` – trägt keine Zeitaussage über die Zukunft, sondern erzählt oft Vorgeschichte
#     („X erzwang zunächst Y, dann wurde es entfernt", `adr.md`). Genau die Bauform der
#     „Verworfen:"-Abschnitte, die jede ADR hier trägt. Der Katalog in `CLAUDE.md` nennt es
#     ebenfalls nicht; es war eine Ausweitung ohne Deckung.
_DEFERRAL_PATTERNS = (
    r"aufgeschoben|aufzuschieben|aufschieben|Aufschub",
    r"vertagt|vertagen",
    r"vorerst|vorläufig|bis auf weiteres",
    r"bis zur (?:Erweiterung|Umsetzung|Einführung)",
    r"technische[rn]? Schuld",
    r"in diesem Zyklus (?:nicht|noch nicht)",
    r"noch nicht (?:implementiert|umgesetzt|gebaut)",
    r"später (?:umgesetzt|implementiert|nachgezogen|erweitert)",
)
_DEFERRAL_RE = re.compile("|".join(_DEFERRAL_PATTERNS), re.IGNORECASE)


def is_adr_file(file_path: str) -> bool:
    """True nur für das ADR-Archiv selbst (absolut wie repo-relativ angegeben)."""
    return Path(file_path).as_posix().endswith(ADR_FILE)


def parse_adr_entries(content: str) -> dict[str, str]:
    """ADR-ID → Eintrags-Rumpf (alles zwischen dieser und der nächsten Eintrags-Überschrift)."""
    parts = _ENTRY_SPLIT_RE.split(content)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def deferral_hits(body: str) -> list[str]:
    """Gefundene Aufschub-Wendungen, ohne Dubletten und in Fundreihenfolge."""
    seen: dict[str, None] = {}
    for match in _DEFERRAL_RE.finditer(body):
        seen.setdefault(match.group(0), None)
    return list(seen)


def find_violations(pre: str, post: str) -> list[tuple[str, list[str]]]:
    """(ADR-ID, Aufschub-Wendungen) für jeden neu erfassten Eintrag mit Aufschub."""
    known = parse_adr_entries(pre).keys()
    return [
        (aid, hits)
        for aid, body in parse_adr_entries(post).items()
        if aid not in known and _ADR_OK not in body and (hits := deferral_hits(body))
    ]


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not file_path or not is_adr_file(file_path):
        return None

    pre = read_file_text(file_path)
    post = compute_post_content(tool, tool_input, pre)
    if post is None:
        return None

    violations = find_violations(pre, post)
    if not violations:
        return None

    lines = "\n".join(
        f"  - {aid}: {', '.join(f'„{h}“' for h in hits)}" for aid, hits in violations
    )
    return (
        "❌ ADR-Erfassung (Poka-Yoke): neu erfasste ADR trägt Aufschub-Vokabular:\n"
        f"{lines}\n"
        "  Eine ADR trägt keinen Aufschub. Operativer Test: „Ist die Sache erledigt – bleibt "
        "dann etwas zu erklären übrig, das ohne diesen Eintrag unverständlich wäre?“\n"
        "  - Ja → ADR. Der Eintrag wird `Superseded` und bleibt stehen.\n"
        "  - Nein → `docs/tech-debt.md`. Der Eintrag verschwindet mit der Behebung ersatzlos.\n"
        "  Ist die Entscheidung teils terminal, teils aufgeschoben, wird der Aufschub-Teil ein "
        "eigener TD-Eintrag; die ADR behält nur den terminalen Rest. Bleibt kein terminaler "
        "Rest, war es nie eine ADR.\n"
        "  Kanonisch: `CLAUDE.md`, Sektion „Ablage: ADR, TD oder offene Frage?“. Präzedenz: "
        "ADR-S083-1 und ADR-S083-2 waren genau solche Hybride und wurden in S119 nach "
        "`tech-debt.md` umgehängt.\n"
        "  Bewusster Einzelfall (z.B. eine ADR, die den Aufschub eines anderen Artefakts nur "
        "zitiert) → `adr-ok`-Marker irgendwo in den Eintrag."
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    try:
        reason = check(data)
        if reason:
            print(reason, file=sys.stderr)
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-adr-capture: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
