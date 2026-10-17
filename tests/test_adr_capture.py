"""Tests für check-adr-capture.py – PreToolUse-Poka-Yoke gegen Aufschub in einer neuen ADR.

Regel: Eine ADR hält eine entschiedene Sache mit terminalem Rest fest. Ein Aufschub
(„machen wir später") verschwindet mit der Erledigung ersatzlos und gehört nach
`docs/tech-debt.md`. Geprüft werden nur **neu hinzukommende** ADR-Einträge; bestehende
bleiben frei änderbar, und ein `adr-ok`-Marker hebt die Prüfung für einen Eintrag auf.
"""
from importlib import import_module

import pytest
from conftest import git_repo

hook = import_module("prozesscode.hooks.check-adr-capture")


def _adr(aid: str, entscheidung: str = "X wird als Y modelliert.", extra: str = "") -> str:
    """Minimaler, formatgetreuer ADR-Block."""
    return (
        f"### {aid}: Kurztitel\n\n"
        "**Status:** Accepted\n"
        "**Tags:** scope:cross-cutting, arch:domain-type\n\n"
        f"**Entscheidung:** {entscheidung}\n\n"
        f"{extra}"
        "**Verworfen:** Die Alternative – aus Gründen.\n\n---\n\n"
    )


def _data(file_path: str, old: str, new: str) -> dict:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": old, "new_string": new},
    }


# --- is_adr_file -------------------------------------------------------------
def test_recognizes_adr_file_relative_and_absolute():
    assert hook.is_adr_file("docs/history/adr.md")
    assert hook.is_adr_file("/home/x/repo/docs/history/adr.md")


def test_ignores_other_files():
    assert not hook.is_adr_file("docs/tech-debt.md")
    assert not hook.is_adr_file("docs/history/decisions-archive.md")


# --- parse_adr_entries -------------------------------------------------------
def test_parses_entries_by_heading():
    content = _adr("ADR-S001-1") + _adr("ADR-S002-3")
    assert set(hook.parse_adr_entries(content)) == {"ADR-S001-1", "ADR-S002-3"}


def test_section_headings_are_not_entries():
    content = "## Domain-Typen & Sum-Types\n\n" + _adr("ADR-S001-1")
    assert set(hook.parse_adr_entries(content)) == {"ADR-S001-1"}


# --- deferral_hits -----------------------------------------------------------
@pytest.mark.parametrize("phrase", [
    "aufgeschoben", "vertagt", "vorerst", "vorläufig", "bis auf weiteres",
    "bis zur Erweiterung", "technische Schuld", "in diesem Zyklus nicht",
    "noch nicht implementiert", "später umgesetzt",
])
def test_detects_each_deferral_phrase(phrase):
    assert hook.deferral_hits(f"Das wird {phrase} und so weiter.")


@pytest.mark.parametrize("sentence", [
    "Aufgeschoben wird die volle Migration.",
    "Noch nicht implementiert ist der Schreibpfad.",
    "Vorerst bleibt es beim Lesepfad.",
])
def test_sentence_initial_capitalization_is_detected(sentence):
    # Deutsche Entscheidungsprosa schreibt satzinitial groß – ohne re.IGNORECASE
    # passierten genau diese Formulierungen die rein kleingeschriebenen Muster.
    assert hook.deferral_hits(sentence)


def test_reports_each_phrase_once_in_order():
    body = "vorerst aufgeschoben, vorerst nochmal"
    assert hook.deferral_hits(body) == ["vorerst", "aufgeschoben"]


def test_zunaechst_is_not_a_deferral_marker():
    # `zunächst` erzählt meist Vorgeschichte („X erzwang zunächst Y, dann entfernt") –
    # die Bauform der „Verworfen:"-Abschnitte. AGENTS.md-Katalog nennt es nicht.
    assert hook.deferral_hits("Der Override erzwang zunächst --locale=C und wurde entfernt.") == []


def test_terminal_decision_is_clean():
    body = "**Entscheidung:** Sum-Types nutzen `switch` mit `SumType.Unreachable<T>()`."
    assert hook.deferral_hits(body) == []


