"""Tests für dotnet-test.py – Coverage-Erhebung unter coverlet.MTP (TD-S089-1, ADR-S089-1).

Zwei Eigenschaften tragen das Gate: Die Ausschlüsse sind dieselben wie bei Stryker (eine Quelle,
nicht zwei Listen), und ein Report zählt nur, wenn er eindeutig aus diesem Lauf stammt –
coverlet.MTP hängt einen Zeitstempel an den Dateinamen, ein fester Pfad ist nicht vorgebbar.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from importlib import import_module
from pathlib import Path

import pytest

from conftest import cli_aufruf

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


# Echte Ausgabe (S141, gekürzt auf das Ende): alle Tests grün, danach stürzt der Test-Host beim
# Entladen ab – coverlet.MTP legt einen benannten Mutex an, .NET sucht ihn unter einem
# XDG_RUNTIME_DIR, das es nicht gibt. Exit 7, kein `failed …`-Block.
MTP_HOST_CRASH = """\
  info: Microsoft.Hosting.Lifetime[0]
        Application is shutting down...
  Error output: Unhandled exception. System.IO.IOException: The system cannot open the device or file specified. : 'mahl_Mutex'. One or more system calls failed: lstat("/run/user/1000", ...) == -1; errno == ENOENT;
     at System.Threading.Mutex.CreateMutexCore(Boolean initiallyOwned, String name, NamedWaitHandleOptionsInternal options, Boolean& createdNew)
     at Coverlet.Core.Instrumentation.Tracker.mahl.Server_22aa6570-671a-4caf-8865-fd03680dad5c.UnloadModule(Object, EventArgs)

        Failed executing DbCommand (1ms) [Parameters=[@p0='?' (DbType = Guid)], CommandType='Text']
Test run summary: Failed!
  error: 1

  total: 57
  failed: 0
  succeeded: 57
  skipped: 0
  duration: 9s 164ms
