"""Der Aufrufpfad der Erfassungs-Scripte – nicht die Funktion dahinter (LL-S128-1).

Die Modul-Tests prüfen `add()`; ob die CLI das Pflichtfeld überhaupt verlangt, sehen sie nicht.
Aufgerufen wird bewusst OHNE Argumente: argparse bricht dann ab, bevor irgendetwas geschrieben
wird, und nennt alle fehlenden Pflichtargumente – ein Lauf kann die echten Tracker so nie
verändern, auch nicht in einer RED-Phase.
"""
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.aufrufpfad("obs", "td", "oq")
@pytest.mark.parametrize("modul", ["obs", "td", "oq"])
def test_add_verlangt_den_aufschubgrund(modul):
    lauf = subprocess.run([sys.executable, "-m", f"prozesscode.{modul}", "add"],
                          cwd=REPO, capture_output=True, text=True, timeout=30)
    assert lauf.returncode == 2
    assert "--aufschubgrund" in lauf.stderr


def _cli(monkeypatch, capsys, modul: str, *argumente: str):
    """`main()` in-process mit dem `sys.argv` eines Starts per `python -m` – derselbe Weg ohne
    Prozessstart je Aufruf."""
    monkeypatch.setattr(sys, "argv", [f"prozesscode.{modul}", *argumente])
    with pytest.raises(SystemExit) as ende:
        import_module(f"prozesscode.{modul}").main()
    return ende.value.code, capsys.readouterr()


@pytest.mark.aufrufpfad("obs")
def test_obs_set_laesst_ersetzen_und_anhaengen_nicht_zugleich_zu(monkeypatch, capsys):
    """Beides zusammen ist widersprüchlich; argparse bricht ab, bevor etwas geschrieben wird.

    Die ID gibt es nie: Der Aufruf läuft gegen die echte Datei, und in einer RED-Phase hätte
    argparse `--beobachtung` still als Präfix von `--beobachtung-anhängen` gelesen.
    """
    code, ausgabe = _cli(monkeypatch, capsys, "obs", "set", "OBS-S000-0",
                         "--beobachtung", "neu", "--beobachtung-anhängen", "mehr")
    assert code == 2
    assert "not allowed with" in ausgabe.err


@pytest.mark.aufrufpfad("obs")
def test_obs_set_ergaenzt_keine_abgekuerzten_optionen(monkeypatch, capsys):
    """`--beob` darf nicht still zu einer der beiden Beobachtungs-Optionen werden."""
    code, ausgabe = _cli(monkeypatch, capsys, "obs", "set", "OBS-S000-0", "--beob", "x")
    assert code == 2
    assert "unrecognized arguments: --beob" in ausgabe.err


@pytest.mark.aufrufpfad("obs", "td", "oq")
@pytest.mark.parametrize("modul, felder", [
    ("obs", ["--beobachtung", "--vorprägung", "--aufschubgrund"]),
    ("td", ["--aufschubgrund"]),
    ("oq", ["--aufschubgrund"]),
])
def test_set_bietet_die_korrekturfelder_an(monkeypatch, capsys, modul, felder):
    code, ausgabe = _cli(monkeypatch, capsys, modul, "set", "--help")
    assert code == 0
    assert all(f in ausgabe.out for f in felder)
