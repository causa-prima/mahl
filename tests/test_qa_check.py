"""Tests für prozesscode/qa-check.py – Standard-Score (inkl. NoCoverage) + Hash/Verify.

Designentscheidung (Stale-Schutz): --skip-stryker gibt KEINEN Übergabe-Hash aus. Damit ist
jeder existierende Hash per Konstruktion ein Frisch-Lauf-Hash; ein MODE-Feld im Hash ist unnötig.
`verify_hash` rechnet den kanonischen Hash aus dem aktuellen Report+Tree nach und vergleicht.
"""
import json
import os
import subprocess
import time
from importlib import import_module

import pytest


def _load():
    return import_module("prozesscode.qa-check")


qa = _load()


def _write_report(tmp_path, *statuses):
    mutants = [{"id": str(i), "status": s} for i, s in enumerate(statuses)]
    report = {"files": {"Foo.tsx": {"mutants": mutants}}}
    p = tmp_path / "mutation-report.json"
    p.write_text(json.dumps(report), encoding="utf-8")
    return p


# --- Standard-Score (inkl. NoCoverage, Timeout als detected) ---

def _score(tmp_path, *statuses) -> float | None:
    """Score des Reports. `_parse_report` liefert (files, metrics, hash);
    der Score ist ein float in `metrics`, nicht mehr ein formatierter String."""
    _, metrics, _ = qa._parse_report(_write_report(tmp_path, *statuses))
    return metrics["score"]


def test_all_killed_is_100(tmp_path):
    assert _score(tmp_path, "Killed", "Killed") == 100.0


def test_nocoverage_lowers_score(tmp_path):
    assert _score(tmp_path, "Killed", "NoCoverage") == 50.0


def test_timeout_counts_as_detected(tmp_path):
    assert _score(tmp_path, "Killed", "Timeout") == 100.0


def test_ignored_excluded(tmp_path):
    # Ignored ist kein valider Mutant und darf den Nenner nicht vergrößern.
    assert _score(tmp_path, "Killed", "Ignored") == 100.0


# --- Lauf ohne validen Mutanten: kein definierter Score (OBS-S108-3) ---
# Der gefährliche Fehlerfall ist nicht „falscher Score", sondern ein leerer Lauf,
# der als 100 % durchgeht und damit ein grünes Gate vortäuscht.

def test_no_mutants_at_all_has_no_score(tmp_path):
    assert _score(tmp_path) is None


def test_only_ignored_mutants_has_no_score(tmp_path):
    # Alle Mutanten in einem Nicht-Bewertungs-Bucket: Nenner 0, nicht 100 %.
    assert _score(tmp_path, "Ignored", "Ignored") is None


def test_compile_error_only_has_no_score(tmp_path):
    assert _score(tmp_path, "CompileError") is None


def test_all_survived_scores_zero_and_is_not_confused_with_empty(tmp_path):
    # Grenze gegen die Tests oben: „alles überlebt" ist ein definierter Score (0.0),
    # kein leerer Lauf. Ohne diesen Fall bliebe offen, ob None nur der generische
    # Rückgabewert für „ungünstiger Report" ist.
    assert _score(tmp_path, "Survived", "Survived") == 0.0


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


# --- Frische-Schutz (Build-/Lock-Fehler darf keinen alten Report durchwinken) ---

def test_fresh_report_accepted(tmp_path):
    # // Given ein Report, der nach dem Lauf-Start geschrieben wurde
    run_started = time.time()
    report = _write_report(tmp_path, "Killed")
    os.utime(report, (run_started + 1, run_started + 1))
    # // When / // Then er gilt als frisch
    assert qa._is_fresh(report, run_started) is True


def test_stale_report_rejected(tmp_path):
    # // Given ein Report, der lange VOR dem Lauf-Start geschrieben wurde (alter Lauf)
    run_started = time.time()
    report = _write_report(tmp_path, "Killed")
    old = run_started - qa._FRESHNESS_SLACK_SECONDS - 60
    os.utime(report, (old, old))
    # // When / // Then er gilt NICHT als frisch → kein stiller Fallback
    assert qa._is_fresh(report, run_started) is False


def test_missing_report_not_fresh(tmp_path):
    # // Given ein nicht existierender Report-Pfad
    missing = tmp_path / "does-not-exist.json"
    # // When / // Then _is_fresh meldet False statt zu werfen
    assert qa._is_fresh(missing, time.time()) is False


