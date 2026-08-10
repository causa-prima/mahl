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


def test_parse_zaehlt_beispiel_eintrag_im_header_kommentar_nicht_mit(tmp_path):
    """Der Datei-Header dokumentiert das Eintrags-Format mit einem Beispiel-Finding.

    Es steht in einem HTML-Kommentar und ist kein echtes Finding – zählte es mit,
    startete jede Periode bei 90 statt 100 und die Retro wäre ~2 Sessions zu früh fällig.
    Die Fixture enthält zusätzlich ein echtes Finding: Ein Fix, der pauschal alles
    verwirft, fällt damit ebenso auf wie gar kein Fix.
    """
    datei = tmp_path / "lessons_learned.md"
    datei.write_text(
        "# Lessons Learned\n"
        "\n"
        "<!--\n"
        "  Beispiel:\n"
        "  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash nicht killbar**\n"
        "    Regel: Content-Hash immer auf stabile Sortierung stützen.\n"
        "-->\n"
        "\n"
        "## Session 200 – 2026-01-01\n"
        "\n"
        "- **[MITTEL] [TOOLING] [Hook/Script] LL-S200-1 – echter Eintrag**\n",
        encoding="utf-8",
    )

    sessions, findings = js.parse(str(datei))

    assert sessions == 1
    assert [f["impact"] for f in findings] == ["MITTEL"]
