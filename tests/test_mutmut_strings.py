"""Tests für die String-Mutanten-Erkennung in mutmut-run.py.

**Der Befund, der das nötig macht** (S129, an drei Modulen gemessen): 48 %, 53 % und 79 %
der überlebenden Mutanten verändern nur einen Stringinhalt. mutmut umschließt ihn dabei mit
`XX…XX` – `"Anker setzen"` wird zu `"XXAnker setzenXX"`. Der ursprüngliche Text bleibt damit
**Substring**, und ein `in`-Test kann so einen Mutanten prinzipiell nicht töten. Tötbar wäre
er nur durch einen exakten Vergleich der ganzen Meldung, und der bricht bei jeder
Umformulierung – ein Test, der schlechter ist als die Lücke, die er schließt.

Ohne die Erkennung wäre die Sperrklinke unbrauchbar: Jede neue Erklärzeile in einer
Guard-Meldung erzeugt einen unsterblichen Mutanten, senkt den Score und reißt die Klinke,
ohne dass sich an der Testgüte etwas geändert hat. In einem Projekt, dessen Meldungen
ausdrücklich den Ausweg nennen sollen, ist das kein Randfall.

Abschalten lässt sich der Mutator nicht: `mutation_by_ast_type` in `mutmut/__init__.py` ist
fest verdrahtet, und mutmut 3 kennt keine Option dafür.
"""
from importlib import import_module

mr = import_module("prozesscode.mutmut-run")

# So legt mutmut einen Mutantenbaum an: je Funktion das Original und je Mutation eine Kopie.
BAUM = '''
def x_pruefe__mutmut_orig(pfad):
    return ["Anker setzen (Termin oder Ereignis)"] if not pfad else []


def x_pruefe__mutmut_1(pfad):
    return ["XXAnker setzen (Termin oder Ereignis)XX"] if not pfad else []


def x_pruefe__mutmut_2(pfad):
    return ["Anker setzen (Termin oder Ereignis)"] if pfad else []


def x_lies__mutmut_orig(a, b):
    return a + b


def x_lies__mutmut_1(a, b):
    return a - b
'''


def baum(tmp_path, modul="prozesscode.beispiel"):
    ziel = tmp_path / "mutants" / "prozesscode"
    ziel.mkdir(parents=True)
    (ziel / "beispiel.py").write_text(BAUM, encoding="utf-8")
    return modul


def test_findet_den_string_mutanten(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.string_mutanten(baum(tmp_path)) == {
        "prozesscode.beispiel.x_pruefe__mutmut_1"}


def test_laesst_verhaltensmutanten_in_ruhe(tmp_path, monkeypatch):
    """GEGENPROBE: Ein umgedrehtes `not` und ein `+`→`-` sind echte Befunde."""
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    gefunden = mr.string_mutanten(baum(tmp_path))
    assert "prozesscode.beispiel.x_pruefe__mutmut_2" not in gefunden
    assert "prozesscode.beispiel.x_lies__mutmut_1" not in gefunden


def test_ein_XX_im_originalcode_erzeugt_keinen_fehltreffer(tmp_path, monkeypatch):
    """Enthält der Originalcode selbst ein `XX`, ist es keine Mutation."""
    ziel = tmp_path / "mutants" / "prozesscode"
    ziel.mkdir(parents=True)
    (ziel / "beispiel.py").write_text(
        'def x_f__mutmut_orig():\n    return "XXL"\n\n\n'
        'def x_f__mutmut_1():\n    return "XXL" if True else None\n',
        encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.string_mutanten("prozesscode.beispiel") == set()


def test_fehlender_baum_liefert_leere_menge(tmp_path, monkeypatch):
    """Fail-open: Ohne Baum wird nichts ausgeklammert, statt den Lauf abzubrechen."""
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.string_mutanten("prozesscode.gibt-es-nicht") == set()


# --- Wirkung auf Score und Verdikt -------------------------------------------
def test_string_mutanten_zaehlen_nicht_in_den_score():
    eintraege = [("m.x_f__mutmut_1", "survived"), ("m.x_f__mutmut_2", "survived"),
                 ("m.x_f__mutmut_3", "killed")]
    getoetet, beurteilbar = mr.score(eintraege, ignorieren={"m.x_f__mutmut_1"})
    assert (getoetet, beurteilbar) == (1, 2)


def test_das_verdikt_weist_sie_getrennt_aus():
    """Verschweigen wäre falsch: Die Stellen sind ungeprüft, nur nicht sinnvoll prüfbar."""
    eintraege = [("m.x_f__mutmut_1", "survived"), ("m.x_f__mutmut_2", "survived")]
    verdikt, _details = mr.baue_verdikt(eintraege, ignorieren={"m.x_f__mutmut_1"})
    assert "1 überlebende an Meldungstexten" in verdikt
