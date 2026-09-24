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

    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


_SAUBER = "All checks passed!\n"
_FUNDE = ("prozesscode/foo.py:12:5: F401 [*] `os` imported but unused\n"
          "prozesscode/bar.py:3:1: B023 Function definition does not bind loop variable\n"
          "Found 2 errors.\n")


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
    assert "F401" in ausgabe and "B023" in ausgabe
    # Das Verdikt steht HINTER den Fundstellen (danach folgt noch der --verbose-Hinweis).
    verdikt = next(i for i, z in enumerate(zeilen) if z.startswith("✗"))
    fund = next(i for i, z in enumerate(zeilen) if "F401" in z)
    assert fund < verdikt, "Verdikt steht vor den Fundstellen"
    assert "2" in zeilen[verdikt], "Anzahl fehlt im Verdikt"


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
    assert "Found 2 errors." in capsys.readouterr().out


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
