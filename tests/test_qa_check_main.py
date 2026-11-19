"""Tests für prozesscode/qa-check.py über den Einstieg `main()` – Verdikt, Exit-Code, Ausgabe.

Aufbau wie im Produktivlauf: ein Wegwerf-Repo als CWD (Checks 1–3/5 und der Tree-Fingerabdruck
laufen echt über git), darin `StrykerOutput/<Schicht>/<Zeitstempel>/reports/mutation-report.json`.
Ersetzt sind nur die fremden Läufe: tsc, Stryker (legt den Report ab und liefert einen Exit-Code),
ESLint und der ADR-Check. Der Report ist ein gekürzter echter StrykerJS-Report
(tests/fixtures/qa_check_stryker_frontend_report.json: Quelltexte und Testdateien entfernt,
lange statusReason gekappt); einzelne Tests ändern daran nur Mutanten-Status.

Die Ausgabe wird überwiegend exakt verglichen: Sie ist die Schnittstelle zum Orchestrator, der
Verdikt, Befunde und Hash daraus liest.
"""
import json
import os
import subprocess
import time
from importlib import import_module
from pathlib import Path

import pytest
from conftest import cli_aufruf

qa = import_module("prozesscode.qa-check")
sr = import_module("prozesscode._stryker_report")

_FIXTURE = Path(__file__).parent / "fixtures" / "qa_check_stryker_frontend_report.json"
_LAUF_ORDNER = "2026-11-05.10-00-00"     # Report des Laufs, den der Test startet
_ALT_ORDNER = "2026-11-05.09-00-00"      # Report eines früheren Laufs
_ADR_GRUEN = ("✓ 3 ADR-Verweise im Code, alle gültig", 0)
_ADR_ROT = ("Server/Foo.cs:12   ADR-S099-1      ✗ nicht gefunden\n"
            "  3 ADR-Verweise im Code, davon 1 mit Befund (oben)", 1)
_LINT_ROT = ("FEHLER – 1 Fehler:\n  Client/src/app.ts:1:1 functional/no-let – Unexpected let", 1)


def _report(*, survived_zu: tuple[str, ...] = (), alle: str | None = None) -> dict:
    """Der echte Report; `survived_zu` gibt den beiden Survivors (in Dateireihenfolge) neue Status,
    `alle` setzt jeden Mutanten auf einen Status."""
    daten = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    mutanten = [m for d in daten["files"].values() for m in d["mutants"]]
    for m, status in zip([m for m in mutanten if m["status"] == "Survived"], survived_zu, strict=False):
        m["status"] = status
    for m in mutanten if alle else []:
        m["status"] = alle
    return daten


_REPORT_100 = dict(survived_zu=("Killed", "Killed"))


def _ablegen(schicht: str, ordner: str, daten: dict, *, alt: bool = False) -> Path:
    pfad = Path("StrykerOutput") / schicht / ordner / "reports" / "mutation-report.json"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten), encoding="utf-8")
    if alt:
        vor_einer_stunde = time.time() - 3600
        os.utime(pfad, (vor_einer_stunde, vor_einer_stunde))
    return pfad


class _Umgebung:
    """Wegwerf-Repo als CWD plus ersetzte fremde Läufe; zeichnet auf, welcher Lauf gestartet wurde."""

    def __init__(self, tmp_path, monkeypatch, *, tsc=0, stryker_rc=0, lauf_report=None,
                 lint=("OK", 0), adr=_ADR_GRUEN):
        self.tmp_path, self.monkeypatch = tmp_path, monkeypatch
        self.tsc_aufrufe, self.stryker_aufrufe, self.lint_aufrufe = 0, [], []
        self.lauf_report = lauf_report
        self._git("init", "-q")
        self._git("config", "user.email", "t@t")
        self._git("config", "user.name", "t")
        monkeypatch.chdir(tmp_path)

        def tsc_lauf():
            self.tsc_aufrufe += 1
            return tsc

        def stryker_lauf(layer):
            self.stryker_aufrufe.append(layer)
            if self.lauf_report is not None:
                _ablegen("Backend" if layer == "backend" else "Frontend", _LAUF_ORDNER, self.lauf_report)
            return stryker_rc

        monkeypatch.setattr(qa, "check_tsc", tsc_lauf)
        monkeypatch.setattr(qa, "_run_stryker", stryker_lauf)
        monkeypatch.setattr(qa, "check_eslint", lambda layer: self.lint_aufrufe.append(layer) or lint)
        monkeypatch.setattr(qa, "check_adr_refs", lambda: adr)

    def _git(self, *args):
        return subprocess.run(["git", *args], cwd=self.tmp_path, capture_output=True, text=True).stdout

    def dateien(self, inhalt: dict[str, str]):
        for rel, text in inhalt.items():
            p = self.tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def commit(self, inhalt: dict[str, str]):
        self.dateien(inhalt)
        self._git("add", ".")
        self._git("commit", "-qm", "basis")

    def blob(self, rel: str) -> str:
        return self._git("hash-object", "-w", rel).strip()


