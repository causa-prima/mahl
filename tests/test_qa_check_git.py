"""Tests für prozesscode/qa-check.py – die Bausteine hinter den Checks.

Git-Auswertung (Pfade, Diff, Fingerabdruck), die Checks 2/3/5 gegen echte `git diff`-Ausgabe
in einem Wegwerf-Repo, die Subprozess-Aufrufe der fremden Werkzeuge (Stryker, ESLint, tsc,
decisions) und Report-Suche/-Frische/-Hash. Der Aufrufpfad über `main()` steht in
tests/test_qa_check_main.py.
"""
import json
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

from _git_repo import init_repo as _init_repo, write_file as _write

qa = import_module("prozesscode.qa-check")


def _repo_mit_basis(tmp_path, monkeypatch, dateien: dict[str, str]):
    """Wegwerf-Repo mit diesen Dateien als erstem Commit; CWD liegt darin (wie im Produktivlauf)."""
    g = _init_repo(tmp_path)
    for rel, inhalt in dateien.items():
        _write(tmp_path, rel, inhalt)
    g("add", ".")
    g("commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    return g


# --- Geänderte Pfade aus `git status --porcelain` ---

def test_geaenderte_pfade_nennen_bei_umbenennung_das_ziel(tmp_path, monkeypatch):
    # // Given eine gestagte Umbenennung – git status zeigt „R  alt -> neu"
    g = _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/alt.ts": "export const a = 1\n"})
    g("mv", "Client/src/alt.ts", "Client/src/neu.ts")
    assert "R  Client/src/alt.ts -> Client/src/neu.ts" in qa._git("status", "--porcelain")
    # // When die geänderten Pfade der Schicht gelesen werden
    pfade = qa._changed_paths(("Client/src/",))
    # // Then zählt nur das Ziel der Umbenennung
    assert pfade == ["Client/src/neu.ts"]


def test_geaenderte_pfade_ohne_anfuehrungszeichen_bei_leerzeichen_im_namen(tmp_path, monkeypatch):
    # // Given eine neue Datei mit Leerzeichen im Namen – git status setzt sie in Anführungszeichen
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    _write(tmp_path, "Client/src/mit leerzeichen.ts", "x\n")
    assert '?? "Client/src/mit leerzeichen.ts"' in qa._git("status", "--porcelain", "-uall")
    # // When die geänderten Pfade gelesen werden
    pfade = qa._changed_paths(("Client/src/",))
    # // Then steht der Pfad ohne Anführungszeichen da, lesbar für Path(...)
    assert pfade == ["Client/src/mit leerzeichen.ts"]


def test_datei_in_head_unterscheidet_bestand_von_neu_ohne_ausgabe(tmp_path, monkeypatch, capfd):
    # // Given eine committete und eine neue Datei
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/alt.ts": "x\n"})
    _write(tmp_path, "Client/src/neu.ts", "y\n")
    # // When / // Then: Bestand ist in HEAD, die neue Datei nicht – und git schreibt dabei nichts
    #    auf das Terminal (die Fehlermeldung von `cat-file -e` für die neue Datei bleibt gefangen)
    assert qa._file_in_head("Client/src/alt.ts") is True
    assert qa._file_in_head("Client/src/neu.ts") is False
    assert capfd.readouterr() == ("", "")


def test_bestehende_suppression_in_geaenderter_datei_ist_nicht_neu(tmp_path, monkeypatch):
    """Eine bestehende Datei wird gegen HEAD gedifft, nicht als Ganzes „hinzugefügt" – sonst
    erschiene jede alte Suppression in jeder angefassten Datei als neue."""
    # // Given eine committete Datei mit Suppression, in der nur eine andere Zeile geändert wird
    _repo_mit_basis(tmp_path, monkeypatch, {
        "Client/src/app.ts": "// Stryker disable next-line all\nexport const a = 1\n"})
    _write(tmp_path, "Client/src/app.ts", "// Stryker disable next-line all\nexport const a = 2\n")
    # // When / // Then keine neue Suppression
    assert qa.check_new_suppressions("frontend") == []


def test_entfernte_suppression_ist_kein_befund(tmp_path, monkeypatch):
    # // Given eine committete Suppression, die jetzt gelöscht wird
    _repo_mit_basis(tmp_path, monkeypatch, {
        "Client/src/app.ts": "// Stryker disable next-line all\nexport const a = 1\n"})
    _write(tmp_path, "Client/src/app.ts", "export const a = 1\n")
    # // When / // Then zählt nur Hinzugefügtes, die entfernte Zeile nicht
    assert qa.check_new_suppressions("frontend") == []


def test_neue_suppressionen_mit_datei_und_zeilentext(tmp_path, monkeypatch):
    # // Given zwei neue Suppressionen in zwei Dateien – eine nicht eingerückt, eine eingerückt
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.ts": "export const a = 1\n"})
    _write(tmp_path, "Client/src/a.ts", "/* v8 ignore next */\nexport const a = 1\n")
    _write(tmp_path, "Client/src/b.ts", "function f() {\n  // Stryker disable next-line all\n  return 1\n}\n")
    # // When / // Then nennt Check 2 je Fund Datei und Zeilentext – nur die Suppressionszeilen
    assert qa.check_new_suppressions("frontend") == [
        ("Client/src/a.ts", "/* v8 ignore next */"),
        ("Client/src/b.ts", "// Stryker disable next-line all"),
    ]


def test_fingerabdruck_zaehlt_geloeschte_datei(tmp_path, monkeypatch):
    # // Given eine committete Datei
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.ts": "x\n"})
    unveraendert = qa._worktree_content_fingerprint("frontend")
    # // When sie gelöscht wird
    (tmp_path / "Client/src/a.ts").unlink()
    # // Then ändert sich der Fingerabdruck, ohne dass das fehlende Lesen abbricht
    assert qa._worktree_content_fingerprint("frontend") != unveraendert


# --- Check 3: Unit-Test-Muster ---

def _fact_test(vorspann: str) -> str:
    return (f"public class FooTests\n{{\n{vorspann}"
            "    [Fact]\n    public void Foo()\n    {\n    }\n}\n")


def test_backend_fact_ohne_http_kontext_ist_verdaechtig(tmp_path, monkeypatch):
    # // Given ein neuer xUnit-Test ohne WebApplicationFactory/HttpClient in der Nähe
    _repo_mit_basis(tmp_path, monkeypatch, {"Server/app.cs": "x\n"})
    _write(tmp_path, "Server.Tests/FooTests.cs", _fact_test(""))
    # // When / // Then meldet Check 3 Datei und Zeile
    assert qa.check_unit_test_patterns("backend") == [("Server.Tests/FooTests.cs", "[Fact]")]


def test_backend_fact_mit_einem_der_http_merkmale_ist_unauffaellig(tmp_path, monkeypatch):
    # // Given je ein Test mit nur WebApplicationFactory bzw. nur HttpClient im Kontext
    _repo_mit_basis(tmp_path, monkeypatch, {"Server/app.cs": "x\n"})
    _write(tmp_path, "Server.Tests/ATests.cs", _fact_test("    WebApplicationFactory<Program> f;\n"))
    _write(tmp_path, "Server.Tests/BTests.cs", _fact_test("    HttpClient c;\n"))
    # // When / // Then reicht jedes der beiden Merkmale
    assert qa.check_unit_test_patterns("backend") == []


def test_backend_kontext_reicht_acht_zeilen_ueber_die_aenderung(tmp_path, monkeypatch):
    """Der Diff trägt 8 Kontextzeilen: ein unveränderter HTTP-Aufbau bis 8 Zeilen über dem neuen
    [Fact] zählt, einer 9 Zeilen darüber nicht mehr."""
    fuell = "".join(f"    // {i}\n" for i in range(7))
    nah = f"public class ATests\n{{\n    HttpClient c;\n{fuell}}}\n"           # 8 Zeilen über dem Einschub
    fern = f"public class BTests\n{{\n    HttpClient c;\n{fuell}    // 7\n}}\n"  # 9 Zeilen darüber
    _repo_mit_basis(tmp_path, monkeypatch, {"Server.Tests/ATests.cs": nah, "Server.Tests/BTests.cs": fern})
    # // Given in beiden Dateien ein neuer [Fact] direkt vor der schließenden Klammer
    _write(tmp_path, "Server.Tests/ATests.cs", nah.replace("}\n", "    [Fact]\n}\n"))
    _write(tmp_path, "Server.Tests/BTests.cs", fern.replace("}\n", "    [Fact]\n}\n"))
    # // When / // Then ist nur der ferne verdächtig
    assert qa.check_unit_test_patterns("backend") == [("Server.Tests/BTests.cs", "[Fact]")]


def test_backend_kontextfenster_umfasst_zwoelf_zeilen(tmp_path, monkeypatch):
    """Das Fenster umfasst die Zeile selbst und die elf davor: in einer neuen Datei zählt ein
    HttpClient elf Zeilen über dem [Fact], einer zwölf Zeilen darüber nicht mehr."""
    _repo_mit_basis(tmp_path, monkeypatch, {"Server/app.cs": "x\n"})
    fuell = "".join(f"// {i}\n" for i in range(10))
    # // Given zwei neue Testdateien, der HttpClient einmal 11, einmal 12 Zeilen über dem [Fact]
    _write(tmp_path, "Server.Tests/ATests.cs", f"HttpClient c;\n{fuell}[Fact]\n")
    _write(tmp_path, "Server.Tests/BTests.cs", f"HttpClient c;\n{fuell}// 10\n[Fact]\n")
    # // When / // Then ist nur der ferne verdächtig
    assert qa.check_unit_test_patterns("backend") == [("Server.Tests/BTests.cs", "[Fact]")]


def test_frontend_describe_und_it_ohne_msw_sind_verdaechtig(tmp_path, monkeypatch):
    # // Given eine neue Vitest-Datei ohne MSW-Aufbau, `describe` nicht eingerückt
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    _write(tmp_path, "Client/src/a.test.ts", "describe('a', () => {\n  it('b', () => {})\n})\n")
    # // When / // Then meldet Check 3 beide Aufrufe mit Datei
    assert qa.check_unit_test_patterns("frontend") == [
        ("Client/src/a.test.ts", "describe('a', () => {"),
        ("Client/src/a.test.ts", "it('b', () => {})"),
    ]


def test_frontend_mit_msw_aufbau_ist_unauffaellig(tmp_path, monkeypatch):
    # // Given eine neue Vitest-Datei, die einen MSW-Server aufsetzt
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    _write(tmp_path, "Client/src/a.test.ts",
           "const server = setupServer()\ndescribe('a', () => {\n  it('b', () => {})\n})\n")
    # // When / // Then kein Befund
    assert qa.check_unit_test_patterns("frontend") == []


# --- Check 5: Test-Struktur ---

def test_test_struktur_prueft_jeden_test_je_datei(tmp_path, monkeypatch):
    # // Given zwei neue Testdateien: in der ersten ein vollständiger und ein leerer Test (Kommentare
    #    nicht eingerückt), in der zweiten ein Test ohne // Then; dazu eine Nicht-Testdatei mit it(
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    _write(tmp_path, "Client/src/a.test.ts",
           "it('voll', () => {\n// Given\n// When\n// Then\n})\nit('leer', () => {\n})\n")
    _write(tmp_path, "Client/src/b.test.ts", "  it('halb', () => {\n    // Given\n    // When\n  })\n")
    _write(tmp_path, "Client/src/hilfe.ts", "it('kein test', () => {})\n")
    # // When / // Then nennt Check 5 je unvollständigem Test die fehlenden Stücke
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('leer', () => {  →  fehlt: // Given, // When, // Then"),
        ("Client/src/b.test.ts", "it('halb', () => {  →  fehlt: // Then"),
    ]


_GEGLIEDERTER_TEST = "  it('{name}', () => {{\n    // Given: a\n    // When: b\n    expect(1).toBe(1)\n    // Then: c\n  }})\n"


def test_test_struktur_umbenannter_test_mit_gliederung_im_rumpf_ist_kein_befund(tmp_path, monkeypatch):
    # // Given ein gegliederter Test im Bestand, von dem nur die it(-Zeile geändert wird – im Diff steht der
    #    Rumpf dann als Kontext, nicht als „+“
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": _GEGLIEDERTER_TEST.format(name="alt")})
    _write(tmp_path, "Client/src/a.test.ts", _GEGLIEDERTER_TEST.format(name="neu"))
    # // When / // Then zählt die Gliederung im unveränderten Rumpf
    assert qa.check_test_structure("frontend") == []


def test_test_struktur_neuer_test_erbt_keine_gliederung_vom_kontext_dahinter(tmp_path, monkeypatch):
    # // Given ein neuer Test ohne Gliederung direkt vor einem gegliederten Bestands-Test – dessen Kommentare
    #    stehen als Kontext im Diff, gehören aber nicht zum neuen Test
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": _GEGLIEDERTER_TEST.format(name="alt")})
    _write(tmp_path, "Client/src/a.test.ts", "  it('neu', () => {\n    expect(2).toBe(2)\n  })\n"
           + _GEGLIEDERTER_TEST.format(name="alt"))
    # // When / // Then bleibt der neue Test ein Befund
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('neu', () => {  →  fehlt: // Given, // When, // Then"),
    ]


def test_test_struktur_neuer_test_erbt_keine_gliederung_von_folgender_hilfsfunktion(tmp_path, monkeypatch):
    # // Given ein neuer Test ohne Gliederung vor einer Hilfsfunktion, die Given/When/Then-Kommentare trägt
    hilfe = "function hilfe() {\n  // Given: x\n  // When: y\n  // Then: z\n}\n"
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": hilfe})
    _write(tmp_path, "Client/src/a.test.ts", "it('neu', () => {\n  expect(2).toBe(2)\n})\n" + hilfe)
    # // When / // Then endet der Test an seiner schließenden Klammer – die Hilfsfunktion zählt nicht
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('neu', () => {  →  fehlt: // Given, // When, // Then"),
    ]


def test_test_struktur_entfernte_gliederung_zaehlt_nicht(tmp_path, monkeypatch):
    # // Given ein gegliederter Bestands-Test, dem Umbenennung und Gliederung zugleich genommen werden – die
    #    Kommentare stehen danach nur noch als „-“-Zeilen im Diff
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": _GEGLIEDERTER_TEST.format(name="alt")})
    _write(tmp_path, "Client/src/a.test.ts", "  it('neu', () => {\n    expect(1).toBe(1)\n  })\n")
    # // When / // Then zählt nur der neue Stand
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('neu', () => {  →  fehlt: // Given, // When, // Then"),
    ]


def test_test_struktur_langer_umbenannter_test_mit_gliederung_am_ende_ist_kein_befund(tmp_path, monkeypatch):
    # // Given ein gegliederter Test, dessen // Then 100 Zeilen unter der umbenannten Kopfzeile steht – weit
    #    außerhalb jedes Diff-Kontexts
    fuell = "".join(f"    expect({i}).toBe({i})\n" for i in range(100))
    lang = "  it('{name}', () => {{\n    // Given: a\n    // When: b\n" + fuell + "    // Then: c\n  }})\n"
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": lang.format(name="alt")})
    _write(tmp_path, "Client/src/a.test.ts", lang.format(name="neu"))
    # // When / // Then wird der ganze Rumpf gelesen, nicht nur der Kontext um die Änderung
    assert qa.check_test_structure("frontend") == []


def test_test_struktur_ungepaarte_klammer_endet_spaetestens_am_naechsten_test(tmp_path, monkeypatch):
    # // Given ein neuer ungegliederter Test mit einer ungepaarten „{“ in einem String – die textuelle
    #    Klammerzählung sieht sein Ende nicht; dahinter ein gegliederter Bestands-Test
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": _GEGLIEDERTER_TEST.format(name="alt")})
    _write(tmp_path, "Client/src/a.test.ts", "  it('neu', () => {\n    expect('{').toBe('{')\n  })\n"
           + _GEGLIEDERTER_TEST.format(name="alt"))
    # // When / // Then leiht er sich die Gliederung des nächsten Tests trotzdem nicht
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('neu', () => {  →  fehlt: // Given, // When, // Then"),
    ]


def test_test_struktur_langer_test_endet_an_seiner_klammer(tmp_path, monkeypatch):
    # // Given ein langer ungegliederter Test, dessen Kopf umbenannt wird, und weit dahinter (jenseits des
    #    40-Zeilen-Kontexts) ein zweiter, gegliederter Test, der sich ebenfalls ändert
    fuell = "".join(f"    expect({i}).toBe({i})\n" for i in range(100))
    lang = "  it('{name}', () => {{\n" + fuell + "  }})\n"
    zwischen = "".join(f"const z{i} = {i}\n" for i in range(60))
    basis = lang.format(name="alt") + zwischen + _GEGLIEDERTER_TEST.format(name="zweit")
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/a.test.ts": basis})
    _write(tmp_path, "Client/src/a.test.ts",
           lang.format(name="neu") + zwischen
           + _GEGLIEDERTER_TEST.format(name="zweit").replace("// Then: c", "// Then: d"))
    # // When / // Then leiht sich der erste Test die Gliederung des zweiten nicht
    assert qa.check_test_structure("frontend") == [
        ("Client/src/a.test.ts", "it('neu', () => {  →  fehlt: // Given, // When, // Then"),
    ]


def _fact(name: str, rumpf: str) -> str:
    return f"    [Fact]\n    public void {name}()\n    {{\n{rumpf}    }}\n"


_GEGLIEDERTER_RUMPF = "        // Given: a\n        // When: b\n        // Then: c\n"


def test_test_struktur_backend_rumpf_beginnt_nach_attribut_und_signatur(tmp_path, monkeypatch):
    # // Given eine bestehende gegliederte Methode, die ein [Fact] erst jetzt bekommt – das Attribut ist die
    #    einzige „+“-Zeile, die Klammer öffnet erst zwei Zeilen tiefer
    methode = "    public void M()\n    {\n" + _GEGLIEDERTER_RUMPF + "    }\n"
    _repo_mit_basis(tmp_path, monkeypatch, {"Server.Tests/T.cs": "public class T\n{\n" + methode + "}\n"})
    _write(tmp_path, "Server.Tests/T.cs", "public class T\n{\n    [Fact]\n" + methode + "}\n")
    # // When / // Then erreicht die Prüfung die Kommentare im Methodenrumpf
    assert qa.check_test_structure("backend") == []


def test_test_struktur_backend_rumpf_endet_an_der_methodenklammer(tmp_path, monkeypatch):
    # // Given ein neuer ungegliederter [Fact] vor einer gegliederten Bestands-Methode
    bestand = _fact("Alt", _GEGLIEDERTER_RUMPF)
    _repo_mit_basis(tmp_path, monkeypatch, {"Server.Tests/T.cs": "public class T\n{\n" + bestand + "}\n"})
    _write(tmp_path, "Server.Tests/T.cs",
           "public class T\n{\n" + _fact("Neu", "        var x = 1;\n") + bestand + "}\n")
    # // When / // Then zählt die Gliederung der nächsten Methode nicht für ihn
    assert qa.check_test_structure("backend") == [("Server.Tests/T.cs", "[Fact]  →  fehlt: // Given, // When, // Then")]


def test_struktur_fast_fail_nennt_jeden_befund_auf_eigener_zeile(tmp_path, monkeypatch):
    # // Given zwei neue Tests ohne Struktur
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    _write(tmp_path, "Client/src/a.test.ts", "it('a', () => {})\nit('b', () => {})\n")
    # // When / // Then
    assert qa.structure_fast_fail("frontend") == (
        "[qa-check] ❌ Test-Struktur (Given/When/Then) unvollständig – Abbruch vor Stryker, kein Übergabe-Hash:\n"
        "  Client/src/a.test.ts:  it('a', () => {})  →  fehlt: // Given, // When, // Then\n"
        "  Client/src/a.test.ts:  it('b', () => {})  →  fehlt: // Given, // When, // Then\n"
        "   Kommentare ergänzen, dann qa-check neu starten.")


# --- Test-Freigabe-Audit ---

def _blob(tmp_path, rel):
    return subprocess.run(["git", "hash-object", "-w", rel], cwd=tmp_path,
                          capture_output=True, text=True).stdout.strip()


def test_audit_zaehlt_jede_auffaelligkeit_und_nennt_jede_datei(tmp_path, monkeypatch):
    # // Given je zwei Testdateien: unverändert, geändert, geändert ohne Blob, ohne Freigabe –
    #    dazu eine freigegebene Datei, die nicht mehr geändert ist
    _repo_mit_basis(tmp_path, monkeypatch, {"Client/src/app.ts": "x\n"})
    namen = ["a1", "a2", "b1", "b2", "c1", "c2"]
    for n in namen:
        _write(tmp_path, f"Client/src/{n}.test.ts", f"it('{n}', () => 1)\n")
    freigabe = {f"Client/src/{n}.test.ts": _blob(tmp_path, f"Client/src/{n}.test.ts") for n in namen[:4]}
    for n in ("c1", "c2"):
        freigabe[f"Client/src/{n}.test.ts"] = subprocess.run(
            ["git", "hash-object", f"Client/src/{n}.test.ts"], cwd=tmp_path, capture_output=True, text=True
        ).stdout.strip()
    freigabe["Client/src/weg.test.ts"] = "0" * 40
    for n in ("b1", "b2", "c1", "c2"):
        _write(tmp_path, f"Client/src/{n}.test.ts", f"it('{n}', () => 2)\n")
    for n in ("d1", "d2"):
        _write(tmp_path, f"Client/src/{n}.test.ts", "it('d', () => 1)\n")
    # // When der Audit läuft
    befunde, zeilen = qa.audit_approved_tests("frontend", freigabe)
    # // Then zählt jede Abweichung (2 geändert, 2 ohne Blob, 2 ohne Freigabe) und jede Datei hat ihre Zeile
    assert befunde == 6
    diff_b1 = subprocess.run(["git", "diff", freigabe["Client/src/b1.test.ts"], "--", "Client/src/b1.test.ts"],
                             cwd=tmp_path, capture_output=True, text=True).stdout.rstrip()
    assert diff_b1.endswith("+it('b1', () => 2)")
    assert zeilen[0:2] == ["✅ Client/src/a1.test.ts: unverändert seit Freigabe.",
                           "✅ Client/src/a2.test.ts: unverändert seit Freigabe."]
    assert zeilen[2:4] == ["⚠️  Client/src/b1.test.ts: seit Freigabe GEÄNDERT – nur Setup (erlaubt) oder auch "
                           "Assertions (verboten)? Diff freigegeben→aktuell:", diff_b1]
    assert zeilen[7].startswith("⚠️  Client/src/c2.test.ts: seit Freigabe GEÄNDERT – der Freigabe-Blob ")
    assert zeilen[8:] == [
        "⚠️  Client/src/d1.test.ts: geändert, aber KEINE Freigabe-SHA übergeben – nie im Test-Review freigegeben?",
        "⚠️  Client/src/d2.test.ts: geändert, aber KEINE Freigabe-SHA übergeben – nie im Test-Review freigegeben?",
        "ℹ️  Client/src/weg.test.ts: freigegeben, taucht aber nicht unter den geänderten Test-Dateien auf "
        "(committet/zurückgesetzt?).",
    ]


# --- Report-Suche, Frische, Report-Hash ---

def _report_ablegen(wurzel: Path, schicht: str, zeitstempel: str, inhalt: str = "{}") -> Path:
    p = wurzel / "StrykerOutput" / schicht / zeitstempel / "reports" / "mutation-report.json"
    p.parent.mkdir(parents=True)
    p.write_text(inhalt, encoding="utf-8")
    return p


def test_report_suche_nimmt_den_neuesten_der_schicht(tmp_path, monkeypatch):
    # // Given je Schicht zwei Läufe (Stryker benennt die Ordner nach Zeitstempel)
    monkeypatch.chdir(tmp_path)
    for schicht in ("Backend", "Frontend"):
        _report_ablegen(tmp_path, schicht, "2026-11-01.10-00-00")
    _report_ablegen(tmp_path, "Backend", "2026-11-03.10-00-00")
    _report_ablegen(tmp_path, "Frontend", "2026-11-02.10-00-00")
    # // When / // Then liefert jede Schicht ihren neuesten Report, relativ zum Repo
    assert qa._find_report("backend") == Path("StrykerOutput/Backend/2026-11-03.10-00-00/reports/mutation-report.json")
    assert qa._find_report("frontend") == Path("StrykerOutput/Frontend/2026-11-02.10-00-00/reports/mutation-report.json")


def test_report_suche_ohne_report_liefert_none(tmp_path, monkeypatch):
    # // Given nur ein Backend-Report
    monkeypatch.chdir(tmp_path)
    _report_ablegen(tmp_path, "Backend", "2026-11-01.10-00-00")
    # // When / // Then findet die Frontend-Suche nichts
    assert qa._find_report("frontend") is None


def test_report_genau_an_der_toleranzgrenze_ist_frisch(tmp_path):
    # // Given ein Report, dessen mtime genau Lauf-Start minus Toleranz ist
    report = _report_ablegen(tmp_path, "Frontend", "x")
    start = 1_800_000_000.0
    grenze = start - qa._FRESHNESS_SLACK_SECONDS
    os.utime(report, (grenze, grenze))
    # // When / // Then gilt er noch als frisch
    assert qa._is_fresh(report, start) is True


_FIXTURE = Path(__file__).parent / "fixtures" / "qa_check_stryker_frontend_report.json"


def _report_hash(tmp_path, daten: dict) -> str:
    p = tmp_path / "r.json"
    p.write_text(json.dumps(daten), encoding="utf-8")
    return qa._parse_report(p)[2]


def test_report_hash_unabhaengig_von_reihenfolge_im_json(tmp_path):
    """StrykerJS schreibt Mutanten und Schlüssel nicht deterministisch geordnet."""
    # // Given ein echter Report und derselbe mit umgekehrter Mutanten- und Schlüsselreihenfolge
    daten = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    umgestellt = {k: daten[k] for k in reversed(list(daten))}
    for datei in umgestellt["files"].values():
        datei["mutants"] = [{k: m[k] for k in reversed(list(m))} for m in reversed(datei["mutants"])]
    # // When / // Then gleicher Hash
    assert _report_hash(tmp_path, umgestellt) == _report_hash(tmp_path, daten)


def test_report_hash_aendert_sich_mit_dem_inhalt(tmp_path):
    # // Given ein echter Report und derselbe mit einem Survivor weniger
    daten = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    vorher = _report_hash(tmp_path, daten)
    next(m for d in daten["files"].values() for m in d["mutants"] if m["status"] == "Survived")["status"] = "Killed"
    # // When / // Then anderer Hash
    assert _report_hash(tmp_path, daten) != vorher


def test_report_ohne_dateien_hat_keine_mutanten(tmp_path):
    # // Given ein Report ohne `files`-Schlüssel
    p = tmp_path / "r.json"
    p.write_text('{"schemaVersion": "1.0"}', encoding="utf-8")
    # // When / // Then: keine Dateien, kein valider Mutant
    files, metrics, _ = qa._parse_report(p)
    assert files == {}
    assert metrics["total_valid"] == 0


# --- Aufrufe der fremden Werkzeuge ---

class _Ergebnis:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


def _subprocess_aufzeichnen(monkeypatch, ergebnis: _Ergebnis) -> list:
    aufrufe = []
    monkeypatch.setattr(qa.subprocess, "run", lambda cmd, **kw: aufrufe.append((cmd, kw)) or ergebnis)
    return aufrufe


def test_stryker_lauf_waehlt_das_werkzeug_der_schicht(monkeypatch):
    # // Given ein aufzeichnender Subprozess, der mit Exit 7 endet
    aufrufe = _subprocess_aufzeichnen(monkeypatch, _Ergebnis(returncode=7))
    # // When Stryker für beide Schichten gestartet wird
    codes = [qa._run_stryker("backend"), qa._run_stryker("frontend")]
    # // Then läuft je das Schicht-Werkzeug im Repo-Wurzelverzeichnis, sein Exit-Code kommt zurück
    assert codes == [7, 7]
    assert aufrufe == [
        ([sys.executable, "-m", "prozesscode.dotnet-stryker"], {"cwd": str(qa._REPO_ROOT)}),
        ([sys.executable, "-m", "prozesscode.stryker-frontend"], {"cwd": str(qa._REPO_ROOT)}),
    ]


def test_tsc_gate_ruft_das_npm_script_typecheck(monkeypatch):
    # // Given ein aufzeichnender Subprozess
    aufrufe = _subprocess_aufzeichnen(monkeypatch, _Ergebnis(returncode=2))
    # // When / // Then
    assert qa.check_tsc() == 2
    assert aufrufe == [(["npm", "run", "typecheck"], {"cwd": str(qa._CLIENT_DIR)})]


_ADR_AUFRUF = ([sys.executable, "-m", "prozesscode.decisions", "check"],
               {"capture_output": True, "text": True, "cwd": str(qa._REPO_ROOT)})


def test_adr_check_gruen_gibt_die_zaehlzeile_weiter(monkeypatch):
    # // Given die echte Erfolgsausgabe von `decisions check`
    aufrufe = _subprocess_aufzeichnen(monkeypatch, _Ergebnis(stdout="✓ 333 ADR-Verweise im Code, alle gültig\n"))
    # // When / // Then
    assert qa.check_adr_refs() == ("✓ 333 ADR-Verweise im Code, alle gültig", 0)
    assert aufrufe == [_ADR_AUFRUF]


def test_adr_check_gruen_ohne_ausgabe_sagt_ok(monkeypatch):
    # // Given / When / Then
    _subprocess_aufzeichnen(monkeypatch, _Ergebnis())
    assert qa.check_adr_refs() == ("OK – keine Stale-Referenzen", 0)


def test_adr_check_rot_zeigt_jede_befundzeile_eingerueckt(monkeypatch):
    # // Given ein Befund im Ausgabeformat von `decisions check` (Spalten aus cmd_check) und eine
    #    stderr-Zeile
    stdout = ("Server/Foo.cs:12   ADR-S099-1      ✗ nicht gefunden\n\n"
              "333 ADR-Verweise im Code, davon 1 mit Befund (oben)\n")
    _subprocess_aufzeichnen(monkeypatch, _Ergebnis(returncode=1, stdout=stdout, stderr="Warnung\n"))
    # // When / // Then: Leerzeilen fallen weg, der Exit-Code bleibt
    assert qa.check_adr_refs() == (
        "Server/Foo.cs:12   ADR-S099-1      ✗ nicht gefunden\n"
        "  333 ADR-Verweise im Code, davon 1 mit Befund (oben)\n"
        "  Warnung", 1)


def test_adr_check_rot_ohne_ausgabe_sagt_es(monkeypatch):
    # // Given / When / Then
    _subprocess_aufzeichnen(monkeypatch, _Ergebnis(returncode=2, stdout="\n"))
    assert qa.check_adr_refs() == ("FEHLER (kein Output)", 2)


def test_eslint_ohne_geaenderte_ts_dateien_wird_uebersprungen(monkeypatch):
    # // Given nur Nicht-TypeScript-Dateien geändert
    gefragt = []
    monkeypatch.setattr(qa, "_changed_paths", lambda p: gefragt.append(p) or ["Client/src/a.css"])
    aufrufe = _subprocess_aufzeichnen(monkeypatch, _Ergebnis())
    # // When / // Then: kein ESLint-Lauf, -1 heißt übersprungen
    assert qa.check_eslint("frontend") == ("übersprungen (keine .ts/.tsx Dateien geändert)", -1)
    assert gefragt == [("Client/src/",)]
    assert aufrufe == []


def test_eslint_laeuft_bei_geaenderter_tsx_datei(monkeypatch):
    # // Given eine geänderte .tsx-Datei, eslint-run grün
    monkeypatch.setattr(qa, "_changed_paths", lambda _p: ["Client/src/App.tsx"])
    aufrufe = _subprocess_aufzeichnen(monkeypatch, _Ergebnis(stdout="✓ ESLint: keine Fehler\n"))
    # // When / // Then
    assert qa.check_eslint("frontend") == ("OK", 0)
    assert aufrufe == [([sys.executable, "-m", "prozesscode.eslint-run"],
                        {"capture_output": True, "text": True, "cwd": str(qa._REPO_ROOT)})]


def test_hash_haengt_am_inhalt_jedes_befunds():
    # // Given zwei Zustände mit gleich vielen, aber inhaltlich verschiedenen Befunden je Check
    basis = dict(layer="frontend", tree="t", report_hash="r", test_files=[], suppressions=[("a", "x")],
                 unit_tests=[("a", "x")], lint_code=0, test_structure=[("a", "x")], adr_code=0)
    # // When / // Then ändert jeder geänderte Befundinhalt den Hash
    for feld in ("suppressions", "unit_tests", "test_structure"):
        anders = {**basis, feld: [("a", "y")]}
        assert qa.compute_hash(**anders) != qa.compute_hash(**basis), feld
