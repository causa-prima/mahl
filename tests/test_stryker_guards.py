"""Tests für die Stryker-Fehlsignal-Guards (`_stryker_report.py`, `_stryker_target.py`).

Diese Guards sind der Grund, warum ein Mutations-Lauf nicht mehr „100 %" melden kann, ohne
etwas gemessen zu haben. Genau solche Sicherungen brechen still – deshalb hier festgenagelt.

Die `--mutate`-Fälle laufen gegen ein Verzeichnis unter `tmp_path`, das die Struktur des Repos
im Kleinen nachbildet (`Server/…`, `Client/src/…`): Die echten Ordner kopiert mutmut nicht in
den Mutantenbaum, und ein Test, der sie braucht, liefe dort nie – `_stryker_target` stand
deshalb bei 0 % Mutationsabdeckung.
"""
from importlib import import_module

import pytest

report = import_module("prozesscode._stryker_report")
target = import_module("prozesscode._stryker_target")


def _files(*statuses_per_file: list[str]) -> dict:
    """Baut einen minimalen Report-`files`-Block aus Status-Listen (eine Liste je Datei)."""
    return {
        f"/repo/Server/File{i}.cs": {
            "mutants": [
                {"id": str(n), "status": s, "mutatorName": "Equality", "replacement": "!=",
                 "location": {"start": {"line": n + 1, "column": 1}}}
                for n, s in enumerate(statuses)
            ]
        }
        for i, statuses in enumerate(statuses_per_file)
    }


# --- Null-Mutanten-Gate: ein Lauf ohne Messung ist kein bestandener Lauf --------------------
def test_report_nur_mit_ignored_und_compile_error_gilt_als_leer_und_faellt_durch():
    """Genau das Bild eines `--mutate`-Laufs auf einen Pfad, den Stryker als Excluded wertet."""
    leer = report.compute_metrics(_files(["Ignored", "CompileError"]))
    assert report.has_no_mutants(leer)
    assert leer["score"] is None  # nicht 100.0
    assert report.gate_code(leer) == 1  # nicht Exit 0, als wären es „100 %"
    assert report.format_score(leer) == "n/a (0 valide Mutanten)"


def test_voellig_leerer_report_faellt_durch():
    assert report.gate_code(report.compute_metrics({})) == 1


def test_nur_compile_error_lauf_faellt_durch_und_nennt_den_grund():
    """Alle Mutanten scheitern am TypeScript-Checker: StrykerJS meldet dafür einen NaN-Score
    und lässt ihn durchs eigene break-Threshold – hier muss es fehlschlagen."""
    nur_compile_errors = report.compute_metrics(_files(["CompileError", "CompileError"]))
    assert report.gate_code(nur_compile_errors) == 1
    assert (report.format_status_breakdown(nur_compile_errors)
            == "   Status-Verteilung: CompileError: 2")


def test_status_verteilung_ohne_mutanten_sagt_das_ausdruecklich():
    assert (report.format_status_breakdown(report.compute_metrics({}))
            == "   Status-Verteilung: keine Mutanten im Report.")


def test_status_verteilung_listet_jeden_status_alphabetisch():
    metriken = report.compute_metrics(_files(["Survived", "Ignored", "Killed", "Ignored"]))
    assert (report.format_status_breakdown(metriken)
            == "   Status-Verteilung: Ignored: 2, Killed: 1, Survived: 1")


# --- Score & Umfang -------------------------------------------------------------------------
def test_echte_hundert_prozent_ueber_valide_mutanten_passieren_das_gate():
    perfekt = report.compute_metrics(_files(["Killed", "Timeout"], ["Killed"]))
    assert report.gate_code(perfekt) == 0
    assert perfekt["score"] == 100.0  # Killed + Timeout zählen als detected
    assert perfekt["mutated_files"] == 2  # Umfang zählt Dateien mit validen Mutanten
    assert report.has_no_mutants(perfekt) is False


def test_ein_survivor_faellt_durch_und_zaehlt_in_den_nenner():
    mit_survivor = report.compute_metrics(_files(["Killed", "Survived"]))
    assert report.gate_code(mit_survivor) == 1
    assert mit_survivor["score"] == 50.0


def test_no_coverage_faellt_durch():
    """Nicht einmal ausgeführt – strenger genommen schlimmer als ein Survivor."""
    assert report.gate_code(report.compute_metrics(_files(["Killed", "NoCoverage"]))) == 1


def test_ignored_und_compile_error_bleiben_aus_dem_nenner():
    """Ignored darf den Score NICHT verwässern – sonst zögen Suppressions ihn hoch."""
    gemischt = report.compute_metrics(_files(["Killed", "Survived", "Ignored", "CompileError"]))
    assert gemischt["total_valid"] == 2


