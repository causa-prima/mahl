#!/usr/bin/env python3
"""Was ein Tracker-Schreibbefehl ändern würde – fertig zum Zeichnen, für den Mod `tracker-diff`.

Warum: Der Freigabedialog zeigt bei `obs|lessons|td|oq add|set|remove` nur die Vorschau aus
`tracker_preview` – Feldwerte, einfarbig, im Prompt selbst, den kein Mod umgestalten kann. Der
Mod `.claude/mods/tracker-diff` zeigt daneben im Pane, was sich ändert; berechnet wird es hier,
damit die Logik mit pytest getestet ist und der Mod nur zeichnet.

**Exakt per Konstruktion:** Das echte `main()` des Werkzeugs läuft im eigenen Prozess, nur
`Path.write_text` ist abgefangen und schreibt nicht. Der Diff entsteht so aus genau dem Code,
der nach der Freigabe läuft – auch eine zweite Datei (`td` pflegt AGENT_MEMORY mit). Eine Shell
ist nicht beteiligt: Die Kommandozeile ist nur `shlex`-geparst, wie in `tracker_preview`.

**Dargestellt** wird je Datei eine Liste von Blöcken: `kopf` (die Überschrift des betroffenen
Eintrags), `geaendert` (eine Zeile mit Wort-Diff), `neu` und `weg` (ganze Zeilen). Jede Zeile
ist eine Liste von Stücken `{text, stil}`, `stil` ⊆ {fett, code, kursiv, weg, neu}. Das Markdown
der Tracker ist dabei aufgelöst – der kleine Teil, den sie nutzen; alles andere bleibt Rohtext.

Aufruf (vom Mod): Befehl auf stdin, JSON auf stdout – `null` für keinen Tracker-Schreibbefehl,
sonst `{"dateien": [{"datei", "bloecke"}], "fehler", "warnung"}`.
"""
import argparse
import contextlib
import difflib
import io
import json
import re
import sys
from importlib import import_module
from pathlib import Path
from unittest import mock

from . import tracker_preview
from ._util import REPO_ROOT

_WARNUNG = ("Shell-Metazeichen im Befehl (` oder $(…)): Die Shell wertet sie aus, bevor das "
            "Script sie sieht – der Diff zeigt sie wörtlich.")


# Inline-Markdown, das die Tracker nutzen: Code (geht vor), fett, kursiv mit `*`, Links. Kursiv
# mit `_` bewusst nicht – es träfe Bezeichner wie `check_name`.
_INLINE = re.compile(r"(`+)(.+?)\1"
                     r"|\*\*(?=\S)(.+?)(?<=\S)\*\*"
                     r"|(?<![\w*])\*(?=[^\s*])([^*]+?)(?<=\S)\*(?![\w*])"
                     r"|\[([^\]]+)\]\([^)\s]+\)")
_UEBERSCHRIFT = re.compile(r"^#{1,6}\s+")
_LISTE = re.compile(r"^(\s*)[-*]\s+")
# Feldname einer Listenzeile (`- Status: NEU`, LL `  - Was: …`) – in TD/OQ steht er schon fett.
_FELDNAME = re.compile(r"^[A-ZÄÖÜ][\w/()-]*(?: [\w/()-]+){0,3}:(?=\s|$)")
# Wo ein Eintrag beginnt: `## OBS-…`/`## TD-…`/`## OQ-…` oder die LL-Kopfzeile `- **[HOCH] …`.
_EINTRAGSKOPF = re.compile(r"^(## |- \*\*\[)")
_WORT = re.compile(r"\s+|\w+|[^\w\s]")

Zeichen = list[tuple[str, frozenset]]


def _inline(text: str, basis: frozenset) -> Zeichen:
    aus, pos = [], 0
    for m in _INLINE.finditer(text):
        aus += [(c, basis) for c in text[pos:m.start()]]
        stil, inhalt = next((s, m.group(g)) for s, g in (("code", 2), ("fett", 3), ("kursiv", 4),
                                                         (None, 5)) if m.group(g) is not None)
        aus += [(c, basis | {stil} if stil else basis) for c in inhalt]
        pos = m.end()
    return aus + [(c, basis) for c in text[pos:]]


