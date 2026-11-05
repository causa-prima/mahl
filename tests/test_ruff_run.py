"""Tests für ruff-run.py – Linter über den Prozess-Code unter .claude/**.

Drei Zusagen, die der Wrapper hält:
  1. Im Erfolgsfall nur ein VERDIKT, im Fehlerfall die Fundstellen davor – dieselbe Politik
     wie bei den übrigen Wrappern, damit ein nachgelagertes `| tail` nie nötig wird.
  2. Ein FEHLENDES venv meldet sich mit dem Befehl, der es herstellt. Sonst fiele der Linter
     nach einem frischen Clone mit einem Datei-nicht-gefunden aus, und ein Werkzeug, das
     unverständlich scheitert, wird abgeschaltet statt repariert.
  3. Der Exit-Code trägt das Ergebnis – der Wrapper ist damit in einem Gate verwendbar.
"""
from importlib import import_module

import pytest

ruff_run = import_module("prozesscode.ruff-run")


class _Lauf:
    """Ergebnis eines subprocess-Laufs, so viel wie der Wrapper davon liest."""

    def __init__(self, stdout: str = "", returncode: int = 0, stderr: str = ""):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


_SAUBER = "All checks passed!\n"
# Echt (ruff 0.x, `check <datei> --output-format concise` über eine Probedatei).
_FUNDE = ("prozesscode/lintprobe_tmp.py:1:8: F401 [*] `os` imported but unused\n"
          "prozesscode/lintprobe_tmp.py:2:8: F401 [*] `sys` imported but unused\n"
          "prozesscode/lintprobe_tmp.py:5:7: E741 Ambiguous variable name: `l`\n"
          "prozesscode/lintprobe_tmp.py:6:12: B905 `zip()` without an explicit `strict=` parameter\n"
          "Found 4 errors.\n"
          "[*] 2 fixable with `--fix` (1 unsafe fix available with `--fix --unsafe-fixes`).\n")


@pytest.mark.aufrufpfad("ruff-run")
def test_sauberer_lauf_meldet_nur_das_verdikt(monkeypatch, capsys):
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", lambda *_a: _Lauf(_SAUBER, 0))
    assert ruff_run.main([]) == 0
    ausgabe = capsys.readouterr().out
    assert ausgabe.strip().startswith("✓")
    assert "F401" not in ausgabe


def test_funde_stehen_vor_dem_verdikt(monkeypatch, capsys):
    """Die Fundstellen zuerst, das Verdikt zuletzt – gelesen wird von unten."""
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", lambda *_a: _Lauf(_FUNDE, 1))
    assert ruff_run.main([]) == 1
    zeilen = capsys.readouterr().out.splitlines()
    ausgabe = "\n".join(zeilen)
    assert "F401" in ausgabe and "B905" in ausgabe
    # Das Verdikt steht HINTER den Fundstellen (danach folgt noch der --verbose-Hinweis).
    verdikt = next(i for i, z in enumerate(zeilen) if z.startswith("✗"))
    fund = next(i for i, z in enumerate(zeilen) if "F401" in z)
    assert fund < verdikt, "Verdikt steht vor den Fundstellen"
    assert "4" in zeilen[verdikt], "Anzahl fehlt im Verdikt"


def test_fehlendes_venv_nennt_den_herstellenden_befehl(monkeypatch, capsys):
    """Gegenprobe zum stummen Ausfall: Nach einem frischen Clone gibt es kein .venv."""
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: False)
    assert ruff_run.main([]) != 0
    ausgabe = capsys.readouterr().out + capsys.readouterr().err
    assert "requirements-dev.txt" in ausgabe
    assert "venv" in ausgabe


def test_verbose_gibt_den_rohen_output(monkeypatch, capsys):
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", lambda *_a: _Lauf(_FUNDE, 1))
    ruff_run.main(["--verbose"])
    assert "Found 4 errors." in capsys.readouterr().out


def test_ohne_fix_flag_wird_nichts_veraendert(monkeypatch):
    """Der Standardlauf ist lesend. Ein Linter, der ungefragt Dateien ändert, ist im
    Review nicht mehr vom Autor zu unterscheiden."""
    gesehen = {}

    def _merke(*befehl: str) -> _Lauf:
        gesehen["befehl"] = befehl
        return _Lauf(_SAUBER)

    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", _merke)
    ruff_run.main([])
    assert "--fix" not in gesehen["befehl"]


