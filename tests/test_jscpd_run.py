"""Tests für jscpd-run.py – Duplikate sind eine Messung, kein Gate.

Die Politik steht in `coding-guideline-python.md`, „Duplikate: gemessen, nicht als Gate":
Der Bestand an nicht extrahierbaren Klonen (Docstring-Schluss + Import-Bootstrap in der
Hook-Familie) darf nicht dauerhaft rot melden – ein Werkzeug, das immer ✗ sagt, wird ignoriert
und meldet dann auch echte Funde wirkungslos. Der Wrapper vergleicht deshalb gegen eine
Baseline und schlägt nur bei **Zuwachs** an.

Die vierte Zusage ist die gegen Klasse STUMM: Erkennt der Parser weniger Klone, als jscpd
selbst meldet, meldet der Wrapper das als Fehler – sonst wäre eine Formatänderung von
„keine neuen Duplikate" nicht zu unterscheiden.
"""
from importlib import import_module

import pytest

jscpd = import_module("prozesscode.jscpd-run")


_A = "prozesscode/hooks/check-adr-capture.py"
_B = "prozesscode/hooks/check-obs-capture.py"
_C = "prozesscode/dotnet-stryker.py"
_D = "prozesscode/stryker-frontend.py"
_NEU_1 = "prozesscode/doc.py"
_NEU_2 = "prozesscode/anchors.py"

# Ein Eintrag deckt genau einen Klon: Der Wert ist der Grund, warum er stehen bleiben darf.
_TEST_BASELINE = {(_A, _B): "Import-Bootstrap", (_C, _D): "Kommentarblock"}


def _klon(datei_a: str, datei_b: str) -> str:
    """Ein Klon-Block im Konsolenformat von jscpd 5.4 mit `"absolute": true` – die ANSI-Sequenzen
    stehen im echten Lauf nur um die erste Fundstelle."""
    return (
        "\x1b[1mClone found (python)\x1b[22m\n"
        f" - \x1b[1m\x1b[32m{jscpd.REPO_ROOT}/{datei_a}\x1b[39m\x1b[22m [33:77 - 44:48] (12 lines, 80 tokens)\n"
        f"   {jscpd.REPO_ROOT}/{datei_b} [24:97 - 35:48]\n"
    )


def _ausgabe(*klone: str, gemeldet: int | None = None) -> str:
    anzahl = len(klone) if gemeldet is None else gemeldet
    return (
        "> mahl-client@0.0.0 lint:duplicates\n"
        "> jscpd --config ../jscpd.config.json\n\n"
        + "".join(klone)
        + f"\x1b[90mFound {anzahl} clones.\x1b[39m\n"
    )


def _lauf(monkeypatch, ausgabe: str, exit_code: int = 0):
    monkeypatch.setattr(jscpd, "BEKANNTE_KLONE", _TEST_BASELINE)
    monkeypatch.setattr(jscpd, "run_npm", lambda *_a, **_k: (ausgabe, exit_code))


@pytest.mark.aufrufpfad("jscpd-run")
def test_bekannter_bestand_meldet_gruen(monkeypatch, capsys):
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B), _klon(_C, _D)))
    assert jscpd.main([]) == 0
    assert "✓" in capsys.readouterr().out


def test_ein_neues_dateipaar_schlaegt_an(monkeypatch, capsys):
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B), _klon(_NEU_1, _NEU_2)))
    assert jscpd.main([]) == 1
    ausgabe = capsys.readouterr().out
    assert "✗" in ausgabe
    assert "doc.py" in ausgabe and "anchors.py" in ausgabe


def test_bekanntes_dateipaar_meldet_nur_den_zuwachs(monkeypatch, capsys):
    """Ein zweiter Klon zwischen denselben zwei Dateien ist neu – das Paar allein trüge
    ihn sonst mit durch."""
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B), _klon(_A, _B), _klon(_C, _D)))
    assert jscpd.main([]) == 1
    assert "check-adr-capture.py" in capsys.readouterr().out


def test_die_reihenfolge_im_paar_spielt_keine_rolle(monkeypatch):
    """jscpd nennt mal die eine, mal die andere Datei zuerst – das ist derselbe Klon."""
    _lauf(monkeypatch, _ausgabe(_klon(_B, _A), _klon(_D, _C)))
    assert jscpd.main([]) == 0


def test_entfallener_klon_bleibt_gruen_nennt_aber_die_baseline(monkeypatch, capsys):
    """Weniger Duplikate sind ein Erfolg, kein Fehler – aber die Baseline verliert sonst
    still ihren Bezug zum Bestand."""
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B)))
    assert jscpd.main([]) == 0
    ausgabe = capsys.readouterr().out
    assert "✓" in ausgabe
    assert "Baseline" in ausgabe


