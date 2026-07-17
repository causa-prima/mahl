"""Tests für .claude/scripts/qa-check.py – Standard-Score (inkl. NoCoverage) + Hash/Verify.

Designentscheidung (Stale-Schutz): --skip-stryker gibt KEINEN Übergabe-Hash aus. Damit ist
jeder existierende Hash per Konstruktion ein Frisch-Lauf-Hash; ein MODE-Feld im Hash ist unnötig.
`verify_hash` rechnet den kanonischen Hash aus dem aktuellen Report+Tree nach und vergleicht.
"""
import importlib.util
import json
import os
import subprocess
import time

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
    assert any("KEINE Freigabe" in l for l in lines)


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
