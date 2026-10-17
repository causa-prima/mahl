#!/usr/bin/env python3
"""Was der Freigabedialog zu einem Tracker-Schreibbefehl sagt – und was ein Tracker-Befehl ist.

Warum (OBS-S116-1): Seit S114 entstehen Einträge über `obs.py`/`lessons.py` statt über `Edit`.
Das spart den erzwungenen Vor-Edit-Read der ganzen Datei (CM-S114-2), kostet aber die
Prüfbarkeit: Ein `Edit` zeigt im Freigabedialog einen Diff, ein Script-Aufruf nur eine lange
Kommandozeile. Den Diff zeigt heute der Mod `tracker-diff` im Pane neben dem Prompt
(`tracker_diff.py`); den Prompt selbst kann kein Mod gestalten.

`vorschau()` liefert dafür nur die Kopfzeile für `permissionDecisionReason`: Werkzeug, Eintrag,
Datei. Sie bleibt, damit ohne Pane – Mod aus, Terminal zu schmal, andere Oberfläche – wenigstens
zu sehen ist, was angefasst wird; dazu die beiden Warnungen, die auch ohne Diff zählen.

**Was der Kanal trägt** – am echten Dialog gemessen, S124 und S129: Zeilenumbrüche und Unicode
ja, Markdown nie, ANSI seit S129 nicht mehr (Terminal-Escapes erscheinen als Bytes, im
Changelog von Claude Code steht dazu nichts). Darum keine Auszeichnung außer `⚠`.

Bewusst OHNE Trockenlauf des Scripts: Ein PreToolUse-Hook, der den vom Agenten gelieferten
Befehl ausführt, wäre eine Lücke im Sicherungsmechanismus selbst – eine Kommando-Substitution
im Argument liefe schon bei der Vorschau. Hier wird nur `shlex`-geparst. Genau daraus folgt die
Metazeichen-Warnung: `shlex` behandelt Backticks und `$(…)` als Literal, die echte Shell führt
sie aus. Weicht beides ab, ist das der stille Korruptionspfad aus S117.
"""
import re
import shlex

# Rohe Zeichen, die die Shell auswertet, bevor das Script sie sieht.
_METAZEICHEN = re.compile(r"[`]|\$\(")
_EINTRAG_ID = re.compile(r"(OBS|LL|OQ|TD)-S\d+-\d+")

# Welches Werkzeug in welche Datei schreibt (`td` zusätzlich, bei `Fällig: jetzt`, in
# AGENT_MEMORY – das zeigt der Diff im Pane).
_TRACKER = {
    "obs": "docs/kaizen/observations.md",
    "lessons": "docs/kaizen/lessons_learned.md",
    "oq": "docs/open-questions.md",
    "td": "docs/tech-debt.md",
}

_SCHREIBT = ("add", "set", "remove")

_PANE = "Änderung im Pane (Mod tracker-diff)"
_ERSATZLOS = "⚠ Löscht den Eintrag ersatzlos – die Datei behält keine Kopie."
_SHELL = ("⚠ Shell-Metazeichen im Befehl (` oder $(…)): Die Shell wertet sie aus, bevor das "
          "Script sie sieht – der geschriebene Text kann vom Befehl abweichen.")


def _werkzeugname(wort: str) -> str:
    """Der Werkzeugname aus jeder Aufrufform: `prozesscode.oq`, `prozesscode/oq.py`, `oq.py`.

    Der Pfadaufruf scheitert heute an den paketinternen Importen; er bleibt trotzdem erkannt,
    damit die Vorschau nicht ausfällt, falls er je wieder möglich wird.
    """
    return wort.rsplit("/", 1)[-1].removesuffix(".py").rsplit(".", 1)[-1]


def schreibaufruf(command: str) -> tuple[str, str, list[str]] | None:
    """(Werkzeug, Unterbefehl, Argumente danach) eines Tracker-Schreibbefehls, sonst None.

    Nur `shlex`-geparst, nie ausgeführt (siehe Modul-Docstring). None auch bei einer
    unparsbaren Kommandozeile – lieber keine Auskunft als eine falsche.
    """
    try:
        teile = shlex.split(command)
    except ValueError:
        return None
    for i, wort in enumerate(teile):
        if _werkzeugname(wort) in _TRACKER:
            unterbefehl = teile[i + 1] if i + 1 < len(teile) else None
            if unterbefehl not in _SCHREIBT:
                return None
            return _werkzeugname(wort), unterbefehl, teile[i + 2:]
    return None


def _eintrag(argumente: list[str]) -> str | None:
    """Die Eintrags-ID unter den Positionsargumenten – nicht der Wert einer Option (`--bezug`)."""
    i = 0
    while i < len(argumente):
        if argumente[i].startswith("--"):
            i += 2
            continue
        if _EINTRAG_ID.fullmatch(argumente[i]):
            return argumente[i]
        i += 1
    return None


def _ausgewertet(command: str) -> str:
    """Der Befehl ohne die Teile, die die Shell wörtlich nimmt: einfach gequoteten Text und
    mit Backslash maskierte Zeichen. Was übrig bleibt, wertet sie aus."""
    aus, i, doppelt = [], 0, False
    while i < len(command):
        c = command[i]
        if c == "\\":
            i += 2
            continue
        if c == "'" and not doppelt:
            ende = command.find("'", i + 1)
            i = len(command) if ende < 0 else ende + 1
            continue
        if c == '"':
            doppelt = not doppelt
        aus.append(c)
        i += 1
    return "".join(aus)


def metazeichen(command: str) -> bool:
    """Wertet die Shell im Befehl etwas aus, bevor das Script es sieht?"""
    return bool(_METAZEICHEN.search(_ausgewertet(command)))


def vorschau(command: str) -> str | None:
    """Kopfzeile und Warnungen für den Freigabedialog – None, wenn kein Tracker-Schreibbefehl."""
    aufruf = schreibaufruf(command)
    if aufruf is None:
        return None
    werkzeug, unterbefehl, argumente = aufruf
    ziel = " ".join(t for t in (werkzeug, unterbefehl, _eintrag(argumente)) if t)
    zeilen = [f"{ziel} → {_TRACKER[werkzeug]} · {_PANE}"]
    if unterbefehl == "remove":
        zeilen.append(_ERSATZLOS)
    if metazeichen(command):
        zeilen.append(_SHELL)
    return "\n".join(zeilen)