Test run completed with non-success exit code: 7 (see: https://aka.ms/testingplatform/exitcodes)
"""


def test_host_error_report_names_the_crash_after_green_tests():
    """Ohne diesen Bericht fiel der Wrapper auf den Rohfilter zurück und zeigte nur die
    `Failed executing DbCommand`-Logzeilen – die Ursache stand nirgends (S141)."""
    report = dt.host_error_report(MTP_HOST_CRASH)

    assert report.startswith("✗ Test-Host-Fehler – 57 von 57 Backend-Tests grün")
    assert "lstat(\"/run/user/1000\", ...) == -1; errno == ENOENT" in report
    assert "Coverlet.Core.Instrumentation.Tracker" in report
    assert "DbCommand" not in report


def test_cli_shows_the_host_error_instead_of_log_lines(monkeypatch, capsys):
    """Über den Aufrufpfad: Der Bericht muss im Wrapper ankommen, nicht nur existieren."""
    monkeypatch.setattr(dt, "run_dotnet", lambda _argumente: (MTP_HOST_CRASH, 7))
    monkeypatch.setattr(sys, "argv", ["dotnet-test", "--filter", "X"])
    with pytest.raises(SystemExit) as beendet:
        dt.main()

    ausgabe = capsys.readouterr().out
    assert beendet.value.code == 7
    assert "Test-Host-Fehler" in ausgabe
    assert "DbCommand" not in ausgabe


def test_host_error_report_is_none_without_error_output():
    assert dt.host_error_report(MTP_FAILED) is None
    assert dt.host_error_report(MTP_SUMMARY) is None


def test_runtime_dir_that_does_not_exist_is_dropped_for_the_test_host(monkeypatch, tmp_path: Path):
    """Ein XDG_RUNTIME_DIR ohne Verzeichnis (WSL ohne User-Session) lässt den Test-Host nach dem
    letzten Test abstürzen; ohne die Variable weicht .NET auf sein Standardverzeichnis aus."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "fehlt"))
    gesehen = _cli_env_beim_lauf(monkeypatch)

    assert "XDG_RUNTIME_DIR" not in gesehen


def test_existing_runtime_dir_is_kept(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    gesehen = _cli_env_beim_lauf(monkeypatch)

    assert gesehen["XDG_RUNTIME_DIR"] == str(tmp_path)


def _cli_env_beim_lauf(monkeypatch) -> dict[str, str]:
    """Startet den Wrapper über seinen Aufrufpfad (gefiltert, ohne Coverage) und liefert die
    Umgebung, die der dotnet-Prozess zu sehen bekäme."""
    gesehen: dict[str, str] = {}

    def fake_run(_argumente):
        gesehen.update(os.environ)
        return MTP_SUMMARY, 0

    monkeypatch.setattr(dt, "run_dotnet", fake_run)
    monkeypatch.setattr(sys, "argv", ["dotnet-test", "--filter", "X"])
    with pytest.raises(SystemExit):
        dt.main()
    return gesehen


def _option_values(args: list[str], option: str) -> list[str]:
    return [args[i + 1] for i, arg in enumerate(args) if arg == option]


# --- Berichte: wörtlich, weil der Bericht die ganze Diagnose eines roten Laufs ist ----------
def test_failure_report_ist_kopf_plus_bereinigter_block():
    assert dt.failure_report(MTP_FAILED) == (
        "✗ 1 von 56 Backend-Tests rot\n"
        "\n"
        'failed mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Restore(requestName: "Koriander") (33ms)\n'
        "  Expected body.Ingredient.BaseUnit to be the same string, but they differ at index 0:\n"
        "     ↓ (actual)\n"
        '    "Töpfchen"\n'
        '    "GEGENPROBE"\n'
        "     ↑ (expected).\n"
        "    at mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Restore(String requestName)"
        " in /repo/Server.Tests/IngredientsEndpointsTests.cs:915"
    )


def test_failure_report_trennt_mehrere_bloecke_durch_leerzeile():
    """Aus der echten Ausgabe abgeleitet: ein zweiter roter Test mit eigenem Block."""
    zweiter = (
        "failed mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Delete (12ms)\n"
        "  from /repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll (net10.0|x64)\n"
        "  Expected response.StatusCode to be 204, but found 404.\n"
    )
    ausgabe = MTP_FAILED.replace("/repo/Server.Tests/bin/Debug/net10.0/mahl.Server.Tests.dll "
                                 "(net10.0|x64) failed", zweiter + "/repo/x failed")

    bericht = dt.failure_report(ausgabe)

    assert bericht.endswith(
        "IngredientsEndpointsTests.cs:915\n"
        "\n"
        "failed mahl.Server.Tests.IngredientsEndpointsTests.US904_Error_Delete (12ms)\n"
        "  Expected response.StatusCode to be 204, but found 404.")


def test_failure_report_ohne_zusammenfassung_nennt_keine_zahlen():
    """Abgeschnittene Ausgabe: der Block ist da, die Summary nicht."""
    ohne_summary = MTP_FAILED.split("Test run summary")[0]

    assert dt.failure_report(ohne_summary).startswith("✗ Backend-Tests rot\n\nfailed mahl.")


def test_host_error_report_wortlaut():
    assert dt.host_error_report(MTP_HOST_CRASH) == (
        "✗ Test-Host-Fehler – 57 von 57 Backend-Tests grün, der Lauf trotzdem rot\n"
        "Error output: Unhandled exception. System.IO.IOException: The system cannot open the"
        " device or file specified. : 'mahl_Mutex'. One or more system calls failed:"
        ' lstat("/run/user/1000", ...) == -1; errno == ENOENT;\n'
        "  at System.Threading.Mutex.CreateMutexCore(Boolean initiallyOwned, String name,"
        " NamedWaitHandleOptionsInternal options, Boolean& createdNew)\n"
        "  at Coverlet.Core.Instrumentation.Tracker.mahl.Server_22aa6570-671a-4caf-8865-fd03680dad5c"
        ".UnloadModule(Object, EventArgs)\n"
        "   Vollständige Ausgabe: python3 -m prozesscode.dotnet-test --verbose"
    )


def test_host_error_report_ohne_zusammenfassung_zeigt_fragezeichen():
    ohne_summary = MTP_HOST_CRASH.split("Test run summary")[0]

    assert dt.host_error_report(ohne_summary).startswith(
        "✗ Test-Host-Fehler – ? von ? Backend-Tests grün, der Lauf trotzdem rot\n")


# --- Aufrufpfad: gefilterter Lauf (ohne Coverage) -------------------------------------------
# Echte Ausgabe eines Build-Fehlers im MTP-Modus (Session-Protokoll, Oktober 2026).
MTP_BUILD_FEHLER = (
    "/home/kieritz/repos/mahl/Server.Tests/Helpers/EndpointsTestsBase.cs(13,13): error CS0246:"
    " The type or namespace name 'IServiceScope' could not be found (are you missing a using"
    " directive or an assembly reference?)"
    " [/home/kieritz/repos/mahl/Server.Tests/mahl.Server.Tests.csproj]\n"
    "Build failed with exit code: 1.\n"
)


def _gefiltert(monkeypatch, ausgabe: str, exit_code: int, *weitere: str) -> int:
    monkeypatch.setattr(dt, "run_dotnet", lambda _argumente: (ausgabe, exit_code))
    return cli_aufruf(monkeypatch, dt, "--filter", "X", *weitere)


@pytest.mark.aufrufpfad("dotnet-test")
def test_gruener_gefilterter_lauf_zeigt_nur_das_verdikt(monkeypatch, capsys):
    monkeypatch.setattr(dt, "run_dotnet", lambda _argumente: (MTP_SUMMARY, 0))

    code = cli_aufruf(monkeypatch, dt, "--filter", "X")

    assert code == 0
    assert capsys.readouterr().out == "✓ 53 Backend-Tests grün, 9s 381ms\n"


def test_roter_gefilterter_lauf_zeigt_den_bericht(monkeypatch, capsys):
    code = _gefiltert(monkeypatch, MTP_FAILED, 1)

    assert code == 1
    assert capsys.readouterr().out == dt.failure_report(MTP_FAILED) + "\n"


def test_verbose_zeigt_die_ganze_ausgabe_statt_des_verdikts(monkeypatch, capsys):
    code = _gefiltert(monkeypatch, MTP_SUMMARY, 0, "--verbose")

    assert code == 0
    assert capsys.readouterr().out == MTP_SUMMARY + "\n"


def test_build_fehler_ohne_bekanntes_muster_zeigt_die_ganze_ausgabe(monkeypatch, capsys):
    """Fail-open: MTP meldet den Build-Fehler als `Build failed with exit code` – das trifft
    keines der Muster, also erscheint alles statt nichts."""
    code = _gefiltert(monkeypatch, MTP_BUILD_FEHLER, 1)

    assert code == 1
    assert capsys.readouterr().out == MTP_BUILD_FEHLER + "\n"


def test_unbekannter_absturz_faellt_auf_die_relevanten_zeilen_zurueck(monkeypatch, capsys):
    """Abgeleitet aus dem echten Host-Absturz, ohne den `Error output:`-Block, den der Bericht
    braucht – so sah die Ausgabe vor dem Host-Fehler-Bericht aus: nur die Logzeilen."""
    log = "        Failed executing DbCommand (1ms) [Parameters=[@p0='?' (DbType = Guid)], CommandType='Text']"
    zeilen = [z for z in MTP_HOST_CRASH.splitlines() if "Error output:" not in z and " at " not in z]
    ausgabe = "\n".join(zeilen).replace(log, log + "\n" + log)

    code = _gefiltert(monkeypatch, ausgabe, 7)

    assert code == 7
    assert capsys.readouterr().out == log + "\n" + log + "\n"


# --- Aufrufpfad: voller Lauf mit Coverage-Gate ----------------------------------------------
_COBERTURA = Path(__file__).parent / "fixtures" / "dotnet_test_cobertura.xml"
_SEP = "─" * 60


class DotnetAttrappe:
    """Ersetzt `dotnet test`: legt wie coverlet.MTP einen Report mit Zeitstempel-Namen ins
    Ergebnisverzeichnis – auch bei roten Tests, coverlet schreibt beim Entladen."""

    def __init__(self, ergebnisse: Path):
        self.ergebnisse = ergebnisse
        self.aufrufe: list[list[str]] = []
        self.ausgabe = MTP_SUMMARY
        self.exit_code = 0
        self.report: str | None = _COBERTURA.read_text(encoding="utf-8")

    def __call__(self, argumente):
        self.aufrufe.append(argumente)
        if self.report is not None:
            ziel = self.ergebnisse / "coverage.cobertura.051126073836430.xml"
            ziel.write_text(self.report, encoding="utf-8")
        return self.ausgabe, self.exit_code


@pytest.fixture
def dotnet(tmp_path, monkeypatch) -> DotnetAttrappe:
    """Frischer Klon: TestResults/ fehlt noch."""
    ergebnisse = tmp_path / "TestResults" / "coverage"
    konfiguration = tmp_path / "stryker-config.json"
    konfiguration.write_text(json.dumps(STRYKER), encoding="utf-8")
    monkeypatch.setattr(dt, "_RESULTS_DIR", ergebnisse)
    monkeypatch.setattr(dt, "_STRYKER_CONFIG", konfiguration)
    attrappe = DotnetAttrappe(ergebnisse)
    monkeypatch.setattr(dt, "run_dotnet", attrappe)
    return attrappe


def _report_ohne_gesamtraten() -> str:
    wurzel = ET.parse(_COBERTURA).getroot()
    del wurzel.attrib["line-rate"], wurzel.attrib["branch-rate"]
    return ET.tostring(wurzel, encoding="unicode")


def _report_mit_luecken() -> str:
    """Der echte Report, umgebaut auf einen Lauf mit Lücken in drei Dateien: Uuid7.Create und
    XminETag.TryParse nie gerufen; in ApplyETagAndWriteAsync der letzte Zweig nie erreicht.
    InterceptGetAsync trägt keine Zeilen – die Form, die der Parser für compiler-generierte
    Klassen abfängt (im aktuellen coverlet.MTP-Report nicht beobachtet)."""
    wurzel = ET.parse(_COBERTURA).getroot()
    wurzel.set("line-rate", "0.9836")
    wurzel.set("branch-rate", "0.9412")
    klassen = {k.get("name").rsplit(".", 1)[-1]: k for k in wurzel.iter("class")}

    def ungerufen(klasse: str, *nummern: int) -> None:
        for zeile in klassen[klasse].iter("line"):
            if int(zeile.get("number")) in nummern:
                zeile.set("hits", "0")

    klassen["Uuid7"].set("line-rate", "0.6666")
    ungerufen("Uuid7", 38)
    klassen["XminETag"].set("line-rate", "0.5")
    ungerufen("XminETag", 20)
    anwenden = klassen["ETagMiddleware/<ApplyETagAndWriteAsync>d__2"]
    anwenden.set("branch-rate", "0.6666")
    anwenden.set("line-rate", "0.7368")
    ungerufen("ETagMiddleware/<ApplyETagAndWriteAsync>d__2", 45, 46, 47, 50, 51)
    for zeile in anwenden.iter("line"):
        if zeile.get("number") == "45":
            zeile.set("condition-coverage", "0% (0/2)")
            zeile.find("conditions/condition").set("coverage", "0%")
    abfangen = klassen["ETagMiddleware/<InterceptGetAsync>d__1"]
    abfangen.set("branch-rate", "0.5")
    for zeilen in abfangen.iter("lines"):
        for zeile in list(zeilen):
            zeilen.remove(zeile)
    return ET.tostring(wurzel, encoding="unicode")


@pytest.mark.aufrufpfad("dotnet-test")
def test_voller_lauf_misst_coverage_mit_den_stryker_ausschluessen(dotnet, monkeypatch):
    cli_aufruf(monkeypatch, dt)

    assert dotnet.aufrufe == [
        ["test", "--project", "Server.Tests/mahl.Server.Tests.csproj",
         *dt.coverage_args(STRYKER, dotnet.ergebnisse)]]


def test_voller_gruener_lauf_mit_voller_coverage_ist_gruen(dotnet, monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, dt)

    ausgabe = capsys.readouterr()
    assert code == 0
    assert ausgabe.out == (
        "✓ 53 Backend-Tests grün, 9s 381ms\n"
        f"\n{_SEP}\n"
        "  Branch Coverage\n"
        f"{_SEP}\n"
        "  Branch   100.00%  ✓\n"
        "  Line     100.00%  ✓\n"
        f"{_SEP}\n"
    )
    assert ausgabe.err == ""


def test_coverage_luecken_machen_den_lauf_rot_und_nennen_datei_und_zeile(
        dotnet, monkeypatch, capsys):
    """Dateien aufsteigend nach Branch-Rate, Gleichstand in Report-Reihenfolge; die Klassen
    einer Datei zusammengefasst mit der jeweils schlechtesten Rate; Zeilen aufsteigend."""
    dotnet.report = _report_mit_luecken()

    code = cli_aufruf(monkeypatch, dt)

    nicht_ausgefuehrt = "nicht ausgeführt (0 hits)"
    assert code == 1
    assert capsys.readouterr().out == (
        "✓ 53 Backend-Tests grün, 9s 381ms\n"
        f"\n{_SEP}\n"
        "  Branch Coverage\n"
        f"{_SEP}\n"
        "  Branch    94.12%  ✗  (threshold: 100%)\n"
        "  Line      98.36%  ✗  (threshold: 100%)\n"
        "\n"
        "  Datei" + " " * 43 + "  Branch    Line\n"
        "  " + "─" * 48 + "  ──────  ──────\n"
        "  Middleware/ETagMiddleware.cs" + " " * 20 + "   50.0%   73.7%\n"
        "      → kein Zeilen-Detail (compiler-generiert: <InterceptGetAsync>d__1)\n"
        "      Zeile  45: branch condition 0%\n"
        f"      Zeile  46: {nicht_ausgefuehrt}\n"
        f"      Zeile  47: {nicht_ausgefuehrt}\n"
        f"      Zeile  50: {nicht_ausgefuehrt}\n"
        f"      Zeile  51: {nicht_ausgefuehrt}\n"
        "  Types/Uuid7.cs" + " " * 34 + "  100.0%   66.7%\n"
        f"      Zeile  38: {nicht_ausgefuehrt}\n"
        "  Middleware/XminETag.cs" + " " * 26 + "  100.0%   50.0%\n"
        f"      Zeile  20: {nicht_ausgefuehrt}\n"
        f"{_SEP}\n"
    )


def test_report_ohne_gesamtraten_laesst_das_gate_fallen(dotnet, monkeypatch, capsys):
    """Fail-closed: Ein Report, dem die Raten fehlen, besteht nicht – und stürzt nicht ab."""
    dotnet.report = _report_ohne_gesamtraten()

    code = cli_aufruf(monkeypatch, dt)

    zeilen = capsys.readouterr().out.splitlines()
    assert code == 1
    assert "  Branch     0.00%  ✗  (threshold: 100%)" in zeilen
    assert "  Line       0.00%  ✗  (threshold: 100%)" in zeilen


def test_gruene_tests_ohne_report_sind_fail_closed(dotnet, monkeypatch, capsys):
    dotnet.report = None

    code = cli_aufruf(monkeypatch, dt)

    assert code == 1
    assert capsys.readouterr().err == (
        f"\n[coverage] FEHLER: nicht genau ein cobertura-Report in {dotnet.ergebnisse}"
        " → Gate fail-closed.\n"
        "   Prüfen: ist coverlet.MTP im Testprojekt referenziert (ADR-S089-1)? Details: --verbose\n"
    )


def test_liegengebliebener_report_wird_vor_dem_lauf_entfernt(dotnet, monkeypatch):
    """Sonst lägen danach zwei Reports im Verzeichnis – das Gate fiele, obwohl alles grün ist."""
    dotnet.ergebnisse.mkdir(parents=True)
    (dotnet.ergebnisse / "coverage.cobertura.010126000000000.xml").write_text("<coverage/>")

    assert cli_aufruf(monkeypatch, dt) == 0


def test_rote_tests_enden_mit_deren_exit_code_ohne_coverage_auswertung(
        dotnet, monkeypatch, capsys):
    """Coverage eines roten Laufs ist bedeutungslos – auch wenn coverlet einen Report schrieb."""
    dotnet.ausgabe = MTP_FAILED
    dotnet.exit_code = 1

    code = cli_aufruf(monkeypatch, dt)

    ausgabe = capsys.readouterr()
    assert code == 1
    assert ausgabe.out == dt.failure_report(MTP_FAILED) + "\n"
    assert ausgabe.err == ""


def test_host_absturz_im_vollen_lauf_behaelt_den_exit_code(dotnet, monkeypatch):
    dotnet.ausgabe = MTP_HOST_CRASH
    dotnet.exit_code = 7

    assert cli_aufruf(monkeypatch, dt) == 7


# --- Einzelteile ohne Weg über den echten Report ---------------------------------------------
@pytest.mark.parametrize(("dateiname", "erwartet"), [
    ("/home/u/repos/mahl/Server/Endpoints/Foo.cs", "Server/Endpoints/Foo.cs"),
    ("C:\\repos\\mahl\\Server\\Endpoints\\Foo.cs", "Server\\Endpoints\\Foo.cs"),
    ("/home/u/repos/mahl/Client/src/a.ts", "Client/src/a.ts"),
    ("Endpoints/Foo.cs", "Endpoints/Foo.cs"),  # coverlet.MTP schreibt relativ zu <source>
])
def test_shorten_kuerzt_absolute_pfade_auf_den_projektteil(dateiname, erwartet):
    assert dt._shorten(dateiname) == erwartet


def test_lange_dateinamen_werden_vorne_gekuerzt(capsys):
    """Die Spalte ist 48 Zeichen breit: genau 48 passen, ab 49 bleibt das Ende sichtbar."""
    name48 = "Endpoints/RecipeIngredientsQuantityValidation.cs"
    name49 = "Endpoints/RecipeIngredientsQuantityValidations.cs"

    dt._report_coverage({"Branch": 0.5}, [(name48, 0.5, 1.0, []), (name49, 1.0, 0.5, [])])

    zeilen = capsys.readouterr().out.splitlines()
    assert "  Endpoints/RecipeIngredientsQuantityValidation.cs   50.0%  100.0%" in zeilen
    assert "  …dpoints/RecipeIngredientsQuantityValidations.cs  100.0%   50.0%" in zeilen