# --- Working-Tree-Content-Hash (index-unabhängig, Subagent muss nicht stagen) ---

def _init_repo(path):
    """Legt ein leeres git-Repo in path an und gibt eine git-Aufruf-Closure zurück."""
    def g(*a):
        return subprocess.run(["git"] + list(a), cwd=path, capture_output=True, text=True)
    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    return g


def _write(path, rel, content):
    fp = path / rel
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    return fp


def test_content_fingerprint_invariant_under_staging(tmp_path, monkeypatch):
    # // Given ein modifizierter (tracked) + ein neuer (untracked) Working-Tree-Zustand
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/tracked.ts", "a\nb\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/tracked.ts", "a\nCHANGED\nb\n")
    _write(tmp_path, "Client/src/new.spec.ts", "it('x', () => {})\n")
    monkeypatch.chdir(tmp_path)
    # // When der Fingerprint vor und nach `git add` berechnet wird
    before = qa._worktree_content_fingerprint("frontend")
    g("add", ".")
    after = qa._worktree_content_fingerprint("frontend")
    # // Then ist er identisch – Stagen ändert den Content-Hash nicht (OBS-S090-2)
    assert before == after


def test_content_fingerprint_changes_with_content(tmp_path, monkeypatch):
    # // Given ein committeter Ausgangszustand
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/f.ts", "a\n")
    g("add", ".")
    g("commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    # // When zwei verschiedene Working-Tree-Inhalte
    _write(tmp_path, "Client/src/f.ts", "a\nb\n")
    h1 = qa._worktree_content_fingerprint("frontend")
    _write(tmp_path, "Client/src/f.ts", "a\nb\nc\n")
    h2 = qa._worktree_content_fingerprint("frontend")
    # // Then unterscheidet sich der Fingerprint
    assert h1 != h2


def test_content_fingerprint_layer_scoped(tmp_path, monkeypatch):
    # // Given eine Änderung außerhalb des Layer-Präfixes
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/f.ts", "a\n")
    _write(tmp_path, "Server/x.cs", "// c\n")
    g("add", ".")
    g("commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    base = qa._worktree_content_fingerprint("frontend")
    # // When nur eine Server-Datei geändert wird
    _write(tmp_path, "Server/x.cs", "// changed\n")
    # // Then bleibt der Frontend-Fingerprint gleich (layer-scoped)
    assert qa._worktree_content_fingerprint("frontend") == base


def test_worktree_diff_untracked_and_invariant(tmp_path, monkeypatch):
    # // Given eine tracked-Modifikation und eine neue untracked-Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/tracked.ts", "a\nb\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/tracked.ts", "a\nMODLINE\nb\n")
    _write(tmp_path, "Client/src/new.ts", "NEWLINE\n")
    monkeypatch.chdir(tmp_path)
    # // When der Working-Tree-Diff vor und nach `git add` erzeugt wird
    before = qa._worktree_diff(("Client/src/",), 0)
    g("add", ".")
    after = qa._worktree_diff(("Client/src/",), 0)
    # // Then erfasst er sowohl untracked als auch modifizierte Zeilen und ist index-unabhängig
    assert "NEWLINE" in before
    assert "MODLINE" in before
    assert before == after


def test_check_changed_test_files_lists_untracked(tmp_path, monkeypatch):
    # // Given eine neue, NICHT gestagte Test-Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/foo.spec.ts", "it('x', () => {})\n")
    monkeypatch.chdir(tmp_path)
    # // When / // Then wird sie ohne Stagen als geänderte Test-Datei gelistet
    assert "Client/src/foo.spec.ts" in qa.check_changed_test_files("frontend")


def test_check_new_suppressions_in_untracked(tmp_path, monkeypatch):
    # // Given eine Suppression in einer neuen, ungestageten Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/new.ts", "// Stryker disable next-line\nconst a = 1\n")
    monkeypatch.chdir(tmp_path)
    # // When / // Then wird die Suppression auch ohne Stagen erkannt
    found = qa.check_new_suppressions("frontend")
    assert any("Stryker disable" in line for _, line in found)


# --- Test-Struktur (Given/When/Then, Pflicht laut CGC-/CGT-given-when-then) ---

_UNSTRUCTURED_FACT = (
    "public class FooTests {\n"
    "    [Fact]\n"
    "    public async Task Foo_Bar_Baz()\n"
    "    {\n"
    "        // When: abgerufen\n"
    "        var x = 1;\n"
    "        // Then: 1\n"
    "        x.Should().Be(1);\n"
    "    }\n"
    "}\n"
)


def _repo_with_new_backend_test(tmp_path, monkeypatch, content):
    g = _init_repo(tmp_path)
    _write(tmp_path, "Server/app.cs", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Server.Tests/FooTests.cs", content)
    monkeypatch.chdir(tmp_path)


def test_check_test_structure_flags_new_test_without_given(tmp_path, monkeypatch):
    # // Given ein neuer Backend-Test ohne // Given
    _repo_with_new_backend_test(tmp_path, monkeypatch, _UNSTRUCTURED_FACT)
    # // When die Struktur geprüft wird
    findings = qa.check_test_structure("backend")
    # // Then nennt der Befund Datei und fehlendes Stück
    assert findings == [("Server.Tests/FooTests.cs", "[Fact]  →  fehlt: // Given")]


def test_check_test_structure_accepts_structured_test(tmp_path, monkeypatch):
    # // Given ein neuer Backend-Test mit Given-, When- und Then-Kommentar
    _repo_with_new_backend_test(tmp_path, monkeypatch,
                                _UNSTRUCTURED_FACT.replace("// When", "// Given: nichts\n        // When"))
    # // When / // Then kein Befund
    assert qa.check_test_structure("backend") == []


def test_structure_fast_fail_reports_before_stryker(tmp_path, monkeypatch):
    # // Given ein neuer Test ohne // Given – S142: der Befund kam erst nach dem minutenlangen Stryker-Lauf
    _repo_with_new_backend_test(tmp_path, monkeypatch, _UNSTRUCTURED_FACT)
    # // When der Fast-Fail vor Stryker prüft
    message = qa.structure_fast_fail("backend")
    # // Then nennt die Meldung den Befund und dass Stryker deshalb nicht lief
    assert message is not None
    assert "Server.Tests/FooTests.cs" in message and "fehlt: // Given" in message
    assert "vor Stryker" in message


def test_structure_fast_fail_is_silent_for_structured_tests(tmp_path, monkeypatch):
    # // Given ein vollständig strukturierter neuer Test
    _repo_with_new_backend_test(tmp_path, monkeypatch,
                                _UNSTRUCTURED_FACT.replace("// When", "// Given: nichts\n        // When"))
    # // When / // Then kein Abbruch
    assert qa.structure_fast_fail("backend") is None


# --- Test-Freigabe-Audit (OBS-S090-4: nur erlaubte Änderungen nach Freigabe) ---

def _hash_object(path, rel):
    return subprocess.run(["git", "hash-object", "-w", rel], cwd=path,
                          capture_output=True, text=True).stdout.strip()


def test_audit_approved_tests_unchanged(tmp_path, monkeypatch):
    # // Given eine freigegebene, seither unveränderte Test-Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/foo.spec.ts", "it('a', () => {})\n")
    monkeypatch.chdir(tmp_path)
    sha = _hash_object(tmp_path, "Client/src/foo.spec.ts")
    # // When gegen die Freigabe-SHA geprüft wird
    findings, _ = qa.audit_approved_tests("frontend", {"Client/src/foo.spec.ts": sha})
    # // Then keine Auffälligkeit
    assert findings == 0


def test_audit_approved_tests_shows_what_changed(tmp_path, monkeypatch):
    # // Given eine freigegebene Test-Datei, deren Assertion danach geändert wurde
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/foo.spec.ts", "it('a', () => { expect(x).toBe(1) })\n")
    monkeypatch.chdir(tmp_path)
    sha = _hash_object(tmp_path, "Client/src/foo.spec.ts")
    _write(tmp_path, "Client/src/foo.spec.ts", "it('a', () => { expect(x).toBe(999) })\n")
    # auch nach Subagent-eigenem Stagen muss der Anker greifen
    g("add", "Client/src/foo.spec.ts")
    # // When gegen die Freigabe-SHA geprüft wird
    findings, lines = qa.audit_approved_tests("frontend", {"Client/src/foo.spec.ts": sha})
    # // Then wird die Abweichung samt konkretem Diff (WAS geändert wurde) gemeldet
    assert findings == 1
    assert "999" in "\n".join(lines)


def test_audit_approved_tests_names_missing_blob_and_way_out(tmp_path, monkeypatch):
    # // Given ein Anker, der ohne -w berechnet wurde (Blob nicht in der Objektdatenbank), und eine
    #    danach geänderte Test-Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/foo.spec.ts", "it('a', () => { expect(x).toBe(1) })\n")
    monkeypatch.chdir(tmp_path)
    sha = subprocess.run(["git", "hash-object", "Client/src/foo.spec.ts"], cwd=tmp_path,
                         capture_output=True, text=True).stdout.strip()
    _write(tmp_path, "Client/src/foo.spec.ts", "it('a', () => { expect(x).toBe(999) })\n")
    # // When gegen diesen Anker geprüft wird
    findings, lines = qa.audit_approved_tests("frontend", {"Client/src/foo.spec.ts": sha})
    # // Then zählt die Abweichung, und die Meldung nennt den fehlenden Blob samt Ausweg statt eines leeren Diffs
    assert findings == 1
    text = "\n".join(lines)
    assert "nicht in der Objektdatenbank" in text
    assert "git hash-object -w" in text


def test_audit_approved_tests_flags_unapproved(tmp_path, monkeypatch):
    # // Given eine geänderte Test-Datei ohne Freigabe-SHA
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/new.spec.ts", "it('a', () => {})\n")
    monkeypatch.chdir(tmp_path)
    # // When ohne Freigabe-SHA geprüft wird
    findings, lines = qa.audit_approved_tests("frontend", {})
    # // Then wird die nie freigegebene Test-Datei als Auffälligkeit gemeldet
    assert findings == 1
    assert any("KEINE Freigabe" in line for line in lines)


def test_is_test_file_recognizes_repo_conventions():
    # // Given die realen Test-Namenskonventionen des Repos
    # // Then erkennt _is_test_file Vitest-Unit-Tests (.test.ts/.test.tsx),
    #        Playwright-E2E (.spec.ts) und Backend-xUnit (…Tests.cs)
    assert qa._is_test_file("Client/src/pages/IngredientsPage.test.tsx")
    assert qa._is_test_file("Client/src/services/conditionalGet.test.ts")
    assert qa._is_test_file("Client/e2e/ingredients.spec.ts")
    assert qa._is_test_file("Server.Tests/IngredientsEndpointsTests.cs")
    # // And behandelt Nicht-Test-Quelldateien NICHT als Test
    assert not qa._is_test_file("Client/src/pages/IngredientsPage.tsx")
    assert not qa._is_test_file("Client/src/services/conditionalGet.ts")


def test_is_test_file_recognizes_test_helpers_by_directory():
    # // Given Testhelfer, deren Name keiner Test-Endung folgt (run-9: RecipeRequests.cs,
    #          EndpointsTestsBase.cs liefen am Freigabe-Audit vorbei)
    # // Then zählen sie über ihr Verzeichnis als Testdatei
    assert qa._is_test_file("Server.Tests/Helpers/RecipeRequests.cs")
    assert qa._is_test_file("Server.Tests/Helpers/EndpointsTestsBase.cs")
    assert qa._is_test_file("Client/src/test/setup.ts")
    assert qa._is_test_file("Client/src/mocks/server.ts")
    # // And ein gleichnamiges Verzeichnis tiefer im Produktcode zählt nicht
    assert not qa._is_test_file("Server/Types/StringConstraints.cs")
    assert not qa._is_test_file("Client/src/pages/test/Foo.ts")


def test_audit_approved_tests_recognizes_test_tsx(tmp_path, monkeypatch):
    # // Given eine freigegebene .test.tsx (echte Vitest-Konvention), danach in einer
    #        Assertion geändert und vom Subagent gestaged. Regression: früher war
    #        _is_test_file blind für .test.tsx → der Anker-Audit lief für Frontend-Runs
    #        ins Leere ("taucht nicht unter geänderten Test-Dateien auf").
    g = _init_repo(tmp_path)
    _write(tmp_path, "Client/src/app.ts", "x\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Client/src/pages/Foo.test.tsx", "it('a', () => { expect(x).toBe(1) })\n")
    monkeypatch.chdir(tmp_path)
    sha = _hash_object(tmp_path, "Client/src/pages/Foo.test.tsx")
    _write(tmp_path, "Client/src/pages/Foo.test.tsx", "it('a', () => { expect(x).toBe(999) })\n")
    g("add", "Client/src/pages/Foo.test.tsx")
    # // When gegen die Freigabe-SHA geprüft wird
    findings, lines = qa.audit_approved_tests("frontend", {"Client/src/pages/Foo.test.tsx": sha})
    # // Then greift der Anker-Audit auch für .test.tsx (Abweichung samt Diff gemeldet)
    assert findings == 1
    assert "999" in "\n".join(lines)


# --- Backend-Tests unter Server.Tests/ (OBS-S102-2: Layer-Präfix war blind) ---
# Regression: Backend-xUnit-Tests liegen unter Server.Tests/, der Layer-Präfix war aber
# nur "Server/". "Server.Tests/…".startswith("Server/") ist False → check_changed_test_files,
# der Blob-Anker-Audit UND der Übergabe-Hash-Fingerprint waren für Backend-Testcode blind
# (CM-S070-1 faktisch aus). Frontend war nie betroffen (Tests unter Client/src/).

def test_check_changed_test_files_backend_in_server_tests_dir(tmp_path, monkeypatch):
    # // Given eine geänderte Backend-Test-Datei unter Server.Tests/
    g = _init_repo(tmp_path)
    _write(tmp_path, "Server/Endpoints/Foo.cs", "// prod\n")
    _write(tmp_path, "Server.Tests/FooTests.cs", "// [Fact] a\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Server.Tests/FooTests.cs", "// [Fact] a CHANGED\n")
    monkeypatch.chdir(tmp_path)
    # // When / // Then wird sie als geänderte Backend-Test-Datei gelistet
    assert "Server.Tests/FooTests.cs" in qa.check_changed_test_files("backend")


def test_content_fingerprint_backend_binds_server_tests(tmp_path, monkeypatch):
    # // Given ein committeter Ausgangszustand mit Prod- und Test-Datei
    g = _init_repo(tmp_path)
    _write(tmp_path, "Server/Endpoints/Foo.cs", "// prod\n")
    _write(tmp_path, "Server.Tests/FooTests.cs", "// assert 1\n")
    g("add", ".")
    g("commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    base = qa._worktree_content_fingerprint("backend")
    # // When NUR der Backend-Testcode geändert wird (z.B. Assertion entfernt)
    _write(tmp_path, "Server.Tests/FooTests.cs", "// assert entfernt\n")
    # // Then ändert sich der Übergabe-Fingerprint (sonst wäre CM-S070-1 für Backend wirkungslos)
    assert qa._worktree_content_fingerprint("backend") != base


def test_audit_approved_tests_backend_server_tests_dir(tmp_path, monkeypatch):
    # // Given eine freigegebene Backend-Test-Datei, deren Assertion danach geändert wurde
    g = _init_repo(tmp_path)
    _write(tmp_path, "Server/Endpoints/Foo.cs", "// prod\n")
    g("add", ".")
    g("commit", "-qm", "init")
    _write(tmp_path, "Server.Tests/FooTests.cs", "// Assert.Equal(1, x)\n")
    monkeypatch.chdir(tmp_path)
    sha = _hash_object(tmp_path, "Server.Tests/FooTests.cs")
    _write(tmp_path, "Server.Tests/FooTests.cs", "// Assert.Equal(999, x)\n")
    g("add", "Server.Tests/FooTests.cs")
    # // When gegen die Freigabe-SHA geprüft wird
    findings, lines = qa.audit_approved_tests("backend", {"Server.Tests/FooTests.cs": sha})
    # // Then greift der Anker-Audit auch für Server.Tests/ (Abweichung samt Diff gemeldet)
    assert findings == 1
    assert "999" in "\n".join(lines)


# --- tsc-Gate (OBS-S090-1-Follow-up: Fast-Fail vor Stryker) ---

def test_tsc_gate_runs_typecheck(monkeypatch):
    # // Given ein gemocktes subprocess.run
    calls = {}

    def fake_run(cmd, **kw):
        calls["cmd"] = cmd
        calls["cwd"] = str(kw.get("cwd"))

        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(qa.subprocess, "run", fake_run)
    # // When check_tsc läuft
    rc = qa.check_tsc()
    # // Then ruft es `npm run typecheck` im Client-Verzeichnis auf
    assert rc == 0
    assert "typecheck" in calls["cmd"]
    assert calls["cwd"].endswith("Client")


# --- ESLint-Meldung (Check 4) und Hash-Warnung bei rotem Check ---

# Echte Ausgabe von `python3 -m prozesscode.eslint-run` (S142) mit zwei Fehlern in einer
# Wegwerfdatei. Die letzte Zeile ist der Wrapper-Hinweis – genau sie meldete Check 4 früher als Befund.
_ESLINT_RUN_FEHLER = """\
{root}/Client/e2e/api/zz-gegenprobe.ts
  2:3  error  Unexpected let, use const instead           functional/no-let
  3:3  error  Unexpected loop, use map or reduce instead  functional/no-loop-statements

{root}/Client/e2e/ingredients.spec.ts
  32:1  warning  Async function 'restoreInFlightBeforeClientRestore' has too many parameters (5). Maximum allowed is 4  max-params

{root}/Client/src/pages/CreateRecipePage.tsx
  15:16  warning  Function 'CreateRecipePage' has too many lines (52). Maximum allowed is 50  max-lines-per-function

✖ 4 problems (2 errors, 2 warnings)

✗ ESLint: 2 Fehler, 2 Warnung(en) – oben aufgelistet
   (vollständiger Output: --verbose)
"""


def _fake_eslint(monkeypatch, stdout: str, returncode: int):
    class R:
        pass
    r = R()
    r.stdout, r.stderr, r.returncode = stdout, "", returncode
    monkeypatch.setattr(qa, "_changed_paths", lambda _paths: ["Client/e2e/api/zz-gegenprobe.ts"])
    monkeypatch.setattr(qa.subprocess, "run", lambda *_a, **_kw: r)


def test_check_eslint_reports_each_error_with_file_position_and_rule(monkeypatch):
    # // Given eslint-run scheitert mit seiner echten Ausgabe: zwei Fehler, zwei Warnungen
    _fake_eslint(monkeypatch, _ESLINT_RUN_FEHLER.format(root=qa._REPO_ROOT), 1)
    # // When Check 4 läuft
    status, code = qa.check_eslint("frontend")
    # // Then nennt die Meldung jeden Fehler mit repo-relativer Datei, Position und Regel –
    #    nicht die Warnungen und nicht den Wrapper-Hinweis als Befund
    assert code == 1
    lines = status.splitlines()
    assert "  Client/e2e/api/zz-gegenprobe.ts:2:3 functional/no-let – Unexpected let, use const instead" in lines
    assert ("  Client/e2e/api/zz-gegenprobe.ts:3:3 functional/no-loop-statements – "
            "Unexpected loop, use map or reduce instead") in lines
    assert str(qa._REPO_ROOT) not in status
    assert "max-params" not in status
    assert "(vollständiger Output: --verbose)" not in status


def test_check_eslint_without_parsable_error_lines_reports_output_before_wrapper_trailer(monkeypatch):
    # // Given eslint-run scheitert ohne Fehlerzeilen im bekannten Format (ESLint-Absturz). Der Absturztext
    #    ist nachgebildet; die Schlusszeilen haben die echte Form von _wrapper_output.emit – genau sie
    #    meldete der Rückfall früher als Befund.
    crash = ("Oops! Something went wrong! :(\n\nESLint: 9.39.1\n\nTypeError: x is undefined\n"
             "    at Object.create (rule.js:1:1)\n    at lint (linter.js:2:2)\n    at run (cli.js:3:3)\n"
             f"\n✗ ESLint: Abbruch\n{qa.VERBOSE_HINT}\n")
    _fake_eslint(monkeypatch, crash, 2)
    # // When Check 4 läuft
    status, code = qa.check_eslint("frontend")
    # // Then ist der Anfang der Ausgabe der Befund – nicht Verdikt oder --verbose-Hinweis des Wrappers,
    #    und der Stacktrace ist abgeschnitten (vollständig zeigt ihn eslint-run selbst)
    assert code == 2
    assert "TypeError: x is undefined" in status
    assert "✗ ESLint: Abbruch" not in status
    assert qa.VERBOSE_HINT not in status
    assert "at run (cli.js:3:3)" not in status


def test_check_eslint_short_fallback_output_drops_wrapper_trailer(monkeypatch):
    # // Given ein kurzer Absturz: Befund und Wrapper-Schlusszeilen passen zusammen in den gezeigten Ausschnitt
    _fake_eslint(monkeypatch, f"Oops! Something went wrong! :(\nTypeError: x is undefined\n\n"
                              f"✗ ESLint: Abbruch\n{qa.VERBOSE_HINT}\n", 2)
    # // When Check 4 läuft
    status, _ = qa.check_eslint("frontend")
    # // Then stehen beide Befundzeilen je für sich da, Verdikt und --verbose-Hinweis des Wrappers nicht
    lines = status.splitlines()
    assert "  Oops! Something went wrong! :(" in lines
    assert "  TypeError: x is undefined" in lines
    assert "  ✗ ESLint: Abbruch" not in lines
    assert qa.VERBOSE_HINT not in status


def test_check_eslint_without_any_output_says_so(monkeypatch):
    # // Given eslint-run scheitert ohne jede Ausgabe
    _fake_eslint(monkeypatch, "", 2)
    # // When Check 4 läuft
    status, code = qa.check_eslint("frontend")
    # // Then nennt die Meldung das Fehlen der Ausgabe statt still leer zu bleiben
    assert code == 2
    assert qa.ESLINT_NO_OUTPUT in status


# Echte Ausgabe von eslint-run (S142) bei einem Parsing-Fehler: die Fehlerzeile trägt keinen Regelnamen.
_ESLINT_RUN_PARSING_ERROR = """\
{root}/Client/e2e/api/zz-gegenprobe.ts
  1:23  error  Parsing error: Expression expected

{root}/Client/src/pages/CreateRecipePage.tsx
  15:16  warning  Function 'CreateRecipePage' has too many lines (52). Maximum allowed is 50  max-lines-per-function

✖ 2 problems (1 error, 1 warning)

✗ ESLint: 1 Fehler, 1 Warnung(en) – oben aufgelistet
   (vollständiger Output: --verbose)
"""


def test_check_eslint_reports_parsing_error_without_rule(monkeypatch):
    # // Given eslint-run scheitert an einem Parsing-Fehler (Fehlerzeile ohne Regelnamen)
    _fake_eslint(monkeypatch, _ESLINT_RUN_PARSING_ERROR.format(root=qa._REPO_ROOT), 1)
    # // When Check 4 läuft
    status, _ = qa.check_eslint("frontend")
    # // Then wird auch dieser Fehler mit Datei und Position gemeldet, statt still zu fehlen
    assert "  Client/e2e/api/zz-gegenprobe.ts:1:23 – Parsing error: Expression expected" in status.splitlines()


def test_check_eslint_flags_incomplete_list_when_summary_counts_more_errors(monkeypatch):
    # // Given die echte Ausgabe, in der eine der zwei Fehlerzeilen ein unbekanntes Format hat (Position
    #    ohne Spalte) – ESLints Zusammenfassung zählt weiter zwei Fehler
    output = _ESLINT_RUN_FEHLER.format(root=qa._REPO_ROOT).replace(
        "  2:3  error  Unexpected let", "  2  error  Unexpected let")
    _fake_eslint(monkeypatch, output, 1)
    # // When Check 4 läuft
    status, _ = qa.check_eslint("frontend")
    # // Then meldet Check 4 den erkannten Fehler und dass die Liste unvollständig ist
    assert "FEHLER – 1 Fehler:" in status
    assert qa.ESLINT_INCOMPLETE.format(reported=2, parsed=1) in status.splitlines()


def test_check_eslint_complete_list_has_no_incomplete_note(monkeypatch):
    # // Given / When: echte Ausgabe, alle Fehlerzeilen im bekannten Format
    _fake_eslint(monkeypatch, _ESLINT_RUN_FEHLER.format(root=qa._REPO_ROOT), 1)
    status, _ = qa.check_eslint("frontend")
    # // Then fehlt der Unvollständig-Hinweis
    assert "unvollständig" not in status


def test_red_checks_names_failed_lint_and_adr_checks():
    # // Given / When / Then: nur ein Exit-Code > 0 ist rot; -1 heißt „übersprungen"
    assert qa.red_checks(lint_code=1, adr_code=0) == [qa.CHECK_ESLINT_TITLE]
    assert qa.red_checks(lint_code=-1, adr_code=1) == [qa.CHECK_ADR_TITLE]
    assert qa.red_checks(lint_code=0, adr_code=-1) == []


def test_red_check_warning_names_red_checks_or_is_absent():
    # // Given / When / Then: die Warnzeile nennt jeden roten Check; ohne roten Check gibt es keine.
    #    Dass main() sie hinter den Hash schreibt, belegt die Gegenprobe (S142: Wegwerfdatei mit
    #    ESLint-Fehler, voller qa-check-Lauf zeigte die Warnzeile).
    warning = qa.red_check_warning(lint_code=1, adr_code=2)
    assert warning is not None
    assert f"Rot: {qa.CHECK_ESLINT_TITLE}, {qa.CHECK_ADR_TITLE}." in warning
    assert qa.red_check_warning(lint_code=0, adr_code=-1) is None


# --- ESLint-Gate (Fast-Fail vor Stryker, S143: ein Lint-Fehler kam erst nach ~5 Minuten Stryker) ---

_LINT_FEHLER_STATUS = "FEHLER – 1 Fehler:\n  Client/src/hooks/useX.ts:5:3 functional/no-conditional-statements – x"


def test_lint_fast_fail_reports_errors_before_stryker():
    # // Given Check 4 meldet einen ESLint-Fehler
    # // When der Fast-Fail vor Stryker prüft
    message = qa.lint_fast_fail(_LINT_FEHLER_STATUS, 1)
    # // Then nennt die Meldung den Befund und dass Stryker deshalb nicht lief
    assert message is not None
    assert "Client/src/hooks/useX.ts:5:3" in message
    assert "vor Stryker" in message


def test_lint_fast_fail_is_silent_for_clean_or_skipped_lint():
    # // Given / When / Then: ohne Fehler (0) oder übersprungen (-1, Backend/keine .ts) kein Abbruch
    assert qa.lint_fast_fail("OK", 0) is None
    assert qa.lint_fast_fail("n/a (backend)", -1) is None


def _main_mit_lint_fehler(monkeypatch, *argv: str) -> tuple[list, list]:
    """Startet qa-check über seinen Einstieg; ESLint meldet einen Fehler. Liefert die Aufrufe von
    Stryker und von Check 4 – und den Exit-Code als SystemExit."""
    stryker_calls, lint_calls = [], []
    monkeypatch.setattr(qa, "check_tsc", lambda: 0)
    monkeypatch.setattr(qa, "structure_fast_fail", lambda _layer: None)
    monkeypatch.setattr(qa, "check_eslint", lambda layer: lint_calls.append(layer) or (_LINT_FEHLER_STATUS, 1))
    monkeypatch.setattr(qa, "_run_stryker", lambda layer: stryker_calls.append(layer) or 0)
    monkeypatch.setattr(qa.sys, "argv", ["qa-check", "--layer", "frontend", *argv])
    return stryker_calls, lint_calls


def test_main_stops_before_stryker_when_eslint_reports_errors(monkeypatch, capsys):
    # // Given ein Frontend-Übergabelauf: Typecheck und Struktur grün, ESLint meldet einen Fehler
    stryker_calls, lint_calls = _main_mit_lint_fehler(monkeypatch)
    # // When qa-check über seinen Einstieg läuft
    with pytest.raises(SystemExit) as stop:
        qa.main()
    # // Then bricht es mit dem Befund ab, ohne Stryker zu starten – ESLint lief genau einmal
    assert stop.value.code == 1
    assert stryker_calls == []
    assert lint_calls == ["frontend"]
    assert "Client/src/hooks/useX.ts:5:3" in capsys.readouterr().err


def test_verify_does_not_stop_early_on_eslint_errors(monkeypatch, capsys):
    # // Given --verify (kein Stryker-Lauf) mit ESLint-Fehler; ein Report fehlt, damit der Lauf
    #    an der nächsten Stelle nach dem Fast-Fail endet
    stryker_calls, lint_calls = _main_mit_lint_fehler(monkeypatch, "--verify", "abc")
    monkeypatch.setattr(qa, "_find_report", lambda _layer: None)
    # // When qa-check läuft
    with pytest.raises(SystemExit):
        qa.main()
    # // Then kein Fast-Fail: Der Lauf kommt bis zur Report-Suche, ESLint lief genau einmal
    err = capsys.readouterr().err
    assert "Abbruch vor Stryker" not in err
    assert "Kein Stryker-Report gefunden" in err
    assert lint_calls == ["frontend"]
    assert stryker_calls == []
