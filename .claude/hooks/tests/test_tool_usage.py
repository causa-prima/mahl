"""Tests für tool-usage.py – die Filter-Quote aus OBS-S085-3.

Gezählt wird die AUSFÜHRUNG eines Wrappers mit nachgelagertem Filter. Zwei Abgrenzungen
tragen die Aussage: Das bloße Lesen einer Wrapper-Datei ist kein Lauf, und ein Filter vor
dem Wrapper filtert dessen Ausgabe nicht.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
tu = import_module("tool-usage")

STAMP = "[2026-07-15 10:00:00] "


def test_plain_run_is_counted_unfiltered():
    assert tu.classify_line(f"{STAMP}python3 .claude/scripts/vitest-run.py") == ("2026-07", "vitest-run", False)


def test_trailing_filter_is_counted():
    line = f"{STAMP}python3 .claude/scripts/qa-check.py | tail -5"
    assert tu.classify_line(line) == ("2026-07", "qa-check", True)


def test_filter_before_the_wrapper_does_not_count():
    """`grep x foo | python3 … qa-check.py` filtert die Wrapper-Ausgabe nicht."""
    line = f"{STAMP}grep -r foo . | python3 .claude/scripts/qa-check.py"
    assert tu.classify_line(line) == ("2026-07", "qa-check", False)


def test_reading_a_wrapper_file_is_not_a_run():
    """Datei-Inspektion darf nicht als gefilterte Ausführung zählen (Kernabgrenzung)."""
    assert tu.classify_line(f"{STAMP}grep -n collect_coverage .claude/scripts/dotnet-test.py") is None


def test_continuation_lines_without_timestamp_are_skipped():
    assert tu.classify_line("    --filter Foo | head -3") is None


def test_non_wrapper_commands_are_ignored():
    assert tu.classify_line(f"{STAMP}python3 .claude/scripts/decisions.py list") is None
    assert tu.classify_line(f"{STAMP}git status") is None


def test_absolute_wrapper_path_is_recognized():
    line = f"{STAMP}python3 /home/kieritz/repos/mahl/.claude/scripts/eslint-run.py | grep error"
    assert tu.classify_line(line) == ("2026-07", "eslint-run", True)


def test_analysis_scripts_are_deliberately_not_wrappers():
    """`read-breakdown.py` ist ein Analyse-Script – seine lange Ausgabe zu schneiden ist
    bestimmungsgemäß und würde die Quote gegenüber der S109-Basislinie verfälschen."""
    assert "read-breakdown" not in tu.WRAPPERS
    assert tu.classify_line(f"{STAMP}python3 .claude/scripts/read-breakdown.py | head") is None


# --- Aggregation -------------------------------------------------------------
def test_measure_counts_runs_and_quote(tmp_path):
    log = tmp_path / "allowed-commands.log"
    log.write_text(
        f"{STAMP}python3 .claude/scripts/vitest-run.py\n"
        f"{STAMP}python3 .claude/scripts/vitest-run.py | tail -3\n"
        "[2026-06-01 09:00:00] python3 .claude/scripts/qa-check.py | grep OK\n"
        f"{STAMP}git status\n",
        encoding="utf-8",
    )
    runs, filtered, by_wrapper, examples = tu.measure_filter_quote(log)
    assert runs == {"2026-07": 2, "2026-06": 1}
    assert filtered == {"2026-07": 1, "2026-06": 1}
    assert by_wrapper == {"vitest-run": 1, "qa-check": 1}
    assert len(examples) == 2


def test_measure_tolerates_a_missing_log(tmp_path):
    runs, filtered, by_wrapper, examples = tu.measure_filter_quote(tmp_path / "fehlt.log")
    assert (runs, filtered, by_wrapper, examples) == ({}, {}, {}, [])


# --- Datumsfenster -----------------------------------------------------------
# Die Wirkung einer Maßnahme zeigt sich nur an den Läufen NACH ihrem Stichtag. Die
# Monats-Buckets allein können das nicht trennen, wenn der Stichtag mitten im Monat liegt
# (S109: 29.07.) – dann mischt der Juli-Bucket Vor- und Nach-Maßnahme.
def test_line_date_yields_the_full_day():
    assert tu.line_date(f"{STAMP}python3 .claude/scripts/vitest-run.py") == "2026-07-15"


def test_line_date_is_none_without_a_timestamp():
    assert tu.line_date("    --filter Foo | head -3") is None


def test_since_skips_earlier_runs(tmp_path):
    log = tmp_path / "allowed-commands.log"
    log.write_text(
        "[2026-07-28 09:00:00] python3 .claude/scripts/vitest-run.py | tail -3\n"
        "[2026-07-30 09:00:00] python3 .claude/scripts/vitest-run.py | tail -3\n"
        "[2026-08-01 09:00:00] python3 .claude/scripts/qa-check.py\n",
        encoding="utf-8",
    )
    runs, filtered, _, _ = tu.measure_filter_quote(log, since="2026-07-30")
    assert sum(runs.values()) == 2
    assert sum(filtered.values()) == 1


def test_since_includes_the_stichtag_itself(tmp_path):
    """Inklusiv – sonst fiele der Stichtag selbst aus beiden Fenstern heraus."""
    log = tmp_path / "allowed-commands.log"
    log.write_text("[2026-07-30 09:00:00] python3 .claude/scripts/vitest-run.py\n", encoding="utf-8")
    runs, _, _, _ = tu.measure_filter_quote(log, since="2026-07-30")
    assert sum(runs.values()) == 1
