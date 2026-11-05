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
import json
from importlib import import_module
from pathlib import Path

import pytest

sr = import_module("prozesscode._stryker_report")


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
    assert _out(m).splitlines()[2] == "           → ?"


# --- exakte Ausgabe der Mutanten-Gruppe ---------------------------------------
def test_gruppe_ohne_grund_und_ohne_deckung_hat_genau_drei_zeilen_und_eine_leerzeile():
    assert sr.format_mutant_group({"Foo.cs": [_mutant(318)]}) == [
        "  Foo.cs (1)",
        "    Zeile  318  Equality mutation",
        "           → >=",
        "",
    ]


def test_mutant_ohne_endposition_zeigt_nur_die_startzeile():
    m = _mutant(318)
    del m["location"]["end"]
    assert _out(m).splitlines()[1] == "    Zeile  318  Equality mutation"


def test_kurzer_einzeiliger_grund_bleibt_unveraendert():
    assert _out(_mutant(318, status_reason="Layout-Wert")).splitlines()[3] == "             (Layout-Wert)"


def test_mehrzeiliger_grund_wird_mit_auslassungszeichen_markiert():
    """Zwei Zeilen genügen: Was nach der ersten kommt, ist abgeschnitten und muss es sagen."""
    zeile = _out(_mutant(318, status_reason="Erwartet: fokussiert\n<div/>")).splitlines()[3]
    assert zeile == "             (Erwartet: fokussiert…)"


def test_grund_genau_an_der_laengengrenze_wird_nicht_gekuerzt():
    grund = "A" * sr._MAX_REASON
    assert _out(_mutant(318, status_reason=grund)).splitlines()[3] == f"             ({grund})"


def test_grund_ueber_der_laengengrenze_wird_auf_die_grenze_gekuerzt():
    grund = "A" * (sr._MAX_REASON + 1)
    zeile = _out(_mutant(318, status_reason=grund)).splitlines()[3]
    assert zeile == f"             ({'A' * sr._MAX_REASON}…)"


# --- Kurzpfade ----------------------------------------------------------------
@pytest.mark.parametrize("voll, kurz", [
    # Stryker.NET: absolute Pfade
    ("/home/kieritz/repos/mahl/Server/Types/NonEmptyImmutableArray.cs",
     "Server/Types/NonEmptyImmutableArray.cs"),
    # Windows-Trenner, Testprojekt
    ("C:\\repos\\mahl\\Server.Tests\\RecipesEndpointsTests.cs", "Server.Tests/RecipesEndpointsTests.cs"),
    # StrykerJS: schon projekt-relativ
    ("src/pages/IngredientsPage.tsx", "src/pages/IngredientsPage.tsx"),
    # kein bekannter Anker: nur der Dateiname
    ("/home/kieritz/repos/mahl/Tools/Program.cs", "Program.cs"),
])
def test_kurzpfad_schneidet_ab_dem_projektanker(voll, kurz):
    assert sr.short_path(voll) == kurz


# --- echter Report (Stryker.NET) ------------------------------------------------
# Auszug aus StrykerOutput/Backend/2026-10-29.14-35-47/reports/mutation-report.json: vier der
# Dateien unverändert übernommen (Mutanten, `language`), nur das Feld `source` entfernt. Er
# enthält je einen Survivor (mit Deckung) und einen NoCoverage-Mutanten (mit `statusReason`),
# Ignored-, Killed- und mehrzeilige Mutanten sowie eine Datei ganz ohne Mutanten.
_ECHTER_REPORT = json.loads(
    (Path(__file__).parent / "fixtures" / "stryker_backend_auszug.json").read_text(encoding="utf-8"))


def test_echter_report_ergibt_metriken_und_gate():
    metriken = sr.compute_metrics(_ECHTER_REPORT["files"])
    assert metriken == {
        "counts": {"Ignored": 3, "Killed": 4, "Survived": 1, "NoCoverage": 1},
        "detected": 4,
        "undetected": 2,
        "total_valid": 6,
        "mutated_files": 2,
        "score": 4 / 6 * 100,
    }
    assert sr.format_score(metriken) == "66.7%"
    assert sr.gate_code(metriken) == 1
    assert (sr.format_status_breakdown(metriken)
            == "   Status-Verteilung: Ignored: 3, Killed: 4, NoCoverage: 1, Survived: 1")


def test_echter_report_trennt_survivor_und_no_coverage():
    survivors, nocoverage = sr.collect_undetected(_ECHTER_REPORT["files"])
    datei = "Server/Types/NonEmptyImmutableArray.cs"
    assert {k: [m["id"] for m in v] for k, v in survivors.items()} == {datei: ["186"]}
    assert {k: [m["id"] for m in v] for k, v in nocoverage.items()} == {datei: ["187"]}


def test_echter_report_formatiert_survivor_und_no_coverage():
    survivors, nocoverage = sr.collect_undetected(_ECHTER_REPORT["files"])
    assert sr.format_mutant_group(survivors) == [
        "  Server/Types/NonEmptyImmutableArray.cs (1)",
        "    Zeile   15  Conditional (false) mutation",
        '           → (false?throw new InvalidOperationException("Uninitialized") :_items)'
        "   (2 Tests decken ab)",
        "",
    ]
    assert sr.format_mutant_group(nocoverage) == [
        "  Server/Types/NonEmptyImmutableArray.cs (1)",
        "    Zeile   15  String mutation",
        '           → ""',
        "             (Not covered by any test.)",
        "",
    ]


def test_mehrere_dateien_mit_survivors_landen_getrennt_und_eine_datei_ohne_mutanten_stoert_nicht():
    files = {
        "/r/Server/A.cs": {"mutants": [_mutant(3) | {"status": "Survived"},
                                       _mutant(1) | {"status": "Survived"}]},
        "/r/Server/B.cs": {"mutants": [_mutant(7) | {"status": "NoCoverage"},
                                       _mutant(8) | {"status": "Killed"}]},
        "/r/Server/C.cs": {},
    }
    survivors, nocoverage = sr.collect_undetected(files)
    assert {k: len(v) for k, v in survivors.items()} == {"Server/A.cs": 2}
    assert {k: len(v) for k, v in nocoverage.items()} == {"Server/B.cs": 1}
