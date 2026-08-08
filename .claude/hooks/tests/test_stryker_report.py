"""Tests für _stryker_report.py – Survivor-Ausgabe (OBS-S111-3).

Der Stryker-Report führt je Mutant `location.start`/`location.end`, `coveredBy`, `killedBy`,
`id`, `static` und `statusReason`; ausgegeben wurden bisher nur Startzeile, Mutator und
Ersetzung. Zwei Verluste sind handlungsrelevant:

* Ohne `location.end` ist die Startzeile bei `Block removal mutation` mehrdeutig – liegt sie
  in einem `try`/`catch` mit verschachtelten Blöcken, sagt „Zeile 304 → {}" nicht, welcher
  Block entfernt wurde.
* Die Anzahl deckender Tests trennt „ein Test deckt ab und tötet nicht" von „zwölf Tests
  decken ab und keiner tötet" – ein Unterschied für die Reaktion.

Nicht abgedeckt vom alten Vorwurf: Die Unterscheidung Survived/NoCoverage ging NIE verloren,
`collect_undetected` trennt sie über `status` in zwei Gruppen (in S115 am Code geprüft).
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
sr = import_module("_stryker_report")


def _mutant(line, end_line=None, mutator="Equality mutation", replacement=">=",
            covered_by=None, status_reason=None):
    m = {
        "location": {"start": {"line": line, "column": 5},
                     "end": {"line": end_line if end_line is not None else line, "column": 20}},
        "mutatorName": mutator,
        "replacement": replacement,
    }
    if covered_by is not None:
        m["coveredBy"] = covered_by
    if status_reason is not None:
        m["statusReason"] = status_reason
    return m


def _out(*mutants, datei="Foo.cs"):
    return "\n".join(sr.format_mutant_group({datei: list(mutants)}))


# --- Zeilenspanne ------------------------------------------------------------
def test_single_line_mutant_shows_one_line():
    assert "Zeile  318" in _out(_mutant(318))
    assert "318-318" not in _out(_mutant(318))


def test_multi_line_mutant_shows_the_span():
    """Der Block-removal-Fall: ohne Endzeile bleibt unklar, welcher Block entfernt wurde."""
    out = _out(_mutant(304, end_line=312, mutator="Block removal mutation", replacement="{}"))
    assert "304-312" in out


def test_mutants_stay_sorted_by_start_line():
    out = _out(_mutant(320), _mutant(304), _mutant(311))
    assert out.index("304") < out.index("311") < out.index("320")


# --- Deckende Tests ----------------------------------------------------------
def test_coverage_count_is_shown_in_plural():
    assert "3 Tests decken ab" in _out(_mutant(318, covered_by=["t1", "t2", "t3"]))


def test_coverage_count_is_shown_in_singular():
    assert "1 Test deckt ab" in _out(_mutant(318, covered_by=["t1"]))


def test_missing_coverage_field_is_tolerated():
    """`coveredBy` fehlt oder ist null (im echten Report bei Ignored/NoCoverage gesehen)."""
    assert "deckt ab" not in _out(_mutant(318))
    assert "deckt ab" not in _out(_mutant(318, covered_by=None))


def test_empty_coverage_list_is_not_reported_as_zero():
    """NoCoverage-Mutanten stehen schon in ihrer eigenen Gruppe – „0 Tests" wäre Rauschen."""
    assert "deckt ab" not in _out(_mutant(318, covered_by=[]))


# --- statusReason ------------------------------------------------------------
def test_status_reason_is_shown_when_present():
    out = _out(_mutant(318, status_reason="kein Test für den Remount-key"))
    assert "kein Test für den Remount-key" in out


def test_status_reason_is_omitted_when_empty():
    assert _out(_mutant(318, status_reason="")) == _out(_mutant(318))


def test_status_reason_keeps_only_the_first_line():
    """Am echten Report gesehen: `statusReason` kann einen Assertion-Diff mit komplettem
    DOM-Dump tragen – hunderte Zeilen. Der Wrapper gibt im Fehlerfall nur Analyse-Relevantes
    aus, also erste Zeile statt Fließband."""
    out = _out(_mutant(318, status_reason="Erwartet: fokussiert\n<div>\n  <input />\n</div>"))
    assert "Erwartet: fokussiert" in out
    assert "<input />" not in out


def test_status_reason_is_capped_in_length():
    lang = "A" * 400
    out = _out(_mutant(318, status_reason=lang))
    assert "…" in out
    assert "A" * 400 not in out
    # Die Ausgabe bleibt in der Größenordnung einer Zeile.
    assert max(len(z) for z in out.splitlines()) < 160


# --- unverändertes Verhalten -------------------------------------------------
def test_file_header_keeps_the_count():
    assert "Foo.cs (2)" in _out(_mutant(1), _mutant(2))


def test_mutator_and_replacement_are_kept():
    out = _out(_mutant(318, mutator="Equality mutation", replacement=">="))
    assert "Equality mutation" in out
    assert ">=" in out


def test_missing_replacement_falls_back():
    m = _mutant(318)
    del m["replacement"]
    assert "?" in _out(m)