def test_ein_mehrfach_eintrag_meldet_auch_die_unterzahl(monkeypatch, capsys):
    """Erwartet der Bestand zwei Funde in einem Paar und kommt nur einer, ist die Erwartung
    zu hoch. Ohne Meldung bliebe sie stehen und deckte künftig einen echten neuen Klon –
    das vollständige Fehlen des Paares allein zu prüfen, reicht dafür nicht."""
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B), _klon(_C, _D)))
    monkeypatch.setattr(jscpd, "_MEHRFACH", {(_C, _D): 2})
    assert jscpd.main([]) == 0
    ausgabe = capsys.readouterr().out
    assert "✓" in ausgabe
    assert "Baseline" in ausgabe
    assert "stryker-frontend.py" in ausgabe


def test_nicht_erkannte_klone_melden_den_parser(monkeypatch, capsys):
    """Klasse STUMM: Ändert jscpd sein Ausgabeformat, findet der Parser nichts mehr – und
    „nichts gefunden" sähe wie „keine neuen Duplikate" aus."""
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B), gemeldet=7))
    assert jscpd.main([]) == 1
    ausgabe = capsys.readouterr().out
    assert "✗" in ausgabe
    assert "jscpd-run.py" in ausgabe


def test_echte_ausgabe_von_jscpd_5_4_wird_der_baseline_zugeordnet(monkeypatch, capsys):
    """Gespeicherte Ausgabe des echten Laufs (jscpd 5.4.1, 2026-10), nur der Repo-Pfad ist
    eingesetzt. Eine handgeschriebene Fixture prüft nur den eigenen Parser – ändert jscpd sein
    Ausgabeformat, fällt das erst gegen die echte Ausgabe auf."""
    wurzel = jscpd.REPO_ROOT
    echt = (
        "\n> mahl-client@0.0.0 lint:duplicates\n> jscpd --config ../jscpd.config.json\n\n"
        "Using config from ../jscpd.config.json\n"
        "\x1b[1mClone found (python)\x1b[22m\n"
        f" - \x1b[1m\x1b[32m{wurzel}/prozesscode/dotnet-stryker.py\x1b[39m\x1b[22m"
        " [85:65 - 93:67] (9 lines, 72 tokens)\n"
        f"   {wurzel}/prozesscode/stryker-frontend.py [85:66 - 93:67]\n"
        "\x1b[90m│\x1b[39m python     \x1b[90m│\x1b[39m 168            \x1b[90m│\x1b[39m 33050"
        "       \x1b[90m│\x1b[39m 204843       \x1b[90m│\x1b[39m 1            \x1b[90m│\x1b[39m\n"
        "\x1b[90mFound 1 clones.\x1b[39m\n"
        "\x1b[90mtime: 56.045ms\x1b[39m\n"
    )
    monkeypatch.setattr(jscpd, "run_npm", lambda *_a, **_k: (echt, 0))
    assert jscpd.main([]) == 0
    assert "✓" in capsys.readouterr().out


def test_fundstelle_ohne_absoluten_pfad_meldet_die_konfiguration(monkeypatch, capsys):
    """Fehlt `"absolute": true`, nennt jscpd 5.4 nur den Dateinamen. Der passt auf keinen
    Baseline-Eintrag und erschiene sonst als „neues Duplikat" – eine falsche Spur."""
    ohne_pfad = (
        "\x1b[1mClone found (python)\x1b[22m\n"
        " - \x1b[1m\x1b[32mdotnet-stryker.py\x1b[39m\x1b[22m [85:65 - 93:67] (9 lines, 72 tokens)\n"
        "   stryker-frontend.py [85:66 - 93:67]\n"
    )
    _lauf(monkeypatch, _ausgabe(ohne_pfad))
    assert jscpd.main([]) == 1
    ausgabe = capsys.readouterr().out
    assert "absolute" in ausgabe
    assert "jscpd.config.json" in ausgabe


def test_zusaetzliche_fundstelle_je_klon_meldet_den_parser(monkeypatch, capsys):
    """Gezählt werden Fundstellen, nicht Paare: Nennte ein geändertes Format drei Dateien je
    Klon, käme die Paarzahl zufällig hin und der Fehlgriff bliebe stumm."""
    dritte = f"   {jscpd.REPO_ROOT}/{_NEU_1} [10:1 - 21:9]\n"
    _lauf(monkeypatch, _ausgabe(_klon(_A, _B) + dritte, _klon(_C, _D)))
    assert jscpd.main([]) == 1
    assert "jscpd-run.py" in capsys.readouterr().out


def test_abgebrochener_lauf_gibt_die_rohausgabe(monkeypatch, capsys):
    """Ohne „Found N clones." hat jscpd nicht zu Ende gearbeitet: Dann trägt nur das Original."""
    _lauf(monkeypatch, "npm error code ENOENT\nnpm error syscall spawn jscpd\n", exit_code=1)
    assert jscpd.main([]) != 0
    assert "ENOENT" in capsys.readouterr().out


def test_die_baseline_begruendet_jeden_eintrag():
    """Eine Baseline ohne Begründung wird zur Müllhalde: Jedes Paar braucht den Grund,
    warum es stehen bleiben darf."""
    for paar, grund in jscpd.BEKANNTE_KLONE.items():
        assert grund.strip(), f"{paar} steht ohne Begründung in der Baseline"
