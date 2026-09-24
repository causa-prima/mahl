"""Aufrufpfad der lesenden Berichts-Werkzeuge: Argumente → `main()` → Ausgabe/Exit-Code.

Jedes Werkzeug hat eigene Tests für seinen Kern. Hier steht, was dort keiner prüft: dass die
Kommandozeile die Argumente tatsächlich an den Kern weiterreicht (LL-S128-1, CM-S133-1).
Wo ein Werkzeug fest verdrahtete Pfade liest, läuft der Test lesend gegen das echte Repo –
auch das ist der echte Pfad. Wo es `anchors.REPO_ROOT` nutzt, gegen ein Test-Repo.
"""
from importlib import import_module

import pytest

from conftest import cli_aufruf
from prozesscode.hooks.checks import guard_log


@pytest.fixture
def mini_repo(tmp_path, monkeypatch):
    anchors = import_module("prozesscode.anchors")
    monkeypatch.setattr(anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    return tmp_path


@pytest.mark.aufrufpfad("anchors")
def test_anchors_check_meldet_toten_verweis(mini_repo, monkeypatch, capsys):
    (mini_repo / "docs" / "a.md").write_text("Siehe [x](a.md#AAA-fehlt).\n", encoding="utf-8")
    code = cli_aufruf(monkeypatch, import_module("prozesscode.anchors"), "check")
    assert code == 1
    assert "AAA-fehlt" in capsys.readouterr().out


@pytest.mark.aufrufpfad("ordinale")
def test_ordinale_meldet_nummerierte_ueberschrift(mini_repo, monkeypatch, capsys):
    (mini_repo / "docs" / "a.md").write_text("# A\n\n## 3. Nachtrag\n", encoding="utf-8")
    code = cli_aufruf(monkeypatch, import_module("prozesscode.ordinale"))
    assert code == 1
    assert "3. Nachtrag" in capsys.readouterr().out


@pytest.mark.aufrufpfad("decisions")
def test_decisions_get_liefert_den_eintrag(monkeypatch, capsys):
    cli_aufruf(monkeypatch, import_module("prozesscode.decisions"), "get", "ADR-S100-1")
    assert "Autofokus im Dialog" in capsys.readouterr().out


@pytest.mark.aufrufpfad("doc")
def test_doc_toc_listet_die_anker_einer_datei(monkeypatch, capsys):
    code = cli_aufruf(monkeypatch, import_module("prozesscode.doc"),
                "toc", "docs/guidelines/coding-guideline-python.md")
    assert code == 0
    assert "CGP-echtes-artefakt" in capsys.readouterr().out


@pytest.mark.aufrufpfad("guard-stats")
def test_guard_stats_zaehlt_eine_ausloesung(monkeypatch, capsys):
    guard_log.protokolliere("check-anchors")  # conftest lenkt das Protokoll in tmp_path
    cli_aufruf(monkeypatch, import_module("prozesscode.guard-stats"))
    zeile = next(z for z in capsys.readouterr().out.splitlines() if "check-anchors" in z)
    assert "1" in zeile


@pytest.mark.aufrufpfad("retro_report")
def test_retro_report_liest_die_uebergebenen_pfade(tmp_path, monkeypatch, capsys):
    ll = tmp_path / "ll.md"
    ll.write_text("## Session 200 – 2026-01-01\n\n"
                  "- **[MITTEL] [PROZESS] [Doku] LL-S200-1 – Erster Fall**\n"
                  "- **[MITTEL] [PROZESS] [Doku] LL-S200-2 – Zweiter Fall**\n", encoding="utf-8")
    (tmp_path / "archiv").mkdir()
    code = cli_aufruf(monkeypatch, import_module("prozesscode.retro_report"), "--current", str(ll),
                "--archive", str(tmp_path / "archiv"), "--cm", str(tmp_path / "cm.md"))
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert "LL-S200-2 – Zweiter Fall" in ausgabe  # Kandidat aus genau dieser Datei


@pytest.mark.aufrufpfad("td_due")
def test_td_due_mit_unbekanntem_szenario_meldet_keinen_treffer(monkeypatch, capsys):
    cli_aufruf(monkeypatch, import_module("prozesscode.td_due"),
         "--szenarien", "Dieses Szenario gibt es nicht")
    assert "kein TD-Eintrag ankert" in capsys.readouterr().out


@pytest.mark.aufrufpfad("tracker")
def test_tracker_listet_die_erfassungswerkzeuge(monkeypatch, capsys):
    cli_aufruf(monkeypatch, import_module("prozesscode.tracker"))
    ausgabe = capsys.readouterr().out
    assert "obs" in ausgabe and "td" in ausgabe and "oq" in ausgabe


@pytest.mark.aufrufpfad("test-inventory")
def test_test_inventory_listet_testnamen_mit_filter(tmp_path, monkeypatch, capsys):
    datei = tmp_path / "test_x.py"
    datei.write_text("def test_alpha():\n    pass\n\n\ndef test_beta():\n    pass\n",
                     encoding="utf-8")
    cli_aufruf(monkeypatch, import_module("prozesscode.test-inventory"), str(datei), "--grep", "beta")
    ausgabe = capsys.readouterr().out
    assert "test_beta" in ausgabe and "test_alpha" not in ausgabe
