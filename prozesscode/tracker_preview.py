#!/usr/bin/env python3
"""Lesbare Vorschau eines Tracker-Schreibbefehls – für den Freigabedialog.

Warum (OBS-S116-1): Seit S114 entstehen Einträge über `obs.py`/`lessons.py` statt über
`Edit`. Das spart den erzwungenen Vor-Edit-Read der ganzen Datei (CM-S114-2), kostet aber
die Prüfbarkeit: Ein `Edit` zeigt im Freigabedialog einen Diff, ein Script-Aufruf nur eine
lange Kommandozeile. Bei `set` ist zusätzlich der Ausgangszustand unsichtbar – aus dem
Aufruf allein ist nicht ablesbar, was ersetzt wird.

`vorschau()` schließt die Lücke: Sie erzeugt aus der Kommandozeile plus dem aktuellen
Dateiinhalt einen Vorher/Nachher-Block, den `check-bash-permission.py` als
`permissionDecisionReason` mitgibt.

**Was der Kanal trägt** – zweimal am echten Dialog gemessen, S124 und S129, mit identischem
Aufbau (temporäre `ask`-Antwort an einem read-only-Befehl, Bild vom User):

    Zeilenumbrüche, Einrückung, Leerzeilen   ✓      Markdown (fett, Code, Liste, Tabelle)  ✗
    Unicode-Rahmen, Emoji, Umlaute           ✓      ANSI (fett, Farbe, Unterstreichung)    ✗ (S129)
    Diff-Marker am Zeilenanfang              ✓      Kürzung langer Zeilen                  keine

**ANSI trug S124 noch und trägt seit S129 nicht mehr.** Terminal-Escapes erscheinen jetzt als
Bytes: `\x1b[1mTitel` wird zu „�[1mTitel". Im Changelog von Claude Code steht dazu nichts;
die Änderung ist undokumentiert und kann sich erneut drehen. Deshalb wird die Auszeichnung
hier **nicht** an ANSI gehängt, sondern an das, was in beiden Messungen trug: `▸` vor dem
Feldnamen, die Wörter `bisher`/`neu` an den Diff-Zeilen (ein `-` allein liest sich einfarbig
wie ein Aufzählungszeichen), `⚠` an Warnungen. `tests/test_tracker_preview.py` hält
fest, dass kein Escape mehr in den Text gerät.

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

# Markiert einen Feldnamen. Ersetzt den früheren Fettdruck, den der Dialog seit S129
# nicht mehr rendert; Unicode trägt er dagegen nachweislich.
_FELD = "▸ "

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
    "--aufschubgrund": "Aufschubgrund",
    "--done": "Done-Kriterium (AGENT_MEMORY)",
}

# Werkzeug → (Datei, Muster der Eintrags-Kopfzeile, Muster einer Feldzeile).
# Das Feldmuster ist je Tracker verschieden (`- Feld:` gegen `**Feld:**`) – die Vereinheitlichung
# wäre eine Migration der Bestandsdateien und steht hier bewusst nicht an.
_TRACKER = {
    "obs": ("docs/kaizen/observations.md", r"^## (OBS-S\d+-\d+)", r"^- {feld}:\s*(.*)$"),
    "lessons": ("docs/kaizen/lessons_learned.md", r"\*\*\[.*?\] (LL-S\d+-\d+)",
                r"^\s*- {feld}:\s*(.*)$"),
    "oq": ("docs/open-questions.md", r"^## (OQ-S\d+-\d+)", r"^\*\*{feld}:\*\*\s*(.*)$"),
    "td": ("docs/tech-debt.md", r"^## (TD-S\d+-\d+)", r"^\*\*{feld}:\*\*\s*(.*)$"),
}

_SCHREIBT = ("add", "set", "remove")
_UMBRUCH = 96


def _werkzeugname(wort: str) -> str:
    """Der Werkzeugname aus jeder Aufrufform: `prozesscode.oq`, `prozesscode/oq.py`, `oq.py`.

    Der Pfadaufruf scheitert heute an den paketinternen Importen; er bleibt trotzdem erkannt,
    damit die Vorschau nicht ausfällt, falls er je wieder möglich wird. Eine fehlende Vorschau
    beim Freigabe-Prompt hieße: Der User bestätigt eine Dateiänderung, die er nicht sieht.
    """
    return wort.rsplit("/", 1)[-1].removesuffix(".py").rsplit(".", 1)[-1]


def _argumente(teile: list[str]) -> tuple[str | None, list[tuple[str, str]]]:
    """(Eintrags-ID, [(Feldname, Wert)]) aus den Argumenten nach dem Unterbefehl."""
    eintrag, felder = None, []
    i = 0
    while i < len(teile):
        wort = teile[i]
        if wort.startswith("--"):
            # Ein hier nicht eingetragenes Argument erscheint unter seinem Rohnamen, statt still
            # aus dem Freigabedialog zu fallen – sonst sieht der User ein neues Feld nie (S133).
            feld = _ARGUMENT_ZU_FELD.get(wort, wort)
            wert = teile[i + 1] if i + 1 < len(teile) else ""
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
        return [einzug + "(leer)"]
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

    werkzeug = unterbefehl = None
    for i, wort in enumerate(teile):
        name = _werkzeugname(wort)
        if name in _TRACKER:
            werkzeug = name
            unterbefehl = teile[i + 1] if i + 1 < len(teile) else None
            teile = teile[i + 2:]
            break
    if werkzeug is None or unterbefehl not in _SCHREIBT:
        return None

    datei, id_muster, feld_muster = _TRACKER[werkzeug]
    eintrag, felder = _argumente(teile)
    if not felder and unterbefehl != "remove":
        return None

    kopf = f"{werkzeug} {unterbefehl} → {datei}"
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
        kopf = f"{werkzeug} {unterbefehl} {eintrag} → {datei}"

    if unterbefehl == "remove":
        # Der ganze Eintrag, nicht nur geänderte Felder: `remove` ist irreversibel, und die
        # Datei behält keine archivierte Kopie. Was hier ungelesen durchgewinkt wird, ist weg.
        kopf = (f"{werkzeug} remove {eintrag} → {datei}\n"
                "⚠ Der folgende Eintrag wird ERSATZLOS gelöscht:")
        # Die Trennlinie am Blockende gehört zum Dokument, nicht zum Eintrag – sie würde
        # sonst so aussehen, als werde auch sie gelöscht.
        rumpf = re.sub(r"\n\s*---\s*$", "", block.strip())
        for zeile in rumpf.splitlines():
            zeilen += (["  -"] if not zeile.strip()
                       else _umbrechen(zeile, "  - "))
    elif unterbefehl == "set":
        for feld, neu in felder:
            alt = _alter_wert(block, feld, feld_muster)
            zeilen.append(f"{_FELD}{feld}")
            if alt is not None:
                zeilen += _umbrechen(alt, "  bisher  ")
            zeilen += _umbrechen(neu, "  neu     ")
            zeilen.append("")
    else:
        if eintrag:
            kopf = f"{werkzeug} add → {datei}  (Bezug: {eintrag})"
        for feld, wert in felder:
            zeilen.append(f"{_FELD}{feld}")
            zeilen += _umbrechen(wert, "    ")
            zeilen.append("")

    if _METAZEICHEN.search(command):
        zeilen.append("⚠ Shell-Metazeichen im Befehl (` oder $(…)): Die Shell wertet sie "
                      "aus, bevor das Script sie sieht – der geschriebene Text kann von dieser "
                      "Vorschau abweichen.")

    return kopf + "\n\n" + "\n".join(zeilen).rstrip()
