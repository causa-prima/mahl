"""Tests für .claude/scripts/qa-check.py – Standard-Score (inkl. NoCoverage) + Hash/Verify.

Designentscheidung (Stale-Schutz): --skip-stryker gibt KEINEN Übergabe-Hash aus. Damit ist
jeder existierende Hash per Konstruktion ein Frisch-Lauf-Hash; ein MODE-Feld im Hash ist unnötig.
`verify_hash` rechnet den kanonischen Hash aus dem aktuellen Report+Tree nach und vergleicht.
"""
import importlib.util
import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "qa-check.py")


def _load():
    spec = importlib.util.spec_from_file_location("qa_check", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


qa = _load()


def _write_report(tmp_path, *statuses):
    mutants = [{"id": str(i), "status": s} for i, s in enumerate(statuses)]
    report = {"files": {"Foo.tsx": {"mutants": mutants}}}
    p = tmp_path / "mutation-report.json"
    p.write_text(json.dumps(report), encoding="utf-8")
    return p


# --- Standard-Score (inkl. NoCoverage, Timeout als detected) ---

def test_all_killed_is_100(tmp_path):
    score, _ = qa._parse_report(_write_report(tmp_path, "Killed", "Killed"))
    assert score == "100.0%"


def test_nocoverage_lowers_score(tmp_path):
    score, _ = qa._parse_report(_write_report(tmp_path, "Killed", "NoCoverage"))
    assert score == "50.0%"


def test_timeout_counts_as_detected(tmp_path):
    score, _ = qa._parse_report(_write_report(tmp_path, "Killed", "Timeout"))
    assert score == "100.0%"


def test_ignored_excluded(tmp_path):
    score, _ = qa._parse_report(_write_report(tmp_path, "Killed", "Ignored"))
    assert score == "100.0%"


# --- Hash + Verify (Q2/Q3) ---

def _args():
    return dict(layer="frontend", tree="t", report_hash="r", test_files=[],
                suppressions=[], unit_tests=[], lint_code=0, test_structure=[], adr_code=0)


def test_compute_hash_deterministic():
    assert qa.compute_hash(**_args()) == qa.compute_hash(**_args())


def test_compute_hash_changes_with_input():
    other = _args()
    other["tree"] = "anderer-tree"
    assert qa.compute_hash(**_args()) != qa.compute_hash(**other)


def test_verify_accepts_matching_hash():
    h = qa.compute_hash(**_args())
    assert qa.verify_hash(h, **_args()) is True


def test_verify_rejects_mismatching_hash():
    h = qa.compute_hash(**_args())
    other = _args()
    other["tree"] = "veraenderter-code"
    assert qa.verify_hash(h, **other) is False
