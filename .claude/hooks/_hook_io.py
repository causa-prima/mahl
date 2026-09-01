"""Datei-Zustand vor und nach einem Edit/Write – gemeinsam für die capture-Hooks.

Ein PreToolUse-Hook läuft, bevor die Änderung geschrieben wird; um sie zu prüfen, muss
er nachbilden, was das Edit-Tool gleich tun wird. Diese Nachbildung lag fünfmal
identisch vor. Gefährlich daran war nicht der Umfang, sondern die Ausfallart: Wird eine
Kopie bei einer Semantik-Änderung des Edit-Tools nicht nachgezogen, prüft der Hook
lautlos einen Dateiinhalt, den es nie geben wird, und winkt durch.

Seit S128 liegt hier auch der EINSTIEG (`edit_zustand`): Die vier Zeilen davor – Tool prüfen,
`file_path` ziehen, Zuständigkeit prüfen – standen neunmal identisch da und machten sieben der
zwölf Python-Clones aus, die jscpd meldete. Es ist dieselbe Ausfallart wie oben, eine Stufe
früher: Ändert sich der Dispatcher-Vertrag, muss man neun Stellen finden, und die vergessene
prüft dann lautlos das Falsche.
"""
from collections.abc import Callable
from pathlib import Path


def read_file_text(file_path: str) -> str:
    """Aktueller Datei-Inhalt; "" wenn die Datei (noch) nicht existiert.

    Ein Write, der die Datei neu anlegt, hat keinen Vorzustand – "" statt Fehler.
    """
    path = Path(file_path)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def compute_post_content(tool: str, tool_input: dict, pre: str) -> str | None:
    """Simuliert den Datei-Inhalt nach dem Edit/Write; None = kein Inhalt zu prüfen."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if old and old in pre:
            count = -1 if tool_input.get("replace_all") else 1
            return pre.replace(old, new, count)
        return pre  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
    return None


def edit_zustand(data: dict,
                 betrifft: Callable[[str], bool] | None = None) -> tuple[str, str, str] | None:
    """`(file_path, pre, post)` für einen Edit/Write – oder None, wenn nichts zu prüfen ist.

    None in vier Fällen, und der Aufrufer behandelt sie alle gleich: kein Edit/Write, kein
    Dateipfad, `betrifft` verneint die Zuständigkeit, oder der Nachzustand ist nicht
    simulierbar. Ein Hook, der hier None bekommt, gibt None zurück – mehr braucht sein
    Einstieg nicht.

    `betrifft` ist optional, weil vier der neun Hooks ihre Zuständigkeit erst am INHALT
    entscheiden (etwa `check-anchors`, das jede Datei mit Ankern angeht) und nicht am Pfad.
    """
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not file_path:
        return None
    if betrifft is not None and not betrifft(file_path):
        return None

    pre = read_file_text(file_path)
    post = compute_post_content(tool, tool_input, pre)
    if post is None:
        return None
    return file_path, pre, post
