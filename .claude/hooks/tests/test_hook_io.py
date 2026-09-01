"""Tests für _hook_io.py – Datei-Zustand vor/nach einem Edit/Write.

`edit_zustand` fasst zusammen, was in S128 neunmal identisch am Anfang jedes blockierenden
Hooks stand: Tool prüfen, `file_path` ziehen, Zuständigkeit prüfen, `pre`/`post` bilden
(jscpd: 7 der 12 Python-Clones). Die Gefahr der Kopien war nie ihr Umfang, sondern ihre
Ausfallart – wird eine bei einer Semantik-Änderung des Edit-Tools nicht nachgezogen, prüft
der Hook lautlos einen Inhalt, den es nie geben wird, und winkt durch. Genau die Begründung,
mit der `compute_post_content` selbst schon zusammengeführt wurde.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import _hook_io


def _write(pfad, tool_input=None, **rest):
    return {"tool_name": "Write",
            "tool_input": {"file_path": str(pfad), "content": "neu\n", **(tool_input or {})},
            **rest}


# --- Vor-/Nachzustand einzeln (bis S128 in test_obs_capture.py, dort am falschen Ort) ------
def test_vorzustand_ist_die_datei_auf_der_platte(tmp_path):
    ziel = tmp_path / "da.md"
    ziel.write_text("Inhalt\n", encoding="utf-8")
    assert _hook_io.read_file_text(str(ziel)) == "Inhalt\n"


def test_vorzustand_einer_fehlenden_datei_ist_leer(tmp_path):
    """Ein Write, der die Datei neu anlegt, hat keinen Vorzustand – "" statt Fehler."""
    assert _hook_io.read_file_text(str(tmp_path / "gibtsnicht.md")) == ""


def test_write_nachzustand_ist_der_neue_inhalt():
    assert _hook_io.compute_post_content("Write", {"content": "neu"}, "alt") == "neu"


def test_edit_nachzustand_wendet_die_ersetzung_an():
    inp = {"old_string": "offen", "new_string": "erledigt"}
    assert _hook_io.compute_post_content("Edit", inp, "Status: offen\n") == "Status: erledigt\n"


def test_edit_mit_unauffindbarem_old_string_laesst_den_inhalt_stehen():
    """Der echte Edit schlüge ohnehin fehl – der Hook darf daraus keinen Phantominhalt bauen."""
    inp = {"old_string": "kommt so nicht vor", "new_string": "egal"}
    assert _hook_io.compute_post_content("Edit", inp, "Status: offen\n") == "Status: offen\n"


def test_replace_all_ersetzt_jedes_vorkommen():
    inp = {"old_string": "x", "new_string": "y", "replace_all": True}
    assert _hook_io.compute_post_content("Edit", inp, "x-x-x") == "y-y-y"


def test_ohne_replace_all_nur_das_erste_vorkommen():
    inp = {"old_string": "x", "new_string": "y"}
    assert _hook_io.compute_post_content("Edit", inp, "x-x-x") == "y-x-x"


# --- Einstieg ----------------------------------------------------------------
def test_write_liefert_pfad_leeren_vorzustand_und_inhalt(tmp_path):
    ziel = tmp_path / "neu.md"
    zustand = _hook_io.edit_zustand(_write(ziel))
    assert zustand == (str(ziel), "", "neu\n")


def test_edit_liefert_vor_und_nachzustand(tmp_path):
    ziel = tmp_path / "da.md"
    ziel.write_text("alt\n", encoding="utf-8")
    data = {"tool_name": "Edit",
            "tool_input": {"file_path": str(ziel), "old_string": "alt", "new_string": "neu"}}
    assert _hook_io.edit_zustand(data) == (str(ziel), "alt\n", "neu\n")


def test_fremdes_werkzeug_geht_den_hook_nichts_an(tmp_path):
    data = {"tool_name": "Read", "tool_input": {"file_path": str(tmp_path / "x.md")}}
    assert _hook_io.edit_zustand(data) is None


def test_ohne_dateipfad_kein_zustand():
    assert _hook_io.edit_zustand({"tool_name": "Write", "tool_input": {}}) is None


def test_leerer_input_kippt_nicht():
    """Ein Hook darf an unerwartetem Input nicht sterben – er blockiert sonst jeden Edit."""
    assert _hook_io.edit_zustand({}) is None


def test_das_praedikat_entscheidet_ueber_die_zustaendigkeit(tmp_path):
    ziel = tmp_path / "egal.md"
    assert _hook_io.edit_zustand(_write(ziel), betrifft=lambda p: False) is None
    assert _hook_io.edit_zustand(_write(ziel), betrifft=lambda p: True) is not None


def test_ohne_praedikat_ist_jede_datei_zustaendig(tmp_path):
    """Vier der neun Hooks prüfen die Zuständigkeit erst später am Inhalt."""
    assert _hook_io.edit_zustand(_write(tmp_path / "beliebig.txt")) is not None


def test_ein_nicht_simulierbarer_post_zustand_liefert_none(tmp_path):
    """`compute_post_content` gibt bei unbekanntem Tool None – das muss durchschlagen,
    sonst prüfte der Hook einen Inhalt, den es nicht gibt."""
    data = {"tool_name": "NotebookEdit", "tool_input": {"file_path": str(tmp_path / "x.md")}}
    assert _hook_io.edit_zustand(data) is None
