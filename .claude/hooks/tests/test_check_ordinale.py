"""Tests für check-ordinale.py – der PreToolUse-Check um ordinale.py herum.

Getrennt von test_ordinale.py: Dort steht die Mustererkennung, hier der Hook-Vertrag
(welche Datei wird geprüft, wann wird geblockt, was landet im Log, fail-open).
"""
import os
import sys
from importlib import import_module

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
check_ordinale = import_module("check-ordinale")


def _edit(pfad, alt, neu):
    return {"tool_name": "Edit", "tool_input": {
        "file_path": str(pfad), "old_string": alt, "new_string": neu}}


@pytest.fixture
def md(tmp_path, monkeypatch):
    """Eine Markdown-Datei im simulierten Repo-Root."""
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_ordinale, "_LOG", tmp_path / ".claude" / "tmp" / "mengen.log")
    datei = tmp_path / "docs" / "guide.md"
    datei.parent.mkdir(parents=True)
    return datei


def test_neue_nummerierte_ueberschrift_blockt(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    grund = check_ordinale.check(_edit(md, "Text.", "Text.\n\n## 3. Nachtrag"))
    assert grund and "3. Nachtrag" in grund


def test_namensueberschrift_blockt_nicht(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    assert check_ordinale.check(_edit(md, "Text.", "Text.\n\n## Nachtrag")) is None


def test_bestehende_nummer_blockt_nicht(md):
    """Ein Edit an anderer Stelle darf eine Altlast nicht kollateral blockieren."""
    md.write_text("# Guide\n\n## 3. Alt\n\nText.\n", encoding="utf-8")
    assert check_ordinale.check(_edit(md, "Text.", "Anderer Text.")) is None


def test_marker_hebt_auf(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    neu = "Text.\n\n## 3. Nachtrag  <!-- ordinal-ok -->"
    assert check_ordinale.check(_edit(md, "Text.", neu)) is None


def test_history_wird_nicht_geprueft(tmp_path, monkeypatch):
    """docs/history/ hält den Zustand von damals fest – dort ist die Nummer korrekt."""
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    datei = tmp_path / "docs" / "history" / "sessions" / "session_1.md"
    datei.parent.mkdir(parents=True)
    datei.write_text("# S1\n\nText.\n", encoding="utf-8")
    assert check_ordinale.check(_edit(datei, "Text.", "Text.\n\n## 3. Nachtrag")) is None


def test_python_kommentar_blockt_nicht(tmp_path, monkeypatch):
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(check_ordinale, "_LOG", tmp_path / ".claude" / "tmp" / "mengen.log")
    datei = tmp_path / "skript.py"
    datei.write_text("x = 1\n", encoding="utf-8")
    assert check_ordinale.check(_edit(datei, "x = 1", "x = 1\n# 2. Schritt: rechnen")) is None


def test_muster_ausnahme_blockt_den_edit_nicht(tmp_path, monkeypatch):
    """Seit die Werkzeug-Tests mitgeprüft werden (S124, zweistufige Ausnahme), muss der Hook
    dieselbe Ausnahme kennen wie der Bestandsprüfer – sonst blockiert er jeden Edit an einer
    Datei, deren Zweck es ist, die Muster als Eingabe zu führen."""
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    monkeypatch.setitem(check_ordinale.anchors.MUSTER_AUSNAHMEN, "t/test_x.py",
                        frozenset({"ordinal"}))
    (tmp_path / "t").mkdir()
    datei = tmp_path / "t" / "test_x.py"
    datei.write_text("# Tests\n", encoding="utf-8")
    grund = check_ordinale.check(_edit(datei, "# Tests", "# Tests\n# gilt nach §3 der Regel"))
    assert grund is None


def test_anderes_tool_wird_ignoriert(md):
    md.write_text("# Guide\n", encoding="utf-8")
    daten = {"tool_name": "Read", "tool_input": {"file_path": str(md)}}
    assert check_ordinale.check(daten) is None


# --- Mengenangaben: Log statt Block ------------------------------------------

def test_mengenangabe_blockt_nicht_und_landet_im_log(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    grund = check_ordinale.check(_edit(md, "Text.", "Text.\n\nWarte auf alle vier Agenten."))
    assert grund is None
    assert "alle vier Agenten" in check_ordinale._LOG.read_text(encoding="utf-8")


def test_log_haelt_die_fundstelle_fest(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    check_ordinale.check(_edit(md, "Text.", "Text.\n\nDie drei Felder sind Pflicht."))
    zeile = check_ordinale._LOG.read_text(encoding="utf-8")
    assert "docs/guide.md" in zeile


def test_log_zeigt_die_umgebung_des_treffers(md):
    """Doku-Zeilen sind lang: In den ersten drei echten Log-Einträgen lag die Fundstelle
    jenseits der Kappungsgrenze, protokolliert wurde der Zeilenanfang. Damit misst das Log
    nicht, wofür es da ist – die spätere Beurteilung braucht die Umgebung des Treffers."""
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    lang = "Vorspann dazu. " * 20 + "Warte auf alle vier Agenten, dann weiter."
    check_ordinale.check(_edit(md, "Text.", "Text.\n\n" + lang))
    assert "dann weiter" in check_ordinale._LOG.read_text(encoding="utf-8")


def test_ohne_mengenangabe_kein_log(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    check_ordinale.check(_edit(md, "Text.", "Text.\n\nWarte auf alle Agenten."))
    assert not check_ordinale._LOG.exists()


def test_log_fehler_blockt_den_edit_nicht(md, monkeypatch):
    """Fail-open: Ein kaputtes Log darf nie einen Edit verhindern (CM-S116-1-Logik)."""
    monkeypatch.setattr(check_ordinale, "_LOG", md.parent / "nicht" / "existent" / "x.log")
    monkeypatch.setattr(check_ordinale.Path, "mkdir", _wirft)
    grund = check_ordinale.check(_edit(md, "", "Warte auf alle vier Agenten."))
    assert grund is None


def _wirft(*_args, **_kwargs):
    raise OSError("Platte voll")
