#!/usr/bin/env python3
"""Lesbare Vorschau eines Tracker-Schreibbefehls – für den Freigabedialog.

Warum (OBS-S116-1): Seit S114 entstehen Einträge über `obs.py`/`lessons.py` statt über
`Edit`. Das spart den erzwungenen Vor-Edit-Read der ganzen Datei (CM-S114-2), kostet aber
die Prüfbarkeit: Ein `Edit` zeigt im Freigabedialog einen Diff, ein Script-Aufruf nur eine
lange Kommandozeile. Bei `set` ist zusätzlich der Ausgangszustand unsichtbar – aus dem
Aufruf allein ist nicht ablesbar, was ersetzt wird.

`vorschau()` schließt die Lücke: Sie erzeugt aus der Kommandozeile plus dem aktuellen
Dateiinhalt einen Vorher/Nachher-Block, den `check-bash-permission.py` als
`permissionDecisionReason` mitgibt. Empirisch geprüft (S124): Dieser Kanal überträgt
mehrzeiligen Text, Einrückung, Unicode und ANSI-Styling, aber **kein** Markdown.

Bewusst OHNE Trockenlauf des Scripts: Ein PreToolUse-Hook, der den vom Agenten gelieferten
Befehl ausführt, wäre eine Lücke im Sicherungsmechanismus selbst – eine Kommando-Substitution
im Argument liefe schon bei der Vorschau. Hier wird nur `shlex`-geparst und die Datei gelesen.
Genau daraus folgt die Metazeichen-Warnung: `shlex` behandelt Backticks und `$(…)` als
Literal, die echte Shell führt sie aus. Weicht beides ab, ist das der stille Korruptionspfad
aus S117 – dann sagt die Vorschau es an, statt still das Falsche zu zeigen.
"""
import re
import shlex
from pathlib import Path

FETT, GRUEN, ROT, GRAU, AUS = "\x1b[1m", "\x1b[32m", "\x1b[31m", "\x1b[90m", "\x1b[0m"

# Rohe Zeichen, die die Shell auswertet, bevor das Script sie sieht.
_METAZEICHEN = re.compile(r"[`]|\$\(")

# Welches Script schreibt in welche Datei, und welches Argument trägt welches Feld.
# Diese Abbildung ist die Grammatik, die alle Tracker teilen sollen – Abweichungen sind
# hier sichtbar und damit korrigierbar.
_ARGUMENT_ZU_FELD = {
    "--status": "Status",
    "--entscheidung": "Entscheidung/Maßnahme",
    "--zusammen-erledigen": "Zusammen-erledigen",
    "--beobachtung-anhängen": "Beobachtung",
    "--beobachtung": "Beobachtung",
    "--titel": "Titel",
    "--quelle": "Quelle",
    "--impact": "Impact",
    "--haeufigkeit": "Häufigkeit",
    "--kategorie": "Kategorie",
    "--kontext": "Kontext",
    "--bezug": "Bezug",
    "--vorprägung": "Vorprägung",
    "--was": "Was",
    "--warum": "Warum",
    "--regel": "Regel",
    "--cm-bezug": "CM-Bezug",
    "--frage": "Frage",
    "--faellig": "Fällig",
    "--hintergrund": "Hintergrund",
    "--problem": "Problem",
    "--behebung": "Behebung",
    "--done": "Done-Kriterium (AGENT_MEMORY)",
}

# Script → (Datei, Muster der Eintrags-Kopfzeile, Muster einer Feldzeile).
# Das Feldmuster ist je Tracker verschieden (`- Feld:` gegen `**Feld:**`) – die Vereinheitlichung
# wäre eine Migration der Bestandsdateien und steht hier bewusst nicht an.
_TRACKER = {
    "obs.py": ("docs/kaizen/observations.md", r"^## (OBS-S\d+-\d+)", r"^- {feld}:\s*(.*)$"),
    "lessons.py": ("docs/kaizen/lessons_learned.md", r"\*\*\[.*?\] (LL-S\d+-\d+)",
                   r"^\s*- {feld}:\s*(.*)$"),
    "oq.py": ("docs/open-questions.md", r"^## (OQ-S\d+-\d+)", r"^\*\*{feld}:\*\*\s*(.*)$"),
    "td.py": ("docs/tech-debt.md", r"^## (TD-S\d+-\d+)", r"^\*\*{feld}:\*\*\s*(.*)$"),
}

_SCHREIBT = ("add", "set", "remove")
_UMBRUCH = 96


def _argumente(teile: list[str]) -> tuple[str | None, list[tuple[str, str]]]:
    """(Eintrags-ID, [(Feldname, Wert)]) aus den Argumenten nach dem Unterbefehl."""
    eintrag, felder = None, []
    i = 0
    while i < len(teile):
        wort = teile[i]
        if wort.startswith("--"):
            feld = _ARGUMENT_ZU_FELD.get(wort)
            wert = teile[i + 1] if i + 1 < len(teile) else ""
            if feld is not None:
                felder.append((feld, wert))
            i += 2
            continue
        if eintrag is None and re.fullmatch(r"(OBS|LL|OQ|TD)-S\d+-\d+", wort):
            eintrag = wort
        i += 1
    return eintrag, felder