def _stryker_block(schicht: str, score: str, report: str) -> str:
    return (f"\n=== STRYKER ({schicht}) ===\nScore:  {score}\nUmfang: 1 Datei(en)  |  11 valide Mutanten\n"
            f"Report: {report}\n")


def _achtung(score: str) -> str:
    return (f"\n⚠️  ACHTUNG: Mutation-Score {score} < 100 % – dieser Lauf ist KEINE gültige Übergabe. "
            "Survivors/NoCoverage oben klären, bevor übergeben wird – außer solche, die laut „Welcher "
            "Survivor bekommt welche Reaktion?“ (docs/process/tdd-process.md#TDD-survivor-entscheidung) an "
            "den Orchestrator gemeldet werden: dann übergeben und jeden einzeln im Return aufführen.\n")


_FRONTEND_REPORT = f"StrykerOutput/Frontend/{_LAUF_ORDNER}/reports/mutation-report.json"
_BACKEND_REPORT = f"StrykerOutput/Backend/{_LAUF_ORDNER}/reports/mutation-report.json"

# Frontend-Änderung mit je einem Befund für Check 1, 2 und 3; Given/When/Then vollständig.
_FRONTEND_BASIS = {"Client/src/app.ts": "export const a = 1\n"}
_FRONTEND_AENDERUNG = {
    "Client/src/app.ts": "// Stryker disable next-line all\nexport const a = 1\n",
    "Client/src/app.test.ts": "it('a', () => {\n  // Given\n  // When\n  // Then\n})\n",
}


def _gruppe(daten: dict, status: str) -> str:
    """Die Mutanten eines Status so, wie `_stryker_report` sie listet – das Format gehört dorthin."""
    je_datei = {datei: [m for m in d["mutants"] if m["status"] == status] for datei, d in daten["files"].items()}
    return "\n".join(sr.format_mutant_group(je_datei))


def _erwarteter_hash(layer: str, report: str, **befunde) -> str:
    """Der Hash über den Zustand im Wegwerf-Repo – Befunde als Literale, damit main() jeden einzelnen
    korrekt einbinden muss."""
    werte = dict(test_files=[], suppressions=[], unit_tests=[], lint_code=-1, test_structure=[], adr_code=0)
    werte.update(befunde)
    return qa.compute_hash(layer=layer, tree=qa._worktree_content_fingerprint(layer),
                           report_hash=qa._parse_report(Path(report))[2], **werte)


# --- Vollständiger Übergabelauf ---

@pytest.mark.aufrufpfad("qa-check")
def test_frontend_lauf_zeigt_alle_checks_den_hash_und_scheitert_am_score(tmp_path, monkeypatch, capsys):
    # // Given ein Frontend-Lauf mit Befunden in Check 1–3, rotem ADR-Check und einem Report mit
    #    einem Survivor und einem NoCoverage-Mutanten
    report = _report(survived_zu=("NoCoverage",))
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=report, adr=_ADR_ROT)
    u.commit(_FRONTEND_BASIS)
    u.dateien(_FRONTEND_AENDERUNG)
    # // When qa-check läuft
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend")
    # // Then: tsc, ESLint und Stryker liefen je einmal, alle Checks stehen da, der Hash mit Warnzeile,
    #    und der Score unter 100 % macht den Lauf ungültig
    out, err = capsys.readouterr()
    erwartet_hash = _erwarteter_hash(
        "frontend", _FRONTEND_REPORT, test_files=["Client/src/app.test.ts"],
        suppressions=[("Client/src/app.ts", "// Stryker disable next-line all")],
        unit_tests=[("Client/src/app.test.ts", "it('a', () => {")], lint_code=0, adr_code=1)
    assert out == (
        "[qa-check] tsc -b (Typecheck) …\n"
        "[qa-check] Starte Stryker (frontend) …\n"
        + _stryker_block("FRONTEND", "81.8%", _FRONTEND_REPORT) +
        f"\n⚠️  1 Survivor(s):\n{_gruppe(report, 'Survived')}\n"
        f"\n⚠️  1 NoCoverage (von keinem Test ausgeführt):\n{_gruppe(report, 'NoCoverage')}\n"
        "\n=== GEÄNDERTE TEST-DATEIEN ===\nClient/src/app.test.ts\n"
        "\n=== NEUE SUPPRESSIONEN ===\n  Client/src/app.ts:  // Stryker disable next-line all\n"
        "\n=== UNIT-TEST-MUSTER ===\n  Client/src/app.test.ts:  it('a', () => {\n"
        "\n=== ESLINT ===\nOK\n"
        "\n=== TEST-STRUKTUR (Given/When/Then) ===\nalle neuen Tests strukturiert\n"
        f"\n=== ADR-REFERENZEN ===\n{_ADR_ROT[0]}\n"
        f"\n=== VERIFIKATIONS-HASH ===\n{erwartet_hash}\n"
        "⚠️  Rot: ADR-REFERENZEN. Der Hash ist verifizierbar, die Übergabe aber erst gültig, wenn "
        "der Check grün ist – Befund oben beheben und qa-check erneut laufen lassen (oder den Befund im "
        "Return begründen).\n")
    assert err == _achtung("81.8%")
    assert code == 1
    assert (u.tsc_aufrufe, u.stryker_aufrufe, u.lint_aufrufe) == (1, ["frontend"], ["frontend"])


