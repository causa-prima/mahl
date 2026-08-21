"""Tests für jenga_score.py – Finding-Parser (Slash- und Bindestrich-Kontexte) und Exit-Code."""
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


# --- Exit-Code: Report, kein Gate --------------------------------------------
# jenga_score.py ist ein Report-Script wie obs-drain.py oder td_due.py: Sein Befund steht
# im stdout, der Exit-Code sagt nur, ob der Lauf gelang. Meldete es „Retro fällig" per
# Exit ≠ 0, wertete ein generischer Aufrufer das als Ausfall – und das Script fiele genau
# dann aus, wenn es etwas zu melden hat.
def _lauf(tmp_path, findings: str) -> int:
    datei = tmp_path / "lessons_learned.md"
    datei.write_text("# Lessons Learned\n\n## Session 200 – 2026-01-01\n\n" + findings,
                     encoding="utf-8")
    sys.argv = ["jenga_score.py", "--file", str(datei)]
    return js.main()


def test_exit_code_is_zero_when_a_retro_is_due(tmp_path, capsys):
    code = _lauf(tmp_path, "- **[KRITISCH] [TOOLING] [Hook/Script] LL-1 – a**\n" * 5)
    ausgabe = capsys.readouterr().out
    assert "RETRO FÄLLIG" in ausgabe, "der Befund muss im stdout stehen"
    assert code == 0, "ein Report meldet seinen Befund im Text, nicht über den Exit-Code"


def test_exit_code_is_zero_when_the_score_is_healthy(tmp_path, capsys):
    assert _lauf(tmp_path, "") == 0
    assert "OK" in capsys.readouterr().out


def test_exit_code_is_nonzero_when_the_input_file_is_missing(tmp_path):
    """Gegenprobe: Der echte Fehlerfall muss weiterhin ≠ 0 liefern."""
    sys.argv = ["jenga_score.py", "--file", str(tmp_path / "fehlt.md")]
    assert js.main() != 0