def _block(text: str, eintrag: str, id_muster: str) -> str | None:
    """Der Textabschnitt eines Eintrags – von seiner Kopfzeile bis zur nächsten."""
    kopf = re.compile(id_muster, re.M)
    treffer = list(kopf.finditer(text))
    for i, m in enumerate(treffer):
        if m.group(1) == eintrag:
            ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
            return text[m.start():ende]
    return None


def _alter_wert(block: str, feld: str, feld_muster: str) -> str | None:
    m = re.search(feld_muster.format(feld=re.escape(feld)), block, re.M)
    return m.group(1).strip() if m else None


def _umbrechen(wert: str, einzug: str) -> list[str]:
    """Lange Werte auf lesbare Zeilen – der Dialog kürzt nicht, aber er bricht auch nicht um."""
    zeilen, rest = [], " ".join(wert.split())
    if not rest:
        return [einzug + GRAU + "(leer)" + AUS]
    while rest:
        if len(rest) <= _UMBRUCH:
            zeilen.append(einzug + rest)
            break
        schnitt = rest.rfind(" ", 0, _UMBRUCH)
        schnitt = schnitt if schnitt > 0 else _UMBRUCH
        zeilen.append(einzug + rest[:schnitt])
        rest = rest[schnitt:].lstrip()
    return zeilen


def vorschau(command: str, root: Path | None = None) -> str | None:
    """Lesbarer Vorher/Nachher-Block für einen Tracker-Schreibbefehl.

    Liefert None, sobald irgendetwas nicht eindeutig ist – ein unbekannter Befehl, eine
    unparsbare Kommandozeile, eine fehlende Datei, eine unbekannte ID. Der Aufrufer ist ein
    Permission-Hook: Eine fehlende Vorschau ist harmlos, eine falsche wäre es nicht.
    """
    try:
        teile = shlex.split(command)
    except ValueError:
        return None

    script = unterbefehl = None
    for i, wort in enumerate(teile):
        name = wort.rsplit("/", 1)[-1]
        if name in _TRACKER:
            script = name
            unterbefehl = teile[i + 1] if i + 1 < len(teile) else None
            teile = teile[i + 2:]
            break
    if script is None or unterbefehl not in _SCHREIBT:
        return None

    datei, id_muster, feld_muster = _TRACKER[script]
    eintrag, felder = _argumente(teile)
    if not felder and unterbefehl != "remove":
        return None

    kopf = f"{FETT}{script} {unterbefehl}{AUS} → {datei}"
    zeilen = []

    if unterbefehl in ("set", "remove"):
        if eintrag is None:
            return None
        try:
            text = (Path(root) if root else Path(".")).joinpath(datei).read_text(encoding="utf-8")
        except OSError:
            return None
        block = _block(text, eintrag, id_muster)
        if block is None:
            return None
        kopf = f"{FETT}{script} {unterbefehl} {eintrag}{AUS} → {datei}"

    if unterbefehl == "remove":
        # Der ganze Eintrag, nicht nur geänderte Felder: `remove` ist irreversibel, und die
        # Datei behält keine archivierte Kopie. Was hier ungelesen durchgewinkt wird, ist weg.
        kopf = (f"{FETT}{ROT}{script} remove {eintrag}{AUS} → {datei}\n"
                f"{ROT}Der folgende Eintrag wird ERSATZLOS gelöscht:{AUS}")
        # Die Trennlinie am Blockende gehört zum Dokument, nicht zum Eintrag – sie würde
        # sonst so aussehen, als werde auch sie gelöscht.
        rumpf = re.sub(r"\n\s*---\s*$", "", block.strip())
        for zeile in rumpf.splitlines():
            zeilen += ([f"{ROT}  -{AUS}"] if not zeile.strip()
                       else [f"{ROT}{z}{AUS}" for z in _umbrechen(zeile, "  - ")])
    elif unterbefehl == "set":
        for feld, neu in felder:
            alt = _alter_wert(block, feld, feld_muster)
            zeilen.append(f"{FETT}{feld}{AUS}")
            if alt is not None:
                zeilen += [f"{ROT}{z}{AUS}" for z in _umbrechen(alt, "  - ")]
            zeilen += [f"{GRUEN}{z}{AUS}" for z in _umbrechen(neu, "  + ")]
            zeilen.append("")
    else:
        if eintrag:
            kopf = f"{FETT}{script} add{AUS} → {datei}  (Bezug: {eintrag})"
        for feld, wert in felder:
            zeilen.append(f"{FETT}{feld}{AUS}")
            zeilen += _umbrechen(wert, "    ")
            zeilen.append("")

    if _METAZEICHEN.search(command):
        zeilen.append(f"{ROT}⚠ Shell-Metazeichen im Befehl (` oder $(…)): Die Shell wertet sie "
                      f"aus, bevor das Script sie sieht – der geschriebene Text kann von dieser "
                      f"Vorschau abweichen.{AUS}")

    return kopf + "\n\n" + "\n".join(zeilen).rstrip()
