"""Tests für das Lesen der mutmut-Ergebnisse aus den `.meta`-Dateien.

**Warum nicht `mutmut results`** – der Weg, mit dem der Wrapper anfing: Ein Mutant in
`has_unsafe_output_redirect` endete mit SIGKILL (Exit `-9`, vermutlich eine
Regex-Katastrophe). `status_by_exit_code` in mutmut kennt diesen Code nicht, und
`results` stirbt an einem `KeyError: -9` – **mitten in der Ausgabe**. Der Wrapper las
daraufhin 86 statt 646 Mutanten und bildete daraus einen Score, ohne etwas zu merken:
genau die Klasse STUMM, gegen die er gebaut ist.

Der Mutant ist deterministisch, `--frisch` hilft also nicht. Die `.meta`-Dateien sind
dieselbe Quelle, die `results` liest – nur ohne den Absturz und ohne einen Subprozess über
11.000 Zeilen.
"""
import json
from importlib import import_module

mr = import_module("prozesscode.mutmut-run")


def meta(tmp_path, modul="prozesscode/beispiel", **codes):
    pfad = tmp_path / "mutants" / f"{modul}.py.meta"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    prefix = modul.replace("/", ".")
    pfad.write_text(json.dumps({
        "exit_code_by_key": {f"{prefix}.{name}": code for name, code in codes.items()},
        "hash_by_function_name": {},
    }), encoding="utf-8")
    return tmp_path


def test_liest_status_aus_den_exit_codes(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "ROOT", meta(
        tmp_path, x_f__mutmut_1=1, x_f__mutmut_2=0, x_f__mutmut_3=5, x_f__mutmut_4=None))
    assert dict(mr.lies_ergebnisse()) == {
        "prozesscode.beispiel.x_f__mutmut_1": "killed",
        "prozesscode.beispiel.x_f__mutmut_2": "survived",
        "prozesscode.beispiel.x_f__mutmut_3": "no tests",
        "prozesscode.beispiel.x_f__mutmut_4": "not checked",
    }


def test_sigkill_gilt_als_ausser_wertung():
    """Exit -9 heißt: Der Kernel hat den Mutanten hart beendet – meist eine Endlosschleife
    oder ein Speicherfraß, den die Mutation erzeugt hat. Das sagt nichts über die Tests,
    also gehört er wie ein Timeout aus dem Bruch. mutmut selbst kennt den Code nicht."""
    assert mr.STATUS_JE_EXIT_CODE[-9] == "timeout"


def test_ein_unbekannter_exit_code_reisst_den_lauf_nicht_mit(tmp_path, monkeypatch):
    """GEGENPROBE zum mutmut-Bug: Genau daran ist `results` gestorben.

    Ein Code, den niemand vorhergesehen hat, darf höchstens einen Mutanten unbewertbar
    machen – nicht die Auswertung aller übrigen.
    """
    monkeypatch.setattr(mr, "ROOT", meta(tmp_path, x_f__mutmut_1=1, x_f__mutmut_2=-77))
    gelesen = dict(mr.lies_ergebnisse())
    assert gelesen["prozesscode.beispiel.x_f__mutmut_1"] == "killed"
    assert gelesen["prozesscode.beispiel.x_f__mutmut_2"] == "unbekannt"


def test_der_ausschnitt_filtert_auch_hier(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "ROOT", meta(tmp_path, x_f__mutmut_1=1))
    assert mr.lies_ergebnisse(ausschnitt="prozesscode.anderes") == []
    assert mr.lies_ergebnisse(ausschnitt="prozesscode.beispiel") != []


def test_ohne_mutantenbaum_keine_ergebnisse(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    assert mr.lies_ergebnisse() == []


def test_eine_kaputte_meta_uebergeht_nur_ihre_datei(tmp_path, monkeypatch):
    """Fail-open je Datei: Ein abgebrochener Schreibvorgang darf nicht alle Module kosten."""
    wurzel = meta(tmp_path, x_f__mutmut_1=1)
    (wurzel / "mutants" / "prozesscode" / "kaputt.py.meta").write_text(
        "{kein json", encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", wurzel)
    assert len(mr.lies_ergebnisse()) == 1