_BACKEND_CHECKS_LEER = (
    "\n=== GEÄNDERTE TEST-DATEIEN ===\nkeine\n"
    "\n=== NEUE SUPPRESSIONEN ===\nkeine\n"
    "\n=== UNIT-TEST-MUSTER ===\nkeine verdächtigen Treffer\n"
    "\n=== TEST-STRUKTUR (Given/When/Then) ===\nalle neuen Tests strukturiert\n"
    f"\n=== ADR-REFERENZEN ===\n{_ADR_GRUEN[0]}\n")


@pytest.mark.aufrufpfad("qa-check")
def test_backend_lauf_ohne_befunde_ist_gueltig_und_sein_hash_verifizierbar(tmp_path, monkeypatch, capsys):
    # // Given ein Backend-Lauf ohne geänderte Dateien mit einem Report ohne Survivor
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=_report(**_REPORT_100))
    u.commit({"Server/app.cs": "x\n"})
    # // When qa-check läuft
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend")
    out, err = capsys.readouterr()
    # // Then: kein tsc, kein ESLint, kein Check 4 – leere Checks, Hash ohne Warnung, Exit 0
    erwartet_hash = _erwarteter_hash("backend", _BACKEND_REPORT)
    stryker = _stryker_block("BACKEND", "100.0%", _BACKEND_REPORT)
    assert out == ("[qa-check] Starte Stryker (backend) …\n" + stryker + _BACKEND_CHECKS_LEER
                   + f"\n=== VERIFIKATIONS-HASH ===\n{erwartet_hash}\n")
    assert (err, code) == ("", 0)
    assert (u.tsc_aufrufe, u.stryker_aufrufe, u.lint_aufrufe) == (0, ["backend"], [])
    # // When der Orchestrator den Hash verifiziert
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend", "--verify", erwartet_hash)
    out, err = capsys.readouterr()
    # // Then stimmt er, ohne neuen Stryker-Lauf; der Audit hat keine Testdatei
    assert out == (stryker + _BACKEND_CHECKS_LEER
                   + "\n=== VERIFY ===\n✅ Hash verifiziert – frischer Lauf, Code/Report-Zustand stimmt überein.\n"
                   + "\n=== TEST-FREIGABE-AUDIT ===\nkeine geänderten Test-Dateien\n")
    assert (err, code) == ("", 0)
    assert u.stryker_aufrufe == ["backend"]


def test_verify_mit_falschem_hash_scheitert(tmp_path, monkeypatch, capsys):
    # // Given ein bestehender Report ohne Survivor, keine Änderungen
    u = _Umgebung(tmp_path, monkeypatch)
    u.commit({"Server/app.cs": "x\n"})
    _ablegen("Backend", _LAUF_ORDNER, _report(**_REPORT_100), alt=True)
    # // When ein Hash verifiziert wird, der nicht zum Zustand passt
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend", "--verify", "0123456789abcdef")
    out, err = capsys.readouterr()
    # // Then Exit 1 mit Begründung, kein Audit
    assert out.endswith(_BACKEND_CHECKS_LEER + "\n=== VERIFY ===\n")
    assert err == ("❌ Hash stimmt NICHT überein – der aktuelle Zustand weicht von dem ab, für den der Hash "
                   "erzeugt wurde (Code/Report seit der Übergabe geändert, falsche Schicht, oder ungültiger Hash).\n")
    assert code == 1


