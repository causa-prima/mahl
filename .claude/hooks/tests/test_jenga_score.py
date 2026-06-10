"""Tests für jenga_score.py – Finding-Parser (Slash- und Bindestrich-Kontexte)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import jenga_score as js  # noqa: E402


def test_finding_re_parses_slash_kontext():
    line = "- **[HOCH] [TOOLING] [Hook/Script] Titel**\n"
    m = js.FINDING_RE.match(line)
    assert m is not None
    assert m.group("kontext") == "Hook/Script"


def test_finding_re_parses_hyphen_kontext():
    line = "- **[MITTEL] [TOOLING] [Mutation-Testing] Titel**\n"
    m = js.FINDING_RE.match(line)
    assert m is not None
    assert m.group("kontext") == "Mutation-Testing"


def test_finding_re_parses_plain_kontext():
    line = "- **[GERING] [PROZESS] [Gherkin] Titel**\n"
    m = js.FINDING_RE.match(line)
    assert m is not None
    assert m.group("kategorie") == "PROZESS"
    assert m.group("kontext") == "Gherkin"
