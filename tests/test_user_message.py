"""Tests für user-message.py – die SessionStart-Nachricht an den USER.

Zwei Dinge werden geprüft, beide sonst still:

**Die Form.** Claude Code liest die Hook-Ausgabe nur dann als JSON-Output, wenn sie als JSON
parst, und nur das top-level `systemMessage` erreicht den User. Der erste Messversuch (S131)
hatte das Feld in `hookSpecificOutput` verschachtelt – der Hook lief fehlerfrei, und die
Nachricht kam nirgends an.

**Der Inhalt.** Fällt eine fällige Frage aus der Nachricht, merkt es niemand: Der Session-Start
läuft grün weiter, und dass etwas fehlt, sieht man nur, wenn man es ohnehin schon weiß.
"""
import json
from importlib import import_module

modul = import_module("prozesscode.user-message")


def _frage(oq_id="OQ-S094-2", titel="Mobile-Ansicht: welche Szenarien, ab wann?"):
    return {"id": oq_id, "title": titel, "frage": "Ab wann?", "gruende": ["Phase:MVP erreicht"]}


# --- Form ---------------------------------------------------------------------
def test_output_is_valid_json():
    assert json.loads(modul.ausgabe("hallo"))


def test_system_message_is_top_level():
    # Der Fehler des ersten Messversuchs: in hookSpecificOutput verschachtelt, wo das Feld
    # nicht gelesen wird. Empirisch bestätigt – top-level erreicht den User, verschachtelt nicht.
    daten = json.loads(modul.ausgabe("hallo"))
    assert daten["systemMessage"] == "hallo"
    assert "hookSpecificOutput" not in daten


def test_no_additional_context_field():
    # additionalContext erreicht nur den Agenten – wäre es gesetzt, sähe eine ankommende
    # Nachricht grün aus, obwohl der User-Kanal gar nicht geprüft wurde.
    assert "additionalContext" not in json.loads(modul.ausgabe("x"))


# --- Inhalt -------------------------------------------------------------------
def test_nothing_due_yields_no_message():
    # Kein Rauschen bei jedem Session-Start – die Zeile soll etwas bedeuten, wenn sie erscheint.
    assert modul.nachricht([]) is None


def test_message_names_id_and_title():
    text = modul.nachricht([_frage()])
    assert "OQ-S094-2" in text and "Mobile-Ansicht" in text


def test_message_counts_the_questions():
    text = modul.nachricht([_frage("OQ-A", "Erste"), _frage("OQ-B", "Zweite")])
    assert "2" in text.splitlines()[0]


def test_message_names_the_way_out():
    # Der Zweck ist die Quittung: Der User muss nachfassen können, wenn der Agent schweigt.
    assert "session-agenda --only open-questions" in modul.nachricht([_frage()])


def test_message_does_not_carry_the_full_body():
    # Der Eintragskörper trägt Herleitung und verworfene Varianten – im Terminal nur Ballast.
    frage = {**_frage(), "body": "SEHR LANGE HERLEITUNG"}
    assert "SEHR LANGE HERLEITUNG" not in modul.nachricht([frage])


# --- Zusammenspiel -------------------------------------------------------------
def test_main_prints_nothing_when_nothing_is_due(monkeypatch, capsys):
    monkeypatch.setattr(modul, "faellige_fragen", lambda: [])
    assert modul.main() == 0
    assert capsys.readouterr().out == ""


def test_main_prints_json_when_something_is_due(monkeypatch, capsys):
    monkeypatch.setattr(modul, "faellige_fragen", lambda: [_frage()])
    assert modul.main() == 0
    assert "OQ-S094-2" in json.loads(capsys.readouterr().out)["systemMessage"]