def test_skip_stryker_zeigt_alle_befunde_aber_keinen_hash(tmp_path, monkeypatch, capsys):
    # // Given ein alter Report ohne Survivor und ein neuer Test ohne Given/When/Then; ESLint und
    #    ADR-Check rot
    u = _Umgebung(tmp_path, monkeypatch, lint=_LINT_ROT, adr=_ADR_ROT)
    u.commit(_FRONTEND_BASIS)
    u.dateien({"Client/src/app.test.ts": "it('a', () => {})\n"})
    report = _ablegen("Frontend", _ALT_ORDNER, _report(**_REPORT_100), alt=True)
    # // When qa-check im Diagnose-Modus läuft
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend", "--skip-stryker")
    out, err = capsys.readouterr()
    # // Then: kein tsc, kein Stryker, kein Fast-Fail – jeder Befund steht da, statt des Hashes der Hinweis
    assert out == (
        _stryker_block("FRONTEND", "100.0%", str(report)) +
        "\n=== GEÄNDERTE TEST-DATEIEN ===\nClient/src/app.test.ts\n"
        "\n=== NEUE SUPPRESSIONEN ===\nkeine\n"
        "\n=== UNIT-TEST-MUSTER ===\n  Client/src/app.test.ts:  it('a', () => {})\n"
        f"\n=== ESLINT ===\n{_LINT_ROT[0]}\n"
        "\n=== TEST-STRUKTUR (Given/When/Then) ===\n"
        "  Client/src/app.test.ts:  it('a', () => {})  →  fehlt: // Given, // When, // Then\n"
        f"\n=== ADR-REFERENZEN ===\n{_ADR_ROT[0]}\n"
        "\n=== VERIFIKATIONS-HASH ===\n"
        "(übersprungen – --skip-stryker erzeugt KEINEN Übergabe-Hash. Nur Läufe ohne --skip-stryker sind "
        "zur Übergabe gültig; Verifikation durch den Orchestrator via --verify <hash>.)\n")
    assert (err, code) == ("", 0)
    assert (u.tsc_aufrufe, u.stryker_aufrufe, u.lint_aufrufe) == (0, [], ["frontend"])


# --- Verify mit Test-Freigabe-Audit ---

_ZWEI_TESTS = {
    "Client/src/a.test.ts": "it('a', () => {\n  // Given\n  // When\n  // Then\n})\n",
    "Client/src/b.test.ts": "it('b', () => {\n  // Given\n  // When\n  // Then\n})\n",
}


@pytest.mark.aufrufpfad("qa-check")
def test_verify_mit_freigaben_bestaetigt_hash_und_unveraenderte_tests(tmp_path, monkeypatch, capsys):
    # // Given ein gültiger Frontend-Lauf mit zwei neuen Testdateien
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=_report(**_REPORT_100))
    u.commit(_FRONTEND_BASIS)
    u.dateien(_ZWEI_TESTS)
    assert cli_aufruf(monkeypatch, qa, "--layer", "frontend") == 0
    lauf = capsys.readouterr().out
    vor_hash, _, hash_teil = lauf.partition("\n=== VERIFIKATIONS-HASH ===\n")
    uebergabe_hash = hash_teil.strip()
    # // When der Orchestrator Hash und beide Freigabe-Blobs übergibt
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend", "--verify", uebergabe_hash, "--approved-tests",
                      f"Client/src/a.test.ts={u.blob('Client/src/a.test.ts')}",
                      f"Client/src/b.test.ts={u.blob('Client/src/b.test.ts')}")
    out, err = capsys.readouterr()
    # // Then: Hash stimmt, beide Tests unverändert seit Freigabe – gültig, ohne neuen Stryker-Lauf
    checks = vor_hash.split("\n", 2)[2]          # ohne die Startzeilen von tsc und Stryker
    assert out == (checks
                   + "\n=== VERIFY ===\n✅ Hash verifiziert – frischer Lauf, Code/Report-Zustand stimmt überein.\n"
                   + "\n=== TEST-FREIGABE-AUDIT ===\n"
                   + "✅ Client/src/a.test.ts: unverändert seit Freigabe.\n"
                   + "✅ Client/src/b.test.ts: unverändert seit Freigabe.\n")
    assert (err, code) == ("", 0)
    assert u.stryker_aufrufe == ["frontend"]