def test_yagni_and_minimal_are_not_deferral_markers():
    # Beide begründen häufig eine dauerhafte Entscheidung („wir bauen X nicht") –
    # als Marker wären sie Fehlalarm-Quellen.
    assert hook.deferral_hits("Bewusste YAGNI-Entscheidung: minimal modelliert.") == []


# --- find_violations ---------------------------------------------------------
def test_new_entry_with_deferral_is_reported():
    pre = _adr("ADR-S001-1")
    post = pre + _adr("ADR-S002-1", entscheidung="Y wird aufgeschoben.")
    assert hook.find_violations(pre, post) == [("ADR-S002-1", ["aufgeschoben"])]


def test_new_entry_without_deferral_passes():
    pre = _adr("ADR-S001-1")
    post = pre + _adr("ADR-S002-1")
    assert hook.find_violations(pre, post) == []


def test_existing_entry_may_carry_deferral():
    # Bestandseinträge bleiben änderbar – sonst wäre Aufräumen unmöglich.
    pre = _adr("ADR-S001-1", entscheidung="Y wird aufgeschoben.")
    post = _adr("ADR-S001-1", entscheidung="Y wird aufgeschoben, Detail ergänzt.")
    assert hook.find_violations(pre, post) == []


def test_adr_ok_marker_exempts_entry():
    pre = ""
    post = _adr("ADR-S002-1", entscheidung="Y ist vertagt. <!-- adr-ok: zitiert TD-S089-1 -->")
    assert hook.find_violations(pre, post) == []


# --- Session-Nummer neuer Einträge (OBS-S107-1) ------------------------------
# Ein Subagent mitten in der Session hat kein Signal für die laufende Session-Nummer – der
# Index zeigt die letzte ABGESCHLOSSENE – und setzt naiv die höchste bestehende ADR-Serie
# fort. In S106 legten zwei Subagenten so ADRs mit der Vorgänger-Session an; die Korrektur
# kostete eine Umnummerierung samt ~7 Code- und Doku-Referenzen (LL-S106-2).
def test_neuer_eintrag_mit_fremder_session_wird_gemeldet():
    pre = _adr("ADR-S105-3")
    post = pre + _adr("ADR-S105-4")
    assert hook.falsche_session(pre, post, 106) == ["ADR-S105-4"]


def test_neuer_eintrag_mit_laufender_session_passt():
    """Gegenprobe – ohne sie meldete der Check womöglich jeden neuen Eintrag."""
    pre = _adr("ADR-S105-3")
    post = pre + _adr("ADR-S106-1")
    assert hook.falsche_session(pre, post, 106) == []


def test_bestandseintrag_mit_alter_session_bleibt_unberuehrt():
    """Jeder Bestandseintrag trägt eine ältere Session – sonst wäre nichts mehr änderbar."""
    pre = _adr("ADR-S105-3")
    post = _adr("ADR-S105-3", entscheidung="Detail ergänzt.")
    assert hook.falsche_session(pre, post, 106) == []


def test_adr_ok_marker_exempts_session_check():
    post = _adr("ADR-S105-4", entscheidung="Nachtrag zur alten Serie. <!-- adr-ok -->")
    assert hook.falsche_session("", post, 106) == []


def test_unbekannte_session_prueft_nicht():
    """Ohne verlässliche Session-Nummer lieber gar nicht prüfen als falsch blocken."""
    assert hook.falsche_session("", _adr("ADR-S105-4"), None) == []


# --- check() – Dispatcher-Vertrag --------------------------------------------
def test_check_ignores_non_adr_file(tmp_path):
    target = tmp_path / "tech-debt.md"
    target.write_text("", encoding="utf-8")
    data = _data(str(target), "", "**Fällig:** jetzt – aufgeschoben")
    assert hook.check(data) is None


def test_check_ignores_other_tools(tmp_path):
    data = {"tool_name": "Read", "tool_input": {"file_path": "docs/history/adr.md"}}
    assert hook.check(data) is None


