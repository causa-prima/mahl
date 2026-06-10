"""Tests für retro_report.py – CM-Matching (volles Tripel, severity-exakt) und Finding-Parser."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import retro_report as rr  # noqa: E402


def _cm(schwere="HOCH", kategorie="AGENT", kontexte=None, status="AKTIV"):
    return rr.Countermeasure(
        problem="x", schwere=schwere, kategorie=kategorie,
        kontexte=kontexte if kontexte is not None else [], status=status,
    )


# --- cm_matches: Match auf das volle Tripel (Schwere exakt) -------------------
def test_cm_matches_full_tuple():
    cm = _cm(schwere="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.cm_matches(cm, "HOCH", "AGENT", "Review")


def test_cm_matches_requires_exact_severity():
    cm = _cm(schwere="HOCH", kategorie="AGENT", kontexte=["Review"])
    # MITTEL ≠ HOCH → bewusst kein Match (severity-agnostisch über-maskiert, s. Kommentar im Script)
    assert not rr.cm_matches(cm, "MITTEL", "AGENT", "Review")


def test_cm_matches_requires_kategorie():
    cm = _cm(schwere="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "PROZESS", "Review")


def test_cm_matches_wildcard_kontext_matches_any_kontext():
    cm = _cm(schwere="MITTEL", kategorie="PROZESS", kontexte=[])
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Tooling")
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Gherkin")


def test_cm_matches_kontext_not_in_list():
    cm = _cm(schwere="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "AGENT", "Tooling")


def test_has_cm_matches_full_tuple():
    cm = _cm(schwere="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.has_cm("HOCH", "AGENT", "Review", [cm])
    assert not rr.has_cm("MITTEL", "AGENT", "Review", [cm])


# --- Parser: Titel mit '*' (z.B. JSX-Kommentar) darf nicht durchfallen --------
def test_finding_re_parses_title_with_asterisk():
    line = "- **[GERING] [TOOLING] [Tooling] StrykerJS JSX-`{/* x */}`-Kommentar**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("schwere") == "GERING"
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