def _zeichen(zeile: str) -> Zeichen:
    """Jedes gezeigte Zeichen der Zeile mit seinen Markdown-Stilen."""
    basis = frozenset()
    if m := _UEBERSCHRIFT.match(zeile):
        zeile, basis = zeile[m.end():], frozenset({"fett"})
    aus: Zeichen = []
    if m := _LISTE.match(zeile):
        aus = [(c, basis) for c in m.group(1) + "• "]
        zeile = zeile[m.end():]
        if feld := _FELDNAME.match(zeile):
            aus += [(c, basis | {"fett"}) for c in feld.group()]
            zeile = zeile[feld.end():]
    return aus + _inline(zeile, basis)


def _stuecke(zeichen: Zeichen) -> list[dict]:
    aus: list[dict] = []
    for c, stil in zeichen:
        if aus and aus[-1]["_stil"] == stil:
            aus[-1]["text"] += c
        else:
            aus.append({"text": c, "_stil": stil})
    return [{"text": s["text"], "stil": sorted(s.pop("_stil"))} for s in aus]


def markdown(zeile: str) -> list[dict]:
    """Eine Zeile mit aufgelöstem Markdown – Unbekanntes bleibt Rohtext."""
    return _stuecke(_zeichen(zeile))


def _wort_ops(alt: list[str], neu: list[str]) -> list[tuple]:
    """Die Wort-Opcodes, mit Leerraum zwischen zwei Änderungen der Änderung zugeschlagen.

    Sonst zerfiele ein ersetzter Satz an jedem gleichen Leerzeichen in Wortsalat.
    """
    ops = difflib.SequenceMatcher(None, alt, neu, autojunk=False).get_opcodes()
    zusammen: list[list] = []
    for i, (op, i1, i2, j1, j2) in enumerate(ops):
        nur_leer = op == "equal" and all(not t.strip() for t in alt[i1:i2])
        zwischen = 0 < i < len(ops) - 1 and ops[i - 1][0] != "equal" and ops[i + 1][0] != "equal"
        art = "replace" if nur_leer and zwischen else op
        if zusammen and art != "equal" and zusammen[-1][0] != "equal":
            zusammen[-1][2], zusammen[-1][4] = i2, j2
        else:
            zusammen.append([art, i1, i2, j1, j2])
    return zusammen


def wort_diff(alt: str, neu: str) -> list[dict]:
    """Eine geänderte Zeile: Gleiches aus der neuen Zeile, Gestrichenes `weg`, Neues `neu`."""
    za, zn = _zeichen(alt), _zeichen(neu)
    ta = [m.span() for m in _WORT.finditer("".join(c for c, _ in za))]
    tn = [m.span() for m in _WORT.finditer("".join(c for c, _ in zn))]
    text_a, text_n = "".join(c for c, _ in za), "".join(c for c, _ in zn)
    aus: Zeichen = []
    for op, i1, i2, j1, j2 in _wort_ops([text_a[s:e] for s, e in ta], [text_n[s:e] for s, e in tn]):
        if op == "equal":
            aus += zn[tn[j1][0]:tn[j2 - 1][1]]
            continue
        if i2 > i1:
            aus += [(c, s | {"weg"}) for c, s in za[ta[i1][0]:ta[i2 - 1][1]]]
        if j2 > j1:
            aus += [(c, s | {"neu"}) for c, s in zn[tn[j1][0]:tn[j2 - 1][1]]]
    return _stuecke(aus)


# Ab wann zwei Zeilen als Wort-Diff gezeigt werden. Darunter teilen sie meist nur Füllwörter
# („den", „–", „.") – verschränkt wäre der neue Text quer durch den alten verstreut.
_AEHNLICH_AB = 0.5


