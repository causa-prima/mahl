"""Tests für dotnet-test.py – Coverage-Erhebung unter coverlet.MTP (TD-S089-1, ADR-S089-1).

Zwei Eigenschaften tragen das Gate: Die Ausschlüsse sind dieselben wie bei Stryker (eine Quelle,
nicht zwei Listen), und ein Report zählt nur, wenn er eindeutig aus diesem Lauf stammt –
coverlet.MTP hängt einen Zeitstempel an den Dateinamen, ein fester Pfad ist nicht vorgebbar.
"""
from importlib import import_module
from pathlib import Path

dt = import_module("prozesscode.dotnet-test")

STRYKER = {
    "stryker-config": {
        "mutate": ["**/*.cs", "!**/Migrations/**", "!**/Program.cs"],
    }
}


def test_coverage_args_enable_cobertura_for_server_assembly(tmp_path: Path):
    args = dt.coverage_args(STRYKER, tmp_path)

    assert args[:3] == ["--coverlet", "--coverlet-output-format", "cobertura"]
    assert _option_values(args, "--coverlet-include") == ["[mahl.Server]*"]
    assert "--coverlet-skip-auto-props" in args
    assert _option_values(args, "--results-directory") == [str(tmp_path)]


def test_coverage_args_exclude_by_project_attribute_not_by_excludefromcodecoverage(tmp_path: Path):
    """Stryker.NET verwirft Mutanten in [ExcludeFromCodeCoverage]-Membern (S132 gemessen) – der
    Coverage-Ausschluss braucht deshalb ein eigenes Attribut, das Stryker nicht kennt (ADR-S041-9)."""
    args = dt.coverage_args(STRYKER, tmp_path)

    assert _option_values(args, "--coverlet-exclude-by-attribute") == ["ExcludeFromCoverageGate"]


def test_coverage_args_exclude_exactly_the_stryker_negations(tmp_path: Path):
    """Die positiven mutate-Globs sind keine Ausschlüsse – nur die `!`-Einträge, ohne `!`."""
    args = dt.coverage_args(STRYKER, tmp_path)

    assert _option_values(args, "--coverlet-exclude-by-file") == ["**/Migrations/**", "**/Program.cs"]


def test_find_report_returns_the_single_cobertura(tmp_path: Path):
    """Dateiname wie real von coverlet.MTP 10.0.1 erzeugt (S132) – das Doku-Beispiel weicht davon ab."""
    report = tmp_path / "coverage.cobertura.230926202510265.xml"
    report.write_text("<coverage/>")
    (tmp_path / "coverage.json.230926202510265.json").write_text("{}")

    assert dt.find_report(tmp_path) == report


def test_find_report_is_fail_closed_without_report(tmp_path: Path):
    assert dt.find_report(tmp_path) is None


def test_find_report_is_fail_closed_with_ambiguous_reports(tmp_path: Path):
    """Zwei Reports heißt: mindestens einer ist nicht aus diesem Lauf (Stale-Masking, TD-S089-1)."""
    (tmp_path / "coverage.cobertura.1.xml").write_text("<coverage/>")
    (tmp_path / "coverage.cobertura.2.xml").write_text("<coverage/>")

    assert dt.find_report(tmp_path) is None


def test_clear_results_removes_old_reports(tmp_path: Path):
    results = tmp_path / "coverage"
    results.mkdir()
    (results / "coverage.cobertura.old.xml").write_text("<coverage/>")

    dt.clear_results(results)

    assert dt.find_report(results) is None
    assert results.is_dir()


MTP_SUMMARY = """\
warning MSB3277: Found conflicts between different versions of "X"
Running tests from /repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll (net10.0|x64)

Test run summary: Passed!
  total: 53
  failed: 0
  succeeded: 53
  skipped: 0
  duration: 9s 381ms
"""


def test_verdict_condenses_a_passed_mtp_run_to_one_line():
    """Ausgabeformat des MTP-Modus von `dotnet test`, real beobachtet (S132)."""
    assert dt.verdict(MTP_SUMMARY) == "✓ 53 Backend-Tests grün, 9s 381ms"


def test_verdict_is_none_for_a_failed_run():
    """Rot braucht die Details, nicht eine Zeile – der Aufrufer zeigt dann den Output."""
    failed = MTP_SUMMARY.replace("Passed!", "Failed!").replace("failed: 0", "failed: 1")

    assert dt.verdict(failed) is None


MTP_FAILED = """\
Running tests from /repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll (net10.0|x64)
failed mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Restore(requestName: "Koriander") (33ms)
  from /repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll (net10.0|x64)
  Expected body.Ingredient.BaseUnit to be the same string, but they differ at index 0:
     ↓ (actual)
    "Töpfchen"
    "GEGENPROBE"
     ↑ (expected).
    at AwesomeAssertions.Execution.LateBoundTestFramework.Throw(String message)
    at mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Restore(String requestName) in /repo/Server.Tests/IngredientsEndpointsTests.cs:915
    --- End of stack trace from previous location ---
/repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll (net10.0|x64) failed with 1 error(s) (8s 406ms)
        Failed executing DbCommand (1ms) [Parameters=[@p0='?' (DbType = Guid)], CommandType='Text']

Test run summary: Failed!
  total: 56
  failed: 1
  succeeded: 55
"""


def test_failure_report_shows_message_and_source_frame_of_each_failed_test():
    """Ausgabeformat eines roten Laufs im MTP-Modus, real beobachtet (S132): die Details stehen
    direkt auf stdout, nicht mehr in einer Log-Datei."""
    report = dt.failure_report(MTP_FAILED)

    assert "failed mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Restore" in report
    assert "Expected body.Ingredient.BaseUnit to be the same string" in report
    assert '"GEGENPROBE"' in report
    assert "IngredientsEndpointsTests.cs:915" in report
    assert "✗ 1 von 56 Backend-Tests rot" in report


def test_failure_report_drops_framework_frames_and_log_noise():
    report = dt.failure_report(MTP_FAILED)

    assert "AwesomeAssertions" not in report
    assert "End of stack trace" not in report
    assert "from /repo" not in report
    assert "DbCommand" not in report


def test_failure_report_is_none_without_failed_tests():
    """Kein Testblock (z.B. Build-Fehler) → der Aufrufer fällt auf den Rohfilter zurück."""
    assert dt.failure_report("Build FAILED.\nerror CS1002: ; expected") is None


def _option_values(args: list[str], option: str) -> list[str]:
    return [args[i + 1] for i, arg in enumerate(args) if arg == option]
