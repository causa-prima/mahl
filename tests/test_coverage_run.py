"""Tests für coverage-run.py – Testabdeckung des Prozess-Codes als METRIK.

Drei Zusagen: Der Bericht nennt die Gesamtzahl, hebt die ungetesteten Module heraus statt
die gut gedeckten aufzulisten, und bleibt ein Report (Exit 0) statt ein Gate zu werden.
Warum kein Gate: `coding-guideline-python.md`, „Was nicht gilt".
"""
from importlib import import_module

cov = import_module("prozesscode.coverage-run")


_AUSGABE = """\
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
prozesscode/doc.py                    300      3    99%
prozesscode/retro_report.py           561    422    25%
prozesscode/vitest-run.py              53     53     0%
prozesscode/tracker.py                 44     44     0%
-----------------------------------------------------------
TOTAL                                   11735   3166    73%

1060 passed in 73.17s
"""


class _Lauf:
    def __init__(self, stdout=_AUSGABE, returncode=0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


def test_die_gesamtzahl_wird_berichtet(monkeypatch, capsys):
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf())
    assert cov.main([]) == 0
    assert "73" in capsys.readouterr().out


def test_ungetestete_module_werden_zuerst_genannt(monkeypatch, capsys):
    """0 % ist die einzige Zahl, die für sich spricht: Diese Datei hat KEINEN Test."""
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf())
    cov.main([])
    ausgabe = capsys.readouterr().out
    assert "vitest-run.py" in ausgabe and "tracker.py" in ausgabe
    assert ausgabe.index("vitest-run.py") < ausgabe.index("retro_report.py")


def test_gut_gedeckte_module_verstopfen_den_bericht_nicht(monkeypatch, capsys):
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf())
    cov.main([])
    assert "doc.py" not in capsys.readouterr().out


def test_der_bericht_ist_kein_gate(monkeypatch):
    """Exit 0 auch bei niedriger Abdeckung – sonst wäre die Metrik ein Gate."""
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf())
    assert cov.main([]) == 0


def test_ein_fehlgeschlagener_testlauf_wird_gemeldet(monkeypatch, capsys):
    """Gegenprobe: Bei roten Tests ist die Coverage-Zahl bedeutungslos und darf nicht
    als Befund durchgehen."""
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf("2 failed, 1058 passed\n", 1))
    assert cov.main([]) != 0
    assert "rot" in capsys.readouterr().out.lower()


def test_fehlendes_venv_nennt_den_herstellenden_befehl(monkeypatch, capsys):
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: False)
    assert cov.main([]) != 0
    assert "requirements-dev.txt" in capsys.readouterr().out


def test_verbose_gibt_die_volle_tabelle(monkeypatch, capsys):
    monkeypatch.setattr(cov, "_venv_vorhanden", lambda: True)
    monkeypatch.setattr(cov, "_laufe", lambda *_a: _Lauf())
    cov.main(["--verbose"])
    assert "doc.py" in capsys.readouterr().out