def _aehnlich(alt: str, neu: str) -> bool:
    woerter = [[w for w in _WORT.findall(z) if w.strip()] for z in (alt, neu)]
    return difflib.SequenceMatcher(None, *woerter, autojunk=False).ratio() >= _AEHNLICH_AB


def _kopf_vor(zeilen: list[str], index: int) -> str | None:
    return next((z for z in reversed(zeilen[:index]) if _EINTRAGSKOPF.match(z)), None)


def _zeilenblock(art: str, zeilen: list[str]) -> dict | None:
    while zeilen and not zeilen[0].strip():
        zeilen = zeilen[1:]
    while zeilen and not zeilen[-1].strip():
        zeilen = zeilen[:-1]
    return {"art": art, "zeilen": [markdown(z) for z in zeilen]} if zeilen else None


def bloecke(alt: str, neu: str) -> list[dict]:
    """Die Änderung von `alt` nach `neu` als Blöcke (siehe Modul-Docstring)."""
    za, zn = alt.splitlines(), neu.splitlines()
    aus: list[dict] = []
    letzter_kopf = None
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, za, zn, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        betroffen = za[i1:i2] + zn[j1:j2]
        kopf = _kopf_vor(zn, j1) if j2 > j1 else _kopf_vor(za, i1)
        # Bringt die Änderung ihre Überschrift selbst mit, zeigt sie sie auch selbst.
        if kopf and kopf != letzter_kopf and not any(_EINTRAGSKOPF.match(z) for z in betroffen):
            aus.append({"art": "kopf", "zeilen": [markdown(kopf)]})
            letzter_kopf = kopf
        paare = min(i2 - i1, j2 - j1)
        for a, n in zip(za[i1:i1 + paare], zn[j1:j1 + paare], strict=True):
            if not (a.strip() or n.strip()):
                continue
            if _aehnlich(a, n):
                aus.append({"art": "geaendert", "zeilen": [wort_diff(a, n)]})
            else:
                aus += [{"art": "weg", "zeilen": [markdown(a)]},
                        {"art": "neu", "zeilen": [markdown(n)]}]
        for art, rest in (("weg", za[i1 + paare:i2]), ("neu", zn[j1 + paare:j2])):
            if block := _zeilenblock(art, rest):
                aus.append(block)
    return aus


def _relativ(pfad: Path, root: Path) -> str:
    try:
        return pfad.relative_to(root).as_posix()
    except ValueError:
        return str(pfad)


def befund(command: str, root: Path = REPO_ROOT) -> dict | None:
    """Was der Befehl schriebe – None, wenn er kein Tracker-Schreibbefehl ist."""
    aufruf = tracker_preview.schreibaufruf(command)
    if aufruf is None:
        return None
    werkzeug, unterbefehl, argumente = aufruf

    geschrieben: dict[Path, str] = {}

    def abfangen(pfad, daten, *_args, **_kwargs):
        geschrieben[Path(pfad)] = daten
        return len(daten)

    fehler = io.StringIO()
    with mock.patch.object(Path, "write_text", abfangen), \
            mock.patch.object(sys, "argv", [f"prozesscode.{werkzeug}", unterbefehl, *argumente]), \
            contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(fehler):
        try:
            code = import_module(f"prozesscode.{werkzeug}").main()
        except SystemExit as ende:
            code = ende.code

    warnung = _WARNUNG if tracker_preview.metazeichen(command) else None
    if code not in (None, 0):
        return {"dateien": [], "fehler": fehler.getvalue().strip() or f"Exit {code}",
                "warnung": warnung}
    dateien = [{"datei": _relativ(pfad, root),
                "bloecke": bloecke(pfad.read_text(encoding="utf-8") if pfad.exists() else "", neu)}
               for pfad, neu in geschrieben.items()]
    return {"dateien": dateien, "fehler": None, "warnung": warnung}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__,
                            formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    print(json.dumps(befund(sys.stdin.read().strip()), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
