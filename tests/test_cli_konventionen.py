"""Jeder Parser unter prozesscode/ lehnt abgekürzte Optionen ab.

argparse nimmt standardmäßig jedes eindeutige Präfix einer Option an. Kommt eine Option hinzu,
deren Name Präfix einer bestehenden ist, oder vertippt man sich zu einem Präfix, läuft der Aufruf
still als die längere Option – bei den Tracker-Werkzeugen landet das in den Dateien. Darum baut
jedes Werkzeug seinen Parser über `prozesscode._cli.Parser`, nie direkt über `ArgumentParser`.
"""
import argparse
import ast
from pathlib import Path

import pytest

from prozesscode._cli import Parser

ROOT = Path(__file__).resolve().parent.parent


def _direkte_parser(quelltext: str) -> list[int]:
    return [k.lineno for k in ast.walk(ast.parse(quelltext))
            if isinstance(k, ast.Call)
            and (getattr(k.func, "attr", None) or getattr(k.func, "id", None)) == "ArgumentParser"]


def test_kein_werkzeug_baut_seinen_parser_direkt():
    funde = [f"{pfad.relative_to(ROOT)}:{zeile}"
             for pfad in sorted((ROOT / "prozesscode").rglob("*.py"))
             if "__pycache__" not in pfad.parts
             for zeile in _direkte_parser(pfad.read_text(encoding="utf-8"))]
    assert funde == [], ("Parser über prozesscode._cli.Parser bauen – ArgumentParser ergänzt "
                         "abgekürzte Optionen still:\n  " + "\n  ".join(funde))


@pytest.mark.parametrize("quelltext, erwartet", [
    ("argparse.ArgumentParser(description='x')", [1]),
    ("ArgumentParser()", [1]),
    # Gegenprobe: der eigene Parser und andere Aufrufe bleiben unbeanstandet.
    ("Parser(description='x')", []),
    ("sub.add_parser('get', help='x')", []),
])
def test_pruefung_erkennt_direkte_parser(quelltext, erwartet):
    assert _direkte_parser(quelltext) == erwartet


def _mit_unterbefehl(klasse) -> argparse.ArgumentParser:
    parser = klasse(prog="werkzeug")
    parser.add_argument("--beobachtung-anhaengen")
    setzen = parser.add_subparsers(dest="befehl").add_parser("set")
    setzen.add_argument("--titel-neu")
    return parser


@pytest.mark.parametrize("argumente", [
    ["--beobachtung=x"],
    ["set", "--titel=x"],  # Unterbefehl-Parser erben die Einstellung
])
def test_parser_lehnt_abgekuerzte_optionen_ab(argumente, capsys):
    with pytest.raises(SystemExit) as ende:
        _mit_unterbefehl(Parser).parse_args(argumente)
    assert ende.value.code == 2
    assert "unrecognized arguments" in capsys.readouterr().err


@pytest.mark.parametrize("argumente", [["--beobachtung=x"], ["set", "--titel=x"]])
def test_argparse_selbst_ergaenzt_die_abkuerzung(argumente):
    """Gegenprobe: Ohne den eigenen Parser liefe derselbe Aufruf still durch."""
    assert _mit_unterbefehl(argparse.ArgumentParser).parse_args(argumente)
