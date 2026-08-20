"""Datei-Zustand vor und nach einem Edit/Write – gemeinsam für die capture-Hooks.

Ein PreToolUse-Hook läuft, bevor die Änderung geschrieben wird; um sie zu prüfen, muss
er nachbilden, was das Edit-Tool gleich tun wird. Diese Nachbildung lag fünfmal
identisch vor. Gefährlich daran war nicht der Umfang, sondern die Ausfallart: Wird eine
Kopie bei einer Semantik-Änderung des Edit-Tools nicht nachgezogen, prüft der Hook
lautlos einen Dateiinhalt, den es nie geben wird, und winkt durch.

NICHT hier: die Variante aus check-ref-direction.py und check-e2e-scenario-ref.py –
sie nimmt (tool, file_path, tool_input). Zusammenlegen hieße eine Signatur umbauen.
"""
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