def test_verify_meldet_rote_checks_und_audit_befund_und_haelt_das_score_gate(tmp_path, monkeypatch, capsys):
    # // Given ein bestehender Report mit Survivors, ESLint und ADR-Check rot, zwei neue Testdateien –
    #    nur eine davon freigegeben
    u = _Umgebung(tmp_path, monkeypatch, lint=_LINT_ROT, adr=_ADR_ROT)
    u.commit(_FRONTEND_BASIS)
    u.dateien(_ZWEI_TESTS)
    report = _ablegen("Frontend", _LAUF_ORDNER, _report(), alt=True)
    uebergabe_hash = _erwarteter_hash(
        "frontend", str(report), test_files=["Client/src/a.test.ts", "Client/src/b.test.ts"],
        unit_tests=[("Client/src/a.test.ts", "it('a', () => {"), ("Client/src/b.test.ts", "it('b', () => {")],
        lint_code=1, adr_code=1)
    # // When verifiziert wird
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend", "--verify", uebergabe_hash,
                      "--approved-tests", f"Client/src/a.test.ts={u.blob('Client/src/a.test.ts')}")
    out, err = capsys.readouterr()
    # // Then stimmt der Hash, die Warnzeile nennt beide roten Checks, der Audit die nicht freigegebene
    #    Datei – und der Score unter 100 % macht die Übergabe trotzdem ungültig
    assert out.endswith(
        "\n=== VERIFY ===\n✅ Hash verifiziert – frischer Lauf, Code/Report-Zustand stimmt überein.\n"
        "⚠️  Rot: ESLINT, ADR-REFERENZEN. Der Hash ist verifizierbar, die Übergabe aber "
        "erst gültig, wenn der Check grün ist – Befund oben beheben und qa-check erneut laufen lassen (oder "
        "den Befund im Return begründen).\n"
        "\n=== TEST-FREIGABE-AUDIT ===\n"
        "✅ Client/src/a.test.ts: unverändert seit Freigabe.\n"
        "⚠️  Client/src/b.test.ts: geändert, aber KEINE Freigabe-SHA übergeben – nie im Test-Review freigegeben?\n")
    assert err == ("\n⚠️  1 Test-Datei(en) seit Freigabe geändert bzw. ohne Freigabe – obige Diffs prüfen "
                   "(nur Setup erlaubt).\n" + _achtung("81.8%"))
    assert code == 1


def test_verify_ohne_freigaben_bei_geaenderten_tests_bricht_ab(tmp_path, monkeypatch, capsys):
    # // Given geänderte Testdateien und ein bestehender Report
    u = _Umgebung(tmp_path, monkeypatch)
    u.commit(_FRONTEND_BASIS)
    u.dateien(_ZWEI_TESTS)
    _ablegen("Frontend", _LAUF_ORDNER, _report(**_REPORT_100), alt=True)
    # // When ohne --approved-tests verifiziert wird
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend", "--verify", "0123456789abcdef")
    out, err = capsys.readouterr()
    # // Then Abbruch vor dem Hash-Vergleich
    assert "=== VERIFY ===" not in out
    assert err == ("❌ --verify ohne --approved-tests, obwohl dieser Lauf Test-Dateien ändert. Übergib die im "
                   "Test-Review freigegebenen Blobs (`git hash-object -w <datei>`) via --approved-tests "
                   "<pfad=sha …>, damit prüfbar bleibt, dass nach der Freigabe nur Setup (erlaubt) und keine "
                   "Assertions geändert wurden.\n")
    assert code == 1


# --- Abbrüche vor und nach Stryker ---

def test_tsc_fehler_bricht_vor_stryker_ab(tmp_path, monkeypatch, capsys):
    # // Given ein Frontend-Lauf, dessen Typecheck scheitert
    u = _Umgebung(tmp_path, monkeypatch, tsc=2, lauf_report=_report(**_REPORT_100))
    u.commit(_FRONTEND_BASIS)
    # // When / // Then: Exit 1, weder ESLint noch Stryker
    assert cli_aufruf(monkeypatch, qa, "--layer", "frontend") == 1
    assert capsys.readouterr() == (
        "[qa-check] tsc -b (Typecheck) …\n",
        "[qa-check] ❌ tsc -b fehlgeschlagen – Typfehler zuerst beheben. Kein Übergabe-Hash (Fast-Fail vor Stryker).\n")
    assert (u.stryker_aufrufe, u.lint_aufrufe) == ([], [])