def test_datei_nur_mit_ignored_mutanten_zaehlt_nicht_zum_umfang():
    nur_ignored = report.compute_metrics(_files(["Killed"], ["Ignored"]))
    assert nur_ignored["mutated_files"] == 1


@pytest.mark.parametrize("status", ["Killed", "Timeout", "Survived", "NoCoverage"])
def test_jeder_valide_status_allein_macht_eine_datei_zum_umfang(status):
    assert report.compute_metrics(_files([status]))["mutated_files"] == 1


def test_metriken_vollstaendig_fuer_einen_gemischten_lauf():
    """Timeout zählt als detected: an einem Lauf mit Survivor sichtbar, wo es den Score ändert."""
    metriken = report.compute_metrics(
        _files(["Killed", "Timeout", "Survived"], ["NoCoverage", "Ignored"], ["CompileError"]))
    assert metriken == {
        "counts": {"Killed": 1, "Timeout": 1, "Survived": 1, "NoCoverage": 1, "Ignored": 1,
                   "CompileError": 1},
        "detected": 2,
        "undetected": 2,
        "total_valid": 4,
        "mutated_files": 2,
        "score": 50.0,
    }
    assert report.format_score(metriken) == "50.0%"
    assert report.format_scope(metriken) == "Umfang: 2 Datei(en)  |  4 valide Mutanten"


def test_datei_ohne_mutanten_feld_wird_uebersprungen():
    metriken = report.compute_metrics({"/repo/Server/Leer.cs": {}, **_files(["Killed"])})
    assert (metriken["total_valid"], metriken["mutated_files"]) == (1, 1)


# --- --mutate-Validierung: Abbruch statt stillem Leerlauf -----------------------------------
@pytest.fixture
def repo(tmp_path):
    """Repo im Kleinen: Server/ und Client/ mit je ein paar echten Dateinamen."""
    for datei in ("Server/Endpoints/IngredientsEndpoints.cs",
                  "Server/Middleware/ETagMiddleware.cs",
                  "Server/Types/NonEmptyTrimmedString.cs",
                  "Client/src/pages/IngredientsPage.tsx",
                  "Client/src/services/ingredientsApi.ts"):
        (tmp_path / datei).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / datei).write_text("", encoding="utf-8")
    return tmp_path


def _abbruch(capsys, roh: str, projekt, repo_root) -> str:
    """Ruft `resolve_mutate`, erwartet Exit 2 und gibt die Meldung auf stderr zurück."""
    with pytest.raises(SystemExit) as ende:
        target.resolve_mutate(roh, projekt, repo_root)
    assert ende.value.code == 2
    ausgabe = capsys.readouterr()
    assert ausgabe.out == ""
    return ausgabe.err


def test_repo_root_relativer_pfad_bricht_ab_und_schlaegt_den_projekt_relativen_vor(repo, capsys):
    meldung = _abbruch(capsys, "Server/Endpoints/IngredientsEndpoints.cs", repo / "Server", repo)
    assert meldung == (
        "⛔ --mutate-Muster trifft keine Datei: 'Server/Endpoints/IngredientsEndpoints.cs'\n"
        "   Basis ist Server/ (Stryker wertet die Muster projekt-relativ aus,\n"
        "   NICHT repo-root-relativ wie die meisten anderen Scripts hier).\n"
        "   Meintest du `Endpoints/IngredientsEndpoints.cs`? "
        "(Das Muster trifft repo-root-relativ, projekt-relativ nicht.)\n"
    )


def test_treffer_im_falschen_projekt_bekommt_keinen_korrekturvorschlag(repo, capsys):
    """Der Pfad trifft repo-root-relativ, liegt aber in Client/ – „meintest du" ginge ins Leere."""
    meldung = _abbruch(capsys, "Client/src/pages/IngredientsPage.tsx", repo / "Server", repo)
    assert meldung.endswith("NICHT repo-root-relativ wie die meisten anderen Scripts hier).\n")
    assert "Meintest du" not in meldung


def test_nicht_existierende_datei_bricht_ohne_korrekturvorschlag_ab(repo, capsys):
    meldung = _abbruch(capsys, "Domain/GibtsNicht.cs", repo / "Server", repo)
    assert meldung == (
        "⛔ --mutate-Muster trifft keine Datei: 'Domain/GibtsNicht.cs'\n"
        "   Basis ist Server/ (Stryker wertet die Muster projekt-relativ aus,\n"
        "   NICHT repo-root-relativ wie die meisten anderen Scripts hier).\n"
    )


