"""Tests für check-anchors.py – der PreToolUse-Hook um anchors.py herum.

Die Prüflogik (tote Verweise, falsche Pfade, verwaiste Anker) steht in test_anchors.py. Hier
steht der Hook-Vertrag über den Weg, den der Dispatcher nimmt: `check(payload)`.
"""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-anchors")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setattr(hook.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ziel.md").write_text(
        '# Ziel\n\n<a id="ZIE-da"></a>\n## Da\n\nText.\n', encoding="utf-8")
    return tmp_path


def _write(pfad, inhalt):
    return {"tool_name": "Write", "tool_input": {"file_path": str(pfad), "content": inhalt}}


@pytest.mark.aufrufpfad("check-anchors")
def test_verweis_ohne_ziel_blockt(repo):
    grund = hook.check(_write(repo / "docs" / "neu.md", "Siehe [tot](ziel.md#ZIE-weg).\n"))
    assert grund and "ZIE-weg" in grund


def test_verweis_mit_ziel_passiert(repo):
    """Gegenprobe: Der Block oben liegt am fehlenden Ziel, nicht am Verweis an sich."""
    assert hook.check(_write(repo / "docs" / "neu.md", "Siehe [da](ziel.md#ZIE-da).\n")) is None


def test_datei_ausserhalb_des_repos_geht_den_hook_nichts_an(repo, tmp_path_factory):
    draussen = tmp_path_factory.mktemp("draussen") / "neu.md"
    assert hook.check(_write(draussen, "Siehe [tot](ziel.md#ZIE-weg).\n")) is None


# --- tote Verweise ------------------------------------------------------------------
def test_tote_verweise_mit_zeile_auch_hinter_einer_ausnahme(repo):
    """Eine `anchor-ok`-Zeile fällt aus der Prüfung, verschiebt aber keine Zeilennummer."""
    inhalt = "[a](ziel.md#ZIE-weg1)\n[b](ziel.md#ZIE-weg2) anchor-ok\n[c](ziel.md#ZIE-weg3)\n"
    grund = hook.check(_write(repo / "docs" / "neu.md", inhalt))
    assert grund.split("\n")[:3] == [hook._KOPF_TOT.format(n=2).rstrip("\n"),
                                     "  - Zeile 1: `ZIE-weg1`", "  - Zeile 3: `ZIE-weg3`"]
    assert "weitere" not in grund


def test_tote_verweise_gedeckelt(repo, monkeypatch):
    monkeypatch.setattr(hook, "_MAX_HITS", 2)
    inhalt = "".join(f"[x](ziel.md#ZIE-weg{n})\n" for n in range(1, 4))
    grund = hook.check(_write(repo / "docs" / "neu.md", inhalt))
    assert "  - Zeile 2: `ZIE-weg2`" + hook._MEHR.format(n=1) + "\n" in grund
    assert "ZIE-weg3" not in grund


def test_genau_am_deckel_kein_nachsatz(repo, monkeypatch):
    monkeypatch.setattr(hook, "_MAX_HITS", 2)
    inhalt = "[x](ziel.md#ZIE-weg1)\n[x](ziel.md#ZIE-weg2)\n"
    assert "weitere" not in hook.check(_write(repo / "docs" / "neu.md", inhalt))


# --- verwaiste Anker -----------------------------------------------------------------
def test_anker_mit_verweis_von_aussen_darf_nicht_verschwinden(repo):
    (repo / "docs" / "quelle.md").write_text("Siehe [da](ziel.md#ZIE-da).\n", encoding="utf-8")
    grund = hook.check(_write(repo / "docs" / "ziel.md", "# Ziel\n\n## Da\n\nText.\n"))
    assert grund.split("\n")[:2] == [hook._KOPF_VERWAIST.rstrip("\n"),
                                     "  - `ZIE-da` ← docs/quelle.md:1"]


def test_anker_bleibt_trotz_ausnahmezeile_davor_erhalten(repo):
    """Die ausgeblendete Zeile davor darf die Ankerzeile nicht verändern."""
    (repo / "docs" / "quelle.md").write_text("Siehe [da](ziel.md#ZIE-da).\n", encoding="utf-8")
    neu = '# Ziel\n[x](ziel.md#ZIE-weg) anchor-ok\n<a id="ZIE-da"></a>\n## Da\n\nText.\n'
    assert hook.check(_write(repo / "docs" / "ziel.md", neu)) is None


# --- Link auf die falsche Datei ----------------------------------------------------------
def test_link_auf_die_falsche_datei(repo):
    (repo / "docs" / "dritte.md").write_text("Nichts.\n", encoding="utf-8")
    grund = hook.check(_write(repo / "docs" / "neu.md", "Siehe [da](dritte.md#ZIE-da).\n"))
    assert grund.split("\n")[:2] == [
        hook._KOPF_FALSCH.format(n=1).rstrip("\n"),
        "  - Zeile 1: `ZIE-da` verlinkt docs/dritte.md, liegt aber in docs/ziel.md"]


def test_falscher_link_in_einer_anderen_datei_blockt_nicht(repo):
    """Altlast in einer unbeteiligten Datei darf den Edit hier nicht sperren."""
    (repo / "docs" / "alt.md").write_text("Siehe [da](alt.md#ZIE-da).\n", encoding="utf-8")
    assert hook.check(_write(repo / "docs" / "neu.md", "Text.\n")) is None