def test_unstrukturierter_test_bricht_vor_stryker_ab(tmp_path, monkeypatch, capsys):
    # // Given ein neuer Backend-Test ohne Given/When/Then
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=_report(**_REPORT_100))
    u.commit({"Server/app.cs": "x\n"})
    u.dateien({"Server.Tests/FooTests.cs": "    [Fact]\n    public void Foo() { }\n"})
    # // When / // Then: Exit 1 mit dem Befund, Stryker lief nicht
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend") == 1
    assert capsys.readouterr() == ("", (
        "[qa-check] ❌ Test-Struktur (Given/When/Then) unvollständig – Abbruch vor Stryker, kein Übergabe-Hash:\n"
        "  Server.Tests/FooTests.cs:  [Fact]  →  fehlt: // Given, // When, // Then\n"
        "   Kommentare ergänzen, dann qa-check neu starten.\n"))
    assert u.stryker_aufrufe == []


def test_eslint_fehler_bricht_vor_stryker_ab(tmp_path, monkeypatch, capsys):
    # // Given ein Frontend-Lauf mit ESLint-Fehler
    u = _Umgebung(tmp_path, monkeypatch, lint=_LINT_ROT, lauf_report=_report(**_REPORT_100))
    u.commit(_FRONTEND_BASIS)
    # // When / // Then
    assert cli_aufruf(monkeypatch, qa, "--layer", "frontend") == 1
    assert capsys.readouterr() == (
        "[qa-check] tsc -b (Typecheck) …\n",
        f"[qa-check] ❌ ESLint meldet Fehler – Abbruch vor Stryker, kein Übergabe-Hash:\n{_LINT_ROT[0]}\n"
        "   Fehler beheben, dann qa-check neu starten.\n")
    assert u.stryker_aufrufe == []


def test_belegter_lock_bricht_ab_auch_wenn_ein_frischer_fremder_report_liegt(tmp_path, monkeypatch, capsys):
    # // Given Stryker startet nicht, weil ein konkurrierender Lauf den Lock hält – dessen frischer
    #    Report liegt schon da
    u = _Umgebung(tmp_path, monkeypatch, stryker_rc=qa.LOCK_BUSY_EXIT_CODE, lauf_report=_report(**_REPORT_100))
    u.commit({"Server/app.cs": "x\n"})
    # // When / // Then: Abbruch mit dem Lock-Code, kein Check, kein Hash
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend") == qa.LOCK_BUSY_EXIT_CODE
    assert capsys.readouterr() == (
        "[qa-check] Starte Stryker (backend) …\n",
        f"[qa-check] ❌ Stryker gar nicht gestartet – ein konkurrierender Lauf hält den Lock "
        f"(Exit {qa.LOCK_BUSY_EXIT_CODE}). Kein Übergabe-Hash: ein fremder Report belegt diesen Lauf nicht. "
        "Konkurrierenden Lauf abwarten und neu starten.\n")


_LAUF_FEHLER = ("[qa-check] ❌ Stryker-LAUF fehlgeschlagen (Exit 3) und kein frischer Report erzeugt – das "
                "deutet auf Build-/Compile-Fehler hin, NICHT auf ein Score-Gate. Harter Lauf-Fehler: kein "
                "Übergabe-Hash. Ursache oben im Stryker-Output beheben und neu starten.\n")


@pytest.mark.parametrize("alter_report", [False, True], ids=["ohne-report", "nur-alter-report"])
def test_gescheiterter_lauf_ohne_frischen_report_ist_harter_fehler(tmp_path, monkeypatch, capsys, alter_report):
    # // Given Stryker endet mit Exit 3 und schreibt keinen Report – höchstens ein alter liegt da
    u = _Umgebung(tmp_path, monkeypatch, stryker_rc=3)
    u.commit({"Server/app.cs": "x\n"})
    if alter_report:
        _ablegen("Backend", _ALT_ORDNER, _report(**_REPORT_100), alt=True)
    # // When / // Then: Stryker-Exit-Code durchgereicht, kein Check
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend") == 3
    assert capsys.readouterr() == ("[qa-check] Starte Stryker (backend) …\n", _LAUF_FEHLER)


def test_score_gate_von_stryker_macht_den_lauf_ungueltig_auch_bei_100_prozent(tmp_path, monkeypatch, capsys):
    """Stryker meldet Exit 1, schreibt aber einen frischen Report: die Checks laufen weiter, der Lauf
    bleibt ungültig – auch wenn der Report selbst keinen Survivor zeigt."""
    # // Given
    u = _Umgebung(tmp_path, monkeypatch, stryker_rc=1, lauf_report=_report(**_REPORT_100))
    u.commit({"Server/app.cs": "x\n"})
    # // When
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend")
    out, err = capsys.readouterr()
    # // Then: alle Checks und der Hash, dazu Warnung und Exit 1 – die Meldung nennt den Exit-Code als
    #    Grund, nicht einen Score unter 100 %, den der Report nicht zeigt
    assert out == ("[qa-check] Starte Stryker (backend) …\n" + _stryker_block("BACKEND", "100.0%", _BACKEND_REPORT)
                   + _BACKEND_CHECKS_LEER
                   + f"\n=== VERIFIKATIONS-HASH ===\n{_erwarteter_hash('backend', _BACKEND_REPORT)}\n")
    assert err == ("[qa-check] ⚠️  Stryker endete mit Exit 1 – frischer Report vorhanden, führe restliche "
                   "Checks dennoch aus.\n"
                   "\n⚠️  ACHTUNG: Stryker endete mit Exit 1, der Report zeigt aber 100.0% – der Score ist nicht "
                   "der Grund. Dieser Lauf ist KEINE gültige Übergabe: Ursache im Stryker-Output oben suchen, "
                   "beheben und qa-check erneut laufen lassen.\n")
    assert code == 1