def test_nach_fix_wird_der_rest_gemeldet_nicht_der_ausgangsstand(monkeypatch, capsys):
    """Die berichtete Größe muss die gemessene sein.

    Ruff schreibt nach `--fix`: `Found 25 errors (14 fixed, 11 remaining).` Wer daraus die 25
    zieht, meldet den Stand VOR der eigenen Änderung als Ergebnis – die Zahl klingt plausibel
    und ist trotzdem die falsche.
    """
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", lambda *_a: _Lauf(
        "a.py:1:1: E701 x\nFound 25 errors (14 fixed, 11 remaining).\n", 1))
    ruff_run.main(["--fix"])
    verdikt = next(z for z in capsys.readouterr().out.splitlines() if z.startswith("✗"))
    assert "11" in verdikt
    assert "25" not in verdikt


def test_fix_flag_wird_durchgereicht(monkeypatch):
    gesehen = {}

    def _merke(*befehl: str) -> _Lauf:
        gesehen["befehl"] = befehl
        return _Lauf(_SAUBER)

    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", _merke)
    ruff_run.main(["--fix"])
    assert "--fix" in gesehen["befehl"]
    assert "--unsafe-fixes" not in gesehen["befehl"], "unsafe-Fixes gehören unter Augenschein"


def test_der_linter_laeuft_ueber_die_konfigurierten_pfade(monkeypatch):
    """Ein Linter, der die falschen Dateien liest, ist grün und wertlos."""
    gesehen = {}

    def _merke(*befehl: str) -> _Lauf:
        gesehen["befehl"] = befehl
        return _Lauf(_SAUBER)

    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", _merke)
    ruff_run.main([])
    assert any("prozesscode" in teil for teil in gesehen["befehl"])
    assert any("tests" in teil for teil in gesehen["befehl"])


# --- Vollständige Ausgaben und Befehle ---------------------------------------
_HINT = "   (vollständiger Output: --verbose)"


def _lauf_mit(monkeypatch, lauf: _Lauf) -> list:
    befehle = []
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: True)
    monkeypatch.setattr(ruff_run, "_laufe", lambda *befehl: befehle.append(befehl) or lauf)
    return befehle


@pytest.mark.parametrize("argv, erwartet", [
    ([], [str(ruff_run.RUFF), "check", "prozesscode", "tests", "--output-format", "concise"]),
    (["--fix"], [str(ruff_run.RUFF), "check", "prozesscode", "tests", "--output-format",
                 "concise", "--fix"]),
])
def test_der_befehl_ist_vollstaendig(monkeypatch, argv, erwartet):
    """`concise` gibt eine Fundstelle je Zeile – nur daraus lassen sich die Details bilden."""
    befehle = _lauf_mit(monkeypatch, _Lauf(_SAUBER, 0))
    ruff_run.main(argv)
    assert befehle == [tuple(erwartet)]


@pytest.mark.parametrize("argv, verdikt", [
    ([], "✓ ruff: keine Probleme (2 Pfade)"),
    (["--fix"], "✓ ruff: keine Probleme (nach --fix) (2 Pfade)"),
])
def test_sauberer_lauf_vollstaendiges_verdikt(monkeypatch, capsys, argv, verdikt):
    _lauf_mit(monkeypatch, _Lauf(_SAUBER, 0))
    assert ruff_run.main(argv) == 0
    assert capsys.readouterr().out == f"{verdikt}\n{_HINT}\n"


def test_sauberer_lauf_mit_verbose_zeigt_die_rohausgabe(monkeypatch, capsys):
    _lauf_mit(monkeypatch, _Lauf(_SAUBER, 0))
    assert ruff_run.main(["--verbose"]) == 0
    assert capsys.readouterr().out == _SAUBER.rstrip() + "\n✓ ruff: keine Probleme (2 Pfade)\n"


