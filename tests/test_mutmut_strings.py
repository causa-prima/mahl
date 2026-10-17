"""Tests für den Umgang von mutmut-run.py mit Meldungstexten.

Jeder String-Mutant zählt. Ein Meldungstext erzeugt keine Mutanten, wenn er als
**Modulkonstante** steht – mutmut mutiert nur Funktionsrümpfe. Wo ein Text in der Funktion
bleiben muss, nimmt ihn `# pragma: no mutate – <Grund>` aus; diese Ausnahmen zählt mutmut
selbst nirgends, deshalb nennt sie das Verdikt (Regel: `coding-guideline-python.md`,
„Meldungen sagen, was zu tun ist").

Ein Filter, der String-Mutanten pauschal ausklammerte, blendete auch Protokollschlüssel und
Konstanten aus: In `check-bash-permission` waren es 114 von 245 String-Überlebenden.
"""
from importlib import import_module

import pytest

mr = import_module("prozesscode.mutmut-run")

QUELLE = '''
HINWEIS = "Modulkonstante – wird nicht mutiert"


def f(x):
    return "deny" if x else "allow"  # pragma: no mutate – Meldungstext


def g():
    text = "# pragma: no mutate steht hier nur im String"
    return text
    # pragma: no mutate block
'''


def quelle(tmp_path, monkeypatch, text=QUELLE, modul="prozesscode.beispiel"):
    ziel = tmp_path / "prozesscode"
    ziel.mkdir(parents=True)
    (ziel / "beispiel.py").write_text(text, encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    return modul


def test_zaehlt_die_pragma_kommentare_eines_moduls(tmp_path, monkeypatch):
    assert mr.pragma_zeilen(quelle(tmp_path, monkeypatch)) == 2


def test_ein_pragma_im_string_ist_keines(tmp_path, monkeypatch):
    """GEGENPROBE: mutmut liest Kommentare, nicht Text – ein Docstring, der das Pragma
    erwähnt, nimmt nichts aus und darf nicht mitgezählt werden."""
    modul = quelle(tmp_path, monkeypatch, text='X = "# pragma: no mutate"\n"""# pragma: no mutate"""\n')
    assert mr.pragma_zeilen(modul) == 0


@pytest.mark.parametrize("auf, zu", [("(", ")"), ("[", "]"), ("{", "}")])
def test_ein_pragma_mitten_in_einem_ausdruck_ist_keines(tmp_path, monkeypatch, auf, zu):
    """Gemessen an mutmut 3.8.0 (`commit_msg`): Es liest das Pragma am Ende einer Anweisung und
    auf eigener Zeile davor. Innerhalb von Klammern übergeht es den Kommentar – der Mutant
    entsteht trotzdem."""
    text = f"def f():\n    return {auf}\n        1,  # pragma: no mutate\n    {zu}  # pragma: no mutate\n"
    assert mr.pragma_zeilen(quelle(tmp_path, monkeypatch, text=text)) == 1


def test_fehlende_quelle_zaehlt_null(tmp_path, monkeypatch):
    """Fail-open: Ohne Datei keine Zählung, kein Abbruch."""
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.pragma_zeilen("prozesscode.gibt-es-nicht") == 0


def test_bindestrich_module_finden_ihre_datei(tmp_path, monkeypatch):
    ziel = tmp_path / "prozesscode" / "hooks"
    ziel.mkdir(parents=True)
    (ziel / "check-x.py").write_text("def f():\n    return 1  # pragma: no mutate\n",
                                     encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.pragma_zeilen("prozesscode.hooks.check-x") == 1


def test_das_verdikt_nennt_die_pragma_ausnahmen():
    verdikt, _details = mr.baue_verdikt([("m.x_f__mutmut_1", "killed")], pragmas=3)
    assert "3 Zeilen per Pragma ausgenommen" in verdikt


def test_ohne_pragma_kein_nachsatz():
    verdikt, _details = mr.baue_verdikt([("m.x_f__mutmut_1", "killed")])
    assert "Pragma" not in verdikt


def test_bei_ueberlebenden_nennt_das_verdikt_den_weg_fuer_meldungstexte():
    _verdikt, details = mr.baue_verdikt([("m.x_f__mutmut_1", "survived")])
    hinweis = "\n".join(details)
    assert "Modulkonstante" in hinweis and "# pragma: no mutate" in hinweis


def test_jeder_string_mutant_zaehlt_in_den_score():
    """Kein Filter mehr: Ein überlebender Mutant an einem String ist ein Befund."""
    eintraege = [("m.x_f__mutmut_1", "survived"), ("m.x_f__mutmut_2", "killed")]
    assert mr.score(eintraege) == (1, 2)
