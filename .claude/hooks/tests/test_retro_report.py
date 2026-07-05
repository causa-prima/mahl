"""Tests für retro_report.py – CM-Matching (volles Tripel, severity-exakt) und Finding-Parser."""
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import retro_report as rr  # noqa: E402


def _cm(impact="HOCH", kategorie="AGENT", kontexte=None, status="AKTIV"):
    return rr.Countermeasure(
        problem="x", impact=impact, kategorie=kategorie,
        kontexte=kontexte if kontexte is not None else [], status=status,
    )


# --- cm_matches: Match auf das volle Tripel (Impact exakt) -------------------
def test_cm_matches_full_tuple():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.cm_matches(cm, "HOCH", "AGENT", "Review")


def test_cm_matches_requires_exact_severity():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    # MITTEL ≠ HOCH → bewusst kein Match (severity-agnostisch über-maskiert, s. Kommentar im Script)
    assert not rr.cm_matches(cm, "MITTEL", "AGENT", "Review")


def test_cm_matches_requires_kategorie():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "PROZESS", "Review")


def test_cm_matches_wildcard_kontext_matches_any_kontext():
    cm = _cm(impact="MITTEL", kategorie="PROZESS", kontexte=[])
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Tooling")
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Gherkin")


def test_cm_matches_kontext_not_in_list():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "AGENT", "Tooling")


def test_has_cm_matches_full_tuple():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.has_cm("HOCH", "AGENT", "Review", [cm])
    assert not rr.has_cm("MITTEL", "AGENT", "Review", [cm])


# --- Parser: Titel mit '*' (z.B. JSX-Kommentar) darf nicht durchfallen --------
def test_finding_re_parses_title_with_asterisk():
    line = "- **[GERING] [TOOLING] [Tooling] StrykerJS JSX-`{/* x */}`-Kommentar**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("impact") == "GERING"
    assert "JSX" in m.group("titel")


def test_finding_re_parses_plain_title():
    line = "- **[HOCH] [PROZESS] [TDD] Ganz normaler Titel ohne Sonderzeichen**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("titel") == "Ganz normaler Titel ohne Sonderzeichen"


def test_finding_re_parses_slash_kontext():
    line = "- **[HOCH] [TOOLING] [Bash/Permission] Irgendein Titel**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("kontext") == "Bash/Permission"


# --- load_cm: Fließtext-Format (OBS-S085-14) ---------------------------------
_CM_SAMPLE = textwrap.dedent("""\
    # Countermeasures

    ## Aktive Maßnahmen

    ### CM-S070-3 – Multi-Kontext-Maßnahme
    **Impact:** HOCH | **Kategorie:** TOOLING | **Kontext:** Bash/Permission, Mutation-Testing | **Status:** AKTIV | **Seit:** S070
    **Problem:** Tatsächlicher Problemtext, nicht der Titel
    **Maßnahme:** irgendwas

    ### CM-S047-1 – Wildcard-Kontext
    **Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** – | **Status:** AKTIV | **Seit:** S047
    **Problem:** P
    **Maßnahme:** M

    ## Bewährte Maßnahmen

    ### CM-S078-2 – Offene Maßnahme
    **Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Skill-Nutzung | **Status:** OFFEN | **Seit:** S078
    **Problem:** P2
    **Maßnahme:** M2
    """)


def _write_cm(tmp_path):
    p = tmp_path / "countermeasures.md"
    p.write_text(_CM_SAMPLE, encoding="utf-8")
    return str(p)


def test_load_cm_parses_ids_and_fields(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert [c.cm_id for c in cms] == ["CM-S070-3", "CM-S047-1", "CM-S078-2"]
    first = cms[0]
    assert first.impact == "HOCH"
    assert first.kategorie == "TOOLING"
    assert first.status == "AKTIV"
    assert first.seit_session == 70


def test_load_cm_splits_multi_kontext(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert cms[0].kontexte == ["Bash/Permission", "Mutation-Testing"]


def test_load_cm_dash_kontext_is_wildcard(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    wildcard = next(c for c in cms if c.cm_id == "CM-S047-1")
    assert wildcard.kontexte == []  # – → leer → Wildcard (matcht jeden Kontext)
    assert rr.cm_matches(wildcard, "HOCH", "PROZESS", "BeliebigerKontext")


def test_load_cm_problem_line_overrides_title(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert cms[0].problem == "Tatsächlicher Problemtext, nicht der Titel"


def test_load_cm_parses_status_across_sections(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    offen = next(c for c in cms if c.cm_id == "CM-S078-2")
    assert offen.status == "OFFEN"


# --- archive_start_sessions: speist die CM-Eskalation (Section 9) -------------

def test_archive_start_sessions(tmp_path):
    d = tmp_path / "archive"
    d.mkdir()
    for s in (70, 78, 85):
        (d / f"session_{s:03d}_to_{s + 8:03d}.md").write_text("x", encoding="utf-8")
    (d / "README.md").write_text("x", encoding="utf-8")  # Nicht-Pattern-Datei wird ignoriert
    assert sorted(rr.archive_start_sessions(str(d))) == [70, 78, 85]
