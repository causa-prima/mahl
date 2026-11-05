"""Die gemeinsame Ausgabe-Politik der Wrapper: Verdikt im Normalfall, Rohausgabe mit --verbose.

Das Verdikt ist die Aussage des Wrappers – auch ein ✗ der Sperrklinke oder ein Abbruch. Fehlt es
bei `--verbose`, sieht der Aufrufer den rohen Lauf und hält ihn leicht für bestanden.
"""
from prozesscode._wrapper_output import VERBOSE_HINT, emit, error_lines, strip_noise


def test_ohne_verbose_details_vor_dem_verdikt(capsys):
    emit(verbose=False, output="roh", verdict="✗ 2 Test(s) rot", details=["a", "b"])
    assert capsys.readouterr().out == f"a\nb\n\n✗ 2 Test(s) rot\n{VERBOSE_HINT}\n"


def test_ohne_details_nur_das_verdikt(capsys):
    emit(verbose=False, output="roh", verdict="✓ grün")
    assert capsys.readouterr().out == f"✓ grün\n{VERBOSE_HINT}\n"


def test_verbose_zeigt_rohausgabe_und_am_ende_das_verdikt(capsys):
    emit(verbose=True, output="roh 1\nroh 2\n\n", verdict="✗ Sperrklinke gerissen",
         details=["gekürzt"])
    assert capsys.readouterr().out == "roh 1\nroh 2\n✗ Sperrklinke gerissen\n"


def test_strip_noise_entfernt_npm_zeilen_und_leere_raender():
    roh = "\n> mahl-client@0.0.0 test\nnpm warn x\nInhalt\n> vitest run\n\n"
    assert strip_noise(roh) == ["Inhalt"]


def test_error_lines_waehlt_fehlerzeilen_und_faellt_sonst_auf_das_ende_zurueck():
    zeilen = [f"zeile {i}" for i in range(40)]
    assert error_lines(zeilen + ["ERROR kaputt"]) == ["ERROR kaputt"]
    assert error_lines(zeilen) == zeilen[-30:]
    assert error_lines(zeilen, verbose=True) == zeilen