def test_roter_lauf_vollstaendige_ausgabe(monkeypatch, capsys):
    """Die `Found`-Zeile steckt im Verdikt und steht nicht noch einmal bei den Fundstellen."""
    _lauf_mit(monkeypatch, _Lauf(_FUNDE, 1))
    assert ruff_run.main([]) == 1
    assert capsys.readouterr().out == (
        "prozesscode/lintprobe_tmp.py:1:8: F401 [*] `os` imported but unused\n"
        "prozesscode/lintprobe_tmp.py:2:8: F401 [*] `sys` imported but unused\n"
        "prozesscode/lintprobe_tmp.py:5:7: E741 Ambiguous variable name: `l`\n"
        "prozesscode/lintprobe_tmp.py:6:12: B905 `zip()` without an explicit `strict=` parameter\n"
        "[*] 2 fixable with `--fix` (1 unsafe fix available with `--fix --unsafe-fixes`).\n"
        "\n"
        "✗ ruff: 4 Problem(e) – oben aufgelistet\n"
        f"{_HINT}\n")


def test_eine_fundstelle_mit_dem_wort_error_ist_nicht_die_zusammenfassung():
    """Ruffs Meldung für eine fehlende Datei endet auf `(os error 2)` – gezählt wird trotzdem
    erst die `Found`-Zeile."""
    # Echt: `ruff check prozesscode/gibt_es_nicht.py --output-format concise`.
    assert ruff_run._anzahl("prozesscode/gibt_es_nicht.py:1:1: E902 No such file or directory "
                            "(os error 2)\nFound 1 error.\n") == "1"


# Echt, Exit 2, nur auf stderr: `line-length = ` in einer ruff.toml (Pfad gekürzt).
_TOML_KAPUTT = (
    "ruff failed\n"
    "  Cause: Failed to load configuration `/repo/ruff.toml`\n"
    "  Cause: Failed to parse /repo/ruff.toml\n"
    "  Cause: TOML parse error at line 1, column 15\n"
    "  |\n"
    "1 | line-length = \n"
    "  |               ^\n"
    "string values must be quoted, expected literal string\n")


def test_ohne_zusammenfassung_bleibt_die_zahl_offen(monkeypatch, capsys):
    """Fail-open: Bricht ruff ohne `Found`-Zeile ab, ist die Zahl unbekannt – nicht null.
    Die Meldung steht nur auf stderr; ohne sie stünde über dem Verdikt nichts."""
    _lauf_mit(monkeypatch, _Lauf("", 2, stderr=_TOML_KAPUTT))
    assert ruff_run.main([]) == 1
    assert capsys.readouterr().out == (
        "ruff failed\n"
        "  Cause: Failed to load configuration `/repo/ruff.toml`\n"
        "  Cause: Failed to parse /repo/ruff.toml\n"
        "  Cause: TOML parse error at line 1, column 15\n"
        "  |\n"
        "1 | line-length = \n"
        "  |               ^\n"
        "string values must be quoted, expected literal string\n"
        "\n"
        "✗ ruff: ? Problem(e) – oben aufgelistet\n"
        f"{_HINT}\n")


def test_fehlendes_venv_vollstaendige_meldung(monkeypatch, capsys):
    monkeypatch.setattr(ruff_run, "_ruff_vorhanden", lambda: False)
    assert ruff_run.main([]) == 2
    assert capsys.readouterr().out == (
        f"✗ ruff nicht gefunden ({ruff_run.RUFF}).\n"
        "  Werkzeug-Umgebung herstellen:\n"
        "    python3 -m venv .venv\n"
        "    .venv/bin/pip install -r requirements-dev.txt\n"
        "  (Braucht das Systempaket python3.12-venv.)\n")


def test_ruff_laeuft_im_repo_und_liefert_text(monkeypatch):
    """Ohne `cwd` fände ruff seine `ruff.toml` nicht und die relativen Pfade ins Leere."""
    aufrufe = []
    monkeypatch.setattr(ruff_run.subprocess, "run",
                        lambda befehl, **kw: aufrufe.append((befehl, kw)) or "lauf")
    assert ruff_run._laufe("ruff", "check") == "lauf"
    assert aufrufe == [(("ruff", "check"),
                        {"capture_output": True, "text": True, "cwd": ruff_run.ROOT})]


def test_vorhanden_heisst_die_datei_existiert(tmp_path, monkeypatch):
    monkeypatch.setattr(ruff_run, "RUFF", tmp_path / "ruff")
    assert ruff_run._ruff_vorhanden() is False
    (tmp_path / "ruff").touch()
    assert ruff_run._ruff_vorhanden() is True