def test_score_gate_von_stryker_unter_100_prozent_nennt_den_score(tmp_path, monkeypatch, capsys):
    # // Given Stryker endet mit Exit 1, der frische Report zeigt einen Survivor
    _Umgebung(tmp_path, monkeypatch, stryker_rc=1, lauf_report=_report(survived_zu=("Killed",))).commit(
        {"Server/app.cs": "x\n"})
    # // When
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend")
    # // Then: nur die Score-Warnung – der Exit-Code ist durch den Score erklärt
    assert capsys.readouterr().err == (
        "[qa-check] ⚠️  Stryker endete mit Exit 1 – frischer Report vorhanden, führe restliche Checks "
        "dennoch aus.\n" + _achtung("90.9%"))
    assert code == 1


# --- Timeouts in geänderten Dateien ---

_GEMESSENE_DATEI = "Client/src/hooks/useDeleteIngredientWithUndo.ts"   # die Datei des Fixture-Reports


def _timeout_achtung(anzahl: int) -> str:
    return (f"\n⚠️  ACHTUNG: {anzahl} Timeout(s) in geänderten Dateien – Stryker zählt sie als erkannt, belegt "
            "ist das nicht: Eine zu knappe Zeitgrenze hat schon Survivors verdeckt. Dieser Lauf ist KEINE gültige "
            "Übergabe, bis jeder geklärt ist. Kann der Mutant eine Schleife oder ein Warten ohne Ende erzeugen, "
            "ist er erkannt; sonst ist er wie ein Survivor zu behandeln (docs/process/tdd-process.md"
            "#TDD-survivor-entscheidung). Jeden einzeln mit Einordnung im Return aufführen.\n")


@pytest.mark.aufrufpfad("qa-check")
def test_timeout_in_geaenderter_datei_wird_ausgewiesen_und_macht_den_lauf_ungueltig(tmp_path, monkeypatch, capsys):
    # // Given ein Frontend-Lauf mit 100 %, davon ein Timeout in der geänderten Datei
    report = _report(survived_zu=("Timeout", "Killed"))
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=report)
    u.commit({_GEMESSENE_DATEI: "a\n"})
    u.dateien({_GEMESSENE_DATEI: "b\n"})
    # // When qa-check läuft
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend")
    out, err = capsys.readouterr()
    # // Then: der Timeout steht gesondert direkt unter dem Stryker-Block, der Hash wird ausgegeben,
    #    und der Lauf ist ungültig
    erwartet_hash = _erwarteter_hash("frontend", _FRONTEND_REPORT, lint_code=0)
    assert out.startswith(
        "[qa-check] tsc -b (Typecheck) …\n[qa-check] Starte Stryker (frontend) …\n"
        + _stryker_block("FRONTEND", "100.0%", _FRONTEND_REPORT)
        + f"\n{qa.TIMEOUT_TITEL.format(anzahl=1)}\n{_gruppe(report, 'Timeout')}\n"
        + "\n=== GEÄNDERTE TEST-DATEIEN ===\n")
    assert out.endswith(f"\n=== VERIFIKATIONS-HASH ===\n{erwartet_hash}\n")
    assert (err, code) == (_timeout_achtung(1), 1)
    # // When der Orchestrator den Hash verifiziert
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend", "--verify", erwartet_hash)
    # // Then: Hash stimmt, das Timeout-Gate gilt auch hier
    out, err = capsys.readouterr()
    assert "✅ Hash verifiziert" in out
    assert (err, code) == (_timeout_achtung(1), 1)