@pytest.mark.aufrufpfad("check-adr-capture")
def test_check_blocks_new_deferring_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "history"
    adr_dir.mkdir(parents=True)
    target = adr_dir / "adr.md"
    old = "# Architecture Decision Records\n"
    target.write_text(old, encoding="utf-8")

    new = old + _adr("ADR-S002-1", entscheidung="Volle Union bleibt aufgeschoben.")
    reason = hook.check(_data(str(target), old, new))

    assert reason is not None
    assert "ADR-S002-1" in reason
    assert "aufgeschoben" in reason
    assert "tech-debt.md" in reason


def test_check_blocks_new_deferring_adr_via_write(tmp_path):
    # Write ersetzt die ganze Datei – eigener Zweig in compute_post_content.
    adr_dir = tmp_path / "docs" / "history"
    adr_dir.mkdir(parents=True)
    target = adr_dir / "adr.md"
    target.write_text("# Architecture Decision Records\n", encoding="utf-8")

    content = "# Architecture Decision Records\n" + _adr(
        "ADR-S002-1", entscheidung="Der Rest bleibt vorerst so.")
    reason = hook.check({"tool_name": "Write",
                         "tool_input": {"file_path": str(target), "content": content}})

    assert reason is not None
    assert "ADR-S002-1" in reason


def test_adr_ok_in_one_entry_does_not_exempt_another(tmp_path):
    pre = ""
    post = (_adr("ADR-S002-1", entscheidung="Zitiert fremden Aufschub. <!-- adr-ok -->")
            + _adr("ADR-S002-2", entscheidung="Y bleibt aufgeschoben."))
    violations = hook.find_violations(pre, post)
    assert [aid for aid, _ in violations] == ["ADR-S002-2"]


def test_check_passes_terminal_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "history"
    adr_dir.mkdir(parents=True)
    target = adr_dir / "adr.md"
    old = "# Architecture Decision Records\n"
    target.write_text(old, encoding="utf-8")

    new = old + _adr("ADR-S002-1")
    assert hook.check(_data(str(target), old, new)) is None


# --- check(): laufende Session aus dem Repo der Datei --------------------------------
# Bisher prüften die Tests `falsche_session` nur mit vorgegebener Nummer; ob `check()` die
# Nummer aus dem Repo der Datei überhaupt ermittelt und durchreicht, war ungeprüft.
_HEADER = "# Architecture Decision Records\n"


@pytest.fixture
def repo_s139(tmp_path):
    git_repo(tmp_path, ["Abschluss\n\nSession-Ende: 138"])
    ziel = tmp_path / "docs" / "history" / "adr.md"
    ziel.parent.mkdir(parents=True)
    ziel.write_text(_HEADER, encoding="utf-8")
    return ziel


def test_laufende_session_aus_dem_repo_der_datei(repo_s139):
    assert hook._laufende_session(str(repo_s139)) == 139


def test_ohne_adr_datei_darueber_keine_session(tmp_path):
    assert hook._laufende_session(str(tmp_path / "irgendwo" / "adr.md")) is None


def test_check_blockt_adr_mit_fremder_session(repo_s139):
    grund = hook.check(_data(str(repo_s139), _HEADER, _HEADER + _adr("ADR-S138-1")))
    assert grund == f"{hook._KOPF_SESSION}  - ADR-S138-1\n{hook._HINWEIS_SESSION}"


def test_check_laesst_adr_der_laufenden_session_durch(repo_s139):
    assert hook.check(_data(str(repo_s139), _HEADER, _HEADER + _adr("ADR-S139-1"))) is None


def test_meldung_nennt_jede_aufschub_adr_mit_ihren_wendungen(repo_s139):
    neu = (_HEADER + _adr("ADR-S139-1", entscheidung="Bleibt vorerst so, Rest vertagt.")
           + _adr("ADR-S139-2", entscheidung="Bleibt aufgeschoben."))
    grund = hook.check(_data(str(repo_s139), _HEADER, neu))
    assert grund.split("\n")[:3] == [hook._KOPF_AUFSCHUB.rstrip("\n"),
                                     "  - ADR-S139-1: „vorerst“, „vertagt“",
                                     "  - ADR-S139-2: „aufgeschoben“"]
