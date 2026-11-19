"""Tests für check-ordinale.py – der PreToolUse-Check um ordinale.py herum.

Getrennt von test_ordinale.py: Dort steht die Mustererkennung, hier der Hook-Vertrag
(welche Datei wird geprüft, wann wird geblockt, fail-open). Mengenangaben meldet seit S133
`checks/mengenangaben.py` als Warnung – Tests dazu in test_mengenangaben_check.py.
"""
from importlib import import_module

import pytest

check_ordinale = import_module("prozesscode.hooks.check-ordinale")


def _edit(pfad, alt, neu):
    return {"tool_name": "Edit", "tool_input": {
        "file_path": str(pfad), "old_string": alt, "new_string": neu}}


@pytest.fixture
def md(tmp_path, monkeypatch):
    """Eine Markdown-Datei im simulierten Repo-Root."""
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    datei = tmp_path / "docs" / "guide.md"
    datei.parent.mkdir(parents=True)
    return datei


@pytest.mark.aufrufpfad("check-ordinale")
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


# --- Mengenangaben blocken nicht ----------------------------------------------

def test_mengenangabe_blockt_nicht(md):
    """Die Klasse ist Warnung (checks/mengenangaben.py), kein Block."""
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    grund = check_ordinale.check(_edit(md, "Text.", "Text.\n\nWarte auf alle vier Agenten."))
    assert grund is None


# --- Form der Meldung ------------------------------------------------------------
def test_meldung_zitiert_gekuerzt_und_hoechstens_zehn_funde(md):
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    lang = "## 1. " + "x" * 200
    neu = "Text.\n\n" + "\n\n".join([lang] + [f"## {n}. Teil" for n in range(2, 13)])
    zeilen = check_ordinale.check(_edit(md, "Text.", neu)).split("\n")
    funde = [z for z in zeilen if z.startswith("  - ")]
    assert zeilen[0] + "\n" == check_ordinale._KOPF
    assert len(funde) == check_ordinale._MAX_HITS
    assert funde[0].endswith(f"`{lang[:check_ordinale._MAX_ZEICHEN]}…`")


def test_in_einer_langen_zeile_zitiert_die_meldung_die_fundstelle_statt_des_anfangs(md):
    # // Given eine lange Zeile, wie sie die Tracker-Werkzeuge schreiben (ein Feld = eine Zeile),
    #    mit dem Verstoß weit hinter der Kürzungsgrenze
    md.write_text("# Guide\n\nText.\n", encoding="utf-8")
    vorspann = "- Beobachtung: " + "Eine lange Beschreibung ohne jede Nummer. " * 6
    zeile = vorspann + "Siehe [Schritt 5](#KPR-drain) dort."  # ordinal-ok – Testeingabe
    # // When die Zeile hinzukommt
    grund = check_ordinale.check(_edit(md, "Text.", "Text.\n\n" + zeile))
    # // Then zitiert die Meldung den Satz mit dem Verstoß, als Ausschnitt gekennzeichnet
    [fund] = [z for z in grund.split("\n") if z.startswith("  - ")]
    assert "[Schritt 5](#KPR-drain)" in fund  # ordinal-ok – Testeingabe
    assert "`…Siehe" in fund


# --- Ausschnitt: was genau zitiert wird ------------------------------------------
_VERSTOSS = "Siehe [Schritt 5](#KPR-drain) dort"  # ordinal-ok – Testeingabe
_VORSPANN = "Eine lange Beschreibung ohne jede Nummer. " * 3
_M = check_ordinale._MAX_ZEICHEN


def _zitat(datei, zeile):
    """Der zitierte Ausschnitt aus der Meldung für eine hinzukommende Zeile."""
    datei.write_text("Text.\n", encoding="utf-8")
    grund = check_ordinale.check(_edit(datei, "Text.", "Text.\n\n" + zeile))
    [fund] = [z for z in grund.split("\n") if z.startswith("  - ")]
    return fund.split("`", 1)[1].rsplit("`", 1)[0]


def _satz_der_laenge(n):
    """Ein Satz mit dem Verstoß, genau n Zeichen lang."""
    return _VERSTOSS + "y" * (n - len(_VERSTOSS) - 1) + "."


@pytest.mark.parametrize("zeile, erwartet", [
    pytest.param("Vorweg. " + _satz_der_laenge(_M - 8), "Vorweg. " + _satz_der_laenge(_M - 8),
                 id="genau an der Grenze: ganz, ohne Kürzungszeichen"),
    pytest.param(_VERSTOSS + ". " + _VORSPANN.strip(), _VERSTOSS + ".…",
                 id="Verstoß vorn: nur hinten gekürzt"),
    pytest.param(_VORSPANN + _satz_der_laenge(_M), "…" + _satz_der_laenge(_M),
                 id="Verstoß am Ende, Satz genau an der Grenze: nur vorn gekürzt"),
    pytest.param(_VORSPANN + _satz_der_laenge(_M + 20), "…" + _satz_der_laenge(_M + 20)[:_M] + "…",
                 id="Satz selbst zu lang: beidseitig gekürzt"),
    pytest.param(_VORSPANN + "Gilt für die Schritte (3–5) dort.", "…Gilt für die Schritte (3–5) dort.",
                 id="Markdown-Muster: der Satz wird mit derselben Dateiart geprüft"),
])
def test_ausschnitt_kennzeichnet_genau_die_gekuerzten_seiten(md, zeile, erwartet):
    assert _zitat(md, zeile) == erwartet


def test_ausschnitt_im_code_prueft_den_satz_als_code(tmp_path, monkeypatch):
    """Im Code zählt der Klartext-Verweis, den es in Markdown nicht gibt – der Satz muss mit
    derselben Dateiart geprüft werden wie die Zeile, sonst fiele er auf den Zeilenanfang zurück."""
    monkeypatch.setattr(check_ordinale.anchors, "REPO_ROOT", tmp_path)
    satz = "Siehe docs/x.md#KPR-drain Schritt 5 dort."  # ordinal-ok – Testeingabe
    zeile = "# " + _VORSPANN + satz
    assert _zitat(tmp_path / "skript.py", zeile) == "…" + satz