def test_timeout_im_backend_wird_ueber_den_absoluten_report_pfad_erkannt(tmp_path, monkeypatch, capsys):
    # // Given ein Backend-Report mit einem Timeout in der geänderten Datei Server/Domain/Foo.cs. Die
    #    Pfadform ist nachgebaut: Stryker.NET schreibt absolute Pfade als Schlüssel (an einem echten
    #    Report gesichtet: /home/…/repos/mahl/Server/Domain/Ingredient.cs); die einzige Datei des echten
    #    Frontend-Reports bekommt diesen Schlüssel.
    report = _report(survived_zu=("Timeout", "Killed"))
    [einzige_datei] = report["files"].values()
    report["files"] = {f"{tmp_path}/Server/Domain/Foo.cs": einzige_datei}
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=report)
    u.commit({"Server/Domain/Foo.cs": "a\n"})
    u.dateien({"Server/Domain/Foo.cs": "b\n"})
    # // When
    code = cli_aufruf(monkeypatch, qa, "--layer", "backend")
    out, err = capsys.readouterr()
    # // Then: der Timeout steht unter dem Repo-Pfad der Datei, der Lauf ist ungültig
    assert f"\n{qa.TIMEOUT_TITEL.format(anzahl=1)}\n  Server/Domain/Foo.cs (1)\n" in out
    assert (err, code) == (_timeout_achtung(1), 1)


def test_timeout_in_unveraenderter_datei_bleibt_aussen_vor(tmp_path, monkeypatch, capsys):
    # // Given ein Timeout in der Datei des Reports, geändert ist aber eine andere Datei
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=_report(survived_zu=("Timeout", "Killed")))
    u.commit({_GEMESSENE_DATEI: "a\n", "Client/src/app.ts": "a\n"})
    u.dateien({"Client/src/app.ts": "b\n"})
    # // When
    code = cli_aufruf(monkeypatch, qa, "--layer", "frontend")
    out, err = capsys.readouterr()
    # // Then: kein Timeout-Block, gültige Übergabe
    assert "Timeout" not in out
    assert (err, code) == ("", 0)


def test_erfolgreicher_lauf_mit_nur_altem_report_ist_harter_fehler(tmp_path, monkeypatch, capsys):
    # // Given Stryker endet mit Exit 0, es liegt aber nur ein Report eines früheren Laufs da
    u = _Umgebung(tmp_path, monkeypatch)
    u.commit({"Server/app.cs": "x\n"})
    alt = _ablegen("Backend", _ALT_ORDNER, _report(**_REPORT_100), alt=True)
    # // When / // Then
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend") == 1
    assert capsys.readouterr() == (
        "[qa-check] Starte Stryker (backend) …\n",
        f"[qa-check] ❌ Gefundener Report ist nicht aus diesem Lauf (veraltet): {alt}. "
        "Harter Lauf-Fehler – kein Übergabe-Hash.\n")


def test_ohne_report_bricht_der_diagnose_modus_ab(tmp_path, monkeypatch, capsys):
    # // Given kein Report
    u = _Umgebung(tmp_path, monkeypatch)
    u.commit({"Server/app.cs": "x\n"})
    # // When / // Then
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend", "--skip-stryker") == 1
    assert capsys.readouterr() == ("", "[qa-check] Kein Stryker-Report gefunden.\n")


def test_report_ohne_validen_mutanten_ergibt_keinen_hash(tmp_path, monkeypatch, capsys):
    # // Given ein frischer Report, in dem jeder Mutant ein CompileError ist
    report = _report(alle="CompileError")
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=report)
    u.commit({"Server/app.cs": "x\n"})
    # // When / // Then: harter Fehler mit Status-Verteilung, keine Checks
    assert cli_aufruf(monkeypatch, qa, "--layer", "backend") == 1
    verteilung = sr.format_status_breakdown(sr.compute_metrics(report["files"]))
    assert capsys.readouterr() == (
        "[qa-check] Starte Stryker (backend) …\n",
        f"[qa-check] ❌ {sr.NO_MUTANTS_HINT}\n{verteilung}\n   Kein Übergabe-Hash. Report: {_BACKEND_REPORT}\n")


# --- Argumente ---

@pytest.mark.parametrize("argumente", [[], ["--layer", "mobile"]], ids=["ohne-layer", "unbekannte-layer"])
def test_layer_ist_pflicht_und_auf_die_schichten_begrenzt(tmp_path, monkeypatch, capsys, argumente):
    # // Given
    u = _Umgebung(tmp_path, monkeypatch, lauf_report=_report(**_REPORT_100))
    u.commit({"Server/app.cs": "x\n"})
    # // When / // Then: argparse weist ab, nichts läuft
    assert cli_aufruf(monkeypatch, qa, *argumente) == 2
    assert "--layer" in capsys.readouterr().err
    assert u.stryker_aufrufe == []