@pytest.mark.parametrize("roh", ["src/pages/{A.tsx,B.tsx}", "src/{a.ts", "b.ts}"])
def test_brace_glob_bricht_ab_und_nennt_die_kommaliste(repo, capsys, roh):
    """Auch eine einzelne Klammer: Stryker hat sie aus einer Brace-Expansion herausgeschnitten."""
    meldung = _abbruch(capsys, roh, repo / "Client", repo)
    assert meldung == (
        f"⛔ Brace-Glob nicht unterstützt: {roh!r}\n"
        "   Stryker zerlegt die Liste am Komma – aus `src/{a.ts,b.ts}` werden die beiden\n"
        "   ungültigen Muster `src/{a.ts` und `b.ts}`, die nichts treffen.\n"
        "   Stattdessen als Kommaliste vollständiger Pfade schreiben: `src/a.ts,src/b.ts`\n"
    )


@pytest.mark.parametrize("roh", ["   ", " , ,"])
def test_leeres_mutate_bricht_ab(repo, capsys, roh):
    assert _abbruch(capsys, roh, repo / "Server", repo) == f"⛔ --mutate ist leer: {roh!r}\n"


def test_einzelne_gueltige_datei_passiert(repo):
    assert (target.resolve_mutate("Endpoints/IngredientsEndpoints.cs", repo / "Server", repo)
            == ["Endpoints/IngredientsEndpoints.cs"])


def test_kommaliste_wird_in_einzelmuster_zerlegt(repo):
    assert target.resolve_mutate(" Middleware/ETagMiddleware.cs,Types/NonEmptyTrimmedString.cs ",
                                 repo / "Server", repo) == ["Middleware/ETagMiddleware.cs",
                                                            "Types/NonEmptyTrimmedString.cs"]


def test_ein_fehlendes_muster_hinter_einem_gueltigen_bricht_trotzdem_ab(repo, capsys):
    meldung = _abbruch(capsys, "Middleware/ETagMiddleware.cs,Domain/GibtsNicht.cs",
                       repo / "Server", repo)
    assert "'Domain/GibtsNicht.cs'" in meldung


def test_glob_mit_treffern_passiert(repo):
    assert target.resolve_mutate("src/**/*.ts", repo / "Client", repo) == ["src/**/*.ts"]


def test_ausschlussmuster_darf_ins_leere_zeigen(repo):
    assert target.resolve_mutate("Endpoints/IngredientsEndpoints.cs,!Domain/GibtsNicht.cs",
                                 repo / "Server", repo) == ["Endpoints/IngredientsEndpoints.cs",
                                                            "!Domain/GibtsNicht.cs"]


def test_nach_einem_ausschlussmuster_wird_weiter_geprueft(repo, capsys):
    """Das Ausschlussmuster überspringt nur sich selbst, nicht die Prüfung der übrigen."""
    meldung = _abbruch(capsys, "!Domain/Alt.cs,Domain/GibtsNicht.cs", repo / "Server", repo)
    assert "'Domain/GibtsNicht.cs'" in meldung


def test_ausschlussmuster_auf_eine_vorhandene_datei_passiert(repo):
    assert (target.resolve_mutate("!src/pages/IngredientsPage.tsx", repo / "Client", repo)
            == ["!src/pages/IngredientsPage.tsx"])


def test_mutation_range_wird_vor_der_pruefung_abgetrennt_und_bleibt_im_muster(repo):
    """StrykerJS erlaubt `datei.ts:Zeile:Spalte-Zeile:Spalte`; geprüft wird nur der Dateiteil."""
    assert (target.resolve_mutate("src/services/ingredientsApi.ts:12:3-14:5", repo / "Client", repo)
            == ["src/services/ingredientsApi.ts:12:3-14:5"])


def test_absoluter_pfad_bricht_mit_meldung_ab_statt_mit_traceback(repo, capsys):
    """`Path.glob` lehnt absolute Muster mit NotImplementedError ab (Python 3.12) – ein Pfad,
    wie ihn ein Editor kopiert, endete so in einem Traceback statt in der Korrekturmeldung."""
    absolut = str(repo / "Client" / "src" / "pages" / "IngredientsPage.tsx")
    meldung = _abbruch(capsys, absolut, repo / "Client", repo)
    assert meldung.startswith(f"⛔ --mutate-Muster trifft keine Datei: {absolut!r}\n")


def test_nur_eine_mutation_range_ohne_datei_bricht_ab(repo, capsys):
    """Leerer Dateiteil ist ein ungültiges Glob – Abbruch mit Meldung statt Traceback."""
    meldung = _abbruch(capsys, ":12:3-14:5", repo / "Client", repo)
    assert meldung.startswith("⛔ --mutate-Muster trifft keine Datei: ':12:3-14:5'\n")
