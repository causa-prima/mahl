"""Tests für .claude/scripts/stryker-summary.py – Standard-Mutation-Score + Gate.

Der Score muss dem mutation-testing-elements-Standard entsprechen (wie im HTML-Report):
  detected   = Killed + Timeout
  undetected = Survived + NoCoverage
  score      = detected / (detected + undetected)
Ignored / CompileError / RuntimeError zählen nicht in den Nenner.
"""
import importlib.util
import os

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "stryker-summary.py")


def _load():
    spec = importlib.util.spec_from_file_location("stryker_summary", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ss = _load()


def _files(*statuses):
    return {"Foo.tsx": {"mutants": [{"status": s, "id": str(i)} for i, s in enumerate(statuses)]}}


def test_all_killed_is_100_and_passes():
    m = ss.compute_metrics(_files("Killed", "Killed"))
    assert m["score"] == 100.0
    assert m["undetected"] == 0


def test_nocoverage_lowers_score_below_100():
    # NoCoverage muss in den Nenner: 1 Killed + 1 NoCoverage = 50 %, nicht 100 %.
    m = ss.compute_metrics(_files("Killed", "NoCoverage"))
    assert m["score"] == 50.0
    assert m["undetected"] == 1


def test_survived_lowers_score():
    m = ss.compute_metrics(_files("Killed", "Survived"))
    assert m["score"] == 50.0
    assert m["undetected"] == 1


def test_timeout_counts_as_detected():
    # Timeout = detected (Standard): 1 Killed + 1 Timeout = 100 %.
    m = ss.compute_metrics(_files("Killed", "Timeout"))
    assert m["score"] == 100.0
    assert m["undetected"] == 0


def test_ignored_excluded_from_denominator():
    # Suppressed (Ignored) Mutanten zählen nicht: 1 Killed + 1 Ignored = 100 %.
    m = ss.compute_metrics(_files("Killed", "Ignored"))
    assert m["score"] == 100.0
    assert m["total_valid"] == 1


def test_gate_passes_only_when_no_undetected():
    assert ss.gate_code(ss.compute_metrics(_files("Killed", "Killed"))) == 0
    assert ss.gate_code(ss.compute_metrics(_files("Killed", "Survived"))) == 1
    assert ss.gate_code(ss.compute_metrics(_files("Killed", "NoCoverage"))) == 1
