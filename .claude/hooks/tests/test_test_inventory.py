"""Tests für _test_inventory.py – Testnamen samt Zeilenbereich aus C#- und TS-Testdateien.

Der Zeilenbereich ist der eigentliche Zweck: Er macht den Folge-Read gezielt statt vollständig.
Deshalb prüfen die Tests nicht nur, dass Namen gefunden werden, sondern dass Anfang UND Ende
stimmen – auch wenn Klammern in Zeichenketten oder Kommentaren stehen.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from _test_inventory import block_ende, inventar, parse_csharp, parse_typescript


def _lines(text: str) -> list[str]:
    return text.strip("\n").splitlines()


# --- block_ende --------------------------------------------------------------
def test_finds_the_closing_brace():
    lines = _lines("""
def foo() {
    tue_was();
}
danach
""")
    assert block_ende(lines, 0) == 2


def test_braces_inside_string_literals_do_not_shift_the_end():
    lines = _lines("""
it('zeigt {geschweift}', () => {
    expect(x).toBe('}');
});
""")
    assert block_ende(lines, 0) == 2


def test_braces_in_line_comments_are_ignored():
    lines = _lines("""
it('foo', () => {
    // hier fehlt bewusst eine Klammer: {
    expect(x).toBe(1);
});
""")
    assert block_ende(lines, 0) == 3


def test_declaration_without_a_block_stays_single_line():
    assert block_ende(_lines("nur text\nweiter"), 0) == 1


# --- C# ----------------------------------------------------------------------
CS = """
public class Tests
{
    [Fact]
    public async Task Erster_Test()
    {
        Assert.True(true);
    }

    [Theory]
    [InlineData(1)]
    public void Zweiter_Test(int n)
    {
        Assert.Equal(1, n);
    }

    public void KeinTest()
    {
        Hilfsmethode();
    }
}
"""


def test_csharp_finds_fact_and_theory():
    eintraege = parse_csharp(_lines(CS))
    assert [e.name for e in eintraege] == ["Erster_Test", "Zweiter_Test"]


def test_csharp_range_starts_at_the_attribute_and_ends_at_the_closing_brace():
    erster = parse_csharp(_lines(CS))[0]
    assert (erster.start, erster.end) == (3, 7)


def test_csharp_skips_attributes_between_marker_and_signature():
    """`[Theory]` gefolgt von `[InlineData]` – die Signatur kommt erst danach."""
    zweiter = parse_csharp(_lines(CS))[1]
    assert zweiter.name == "Zweiter_Test"
    assert (zweiter.start, zweiter.end) == (9, 14)


def test_csharp_ignores_methods_without_a_test_attribute():
    assert "KeinTest" not in [e.name for e in parse_csharp(_lines(CS))]


# --- TypeScript --------------------------------------------------------------
TS = """
describe('Suite A', () => {
  it('tut etwas', () => {
    expect(1).toBe(1);
  });

  it.each([1, 2])('parametrisiert %i', (n) => {
    expect(n).toBeGreaterThan(0);
  });
});

test('freistehend', () => {
  expect(true).toBe(true);
});
"""


def test_typescript_separates_suites_from_tests():
    eintraege = parse_typescript(_lines(TS))
    assert [(e.name, e.ist_suite) for e in eintraege] == [
        ("Suite A", True),
        ("tut etwas", False),
        ("parametrisiert %i", False),
        ("freistehend", False),
    ]


def test_typescript_nesting_depth_comes_from_indentation():
    eintraege = parse_typescript(_lines(TS))
    assert eintraege[0].tiefe == 0
    assert eintraege[1].tiefe == 1
    assert eintraege[3].tiefe == 0


def test_typescript_suite_range_spans_all_its_tests():
    suite = parse_typescript(_lines(TS))[0]
    assert (suite.start, suite.end) == (1, 9)


def test_typescript_handles_modifiers_like_it_each():
    namen = [e.name for e in parse_typescript(_lines(TS))]
    assert "parametrisiert %i" in namen


def test_zeilen_counts_inclusive():
    erster_test = parse_typescript(_lines(TS))[1]
    assert (erster_test.start, erster_test.end) == (2, 4)
    assert erster_test.zeilen == 3


# --- inventar ----------------------------------------------------------------
def test_inventar_dispatches_by_suffix(tmp_path):
    cs = tmp_path / "T.cs"
    cs.write_text(CS, encoding="utf-8")
    ts = tmp_path / "t.test.tsx"
    ts.write_text(TS, encoding="utf-8")
    assert len(inventar(cs)) == 2
    assert len(inventar(ts)) == 4


def test_inventar_returns_empty_for_unknown_suffixes(tmp_path):
    other = tmp_path / "readme.md"
    other.write_text("# nichts", encoding="utf-8")
    assert inventar(other) == []


def test_inventar_is_sorted_by_start_line(tmp_path):
    ts = tmp_path / "t.test.ts"
    ts.write_text(TS, encoding="utf-8")
    starts = [e.start for e in inventar(ts)]
    assert starts == sorted(starts)


# --- Gegen die echten Projektdateien -----------------------------------------
def test_real_project_files_are_parsed(tmp_path):
    """Regression gegen die tatsächlich vorhandenen Testdateien – die Muster sollen an
    echtem Code halten, nicht nur an konstruierten Schnipseln."""
    repo = Path(__file__).resolve().parents[3]
    for pfad, mindestens in (("Server.Tests/IngredientsEndpointsTests.cs", 20),
                             ("Client/src/pages/IngredientsPage.test.tsx", 20)):
        datei = repo / pfad
        if not datei.exists():
            continue
        tests = [e for e in inventar(datei) if not e.ist_suite]
        assert len(tests) >= mindestens, f"{pfad}: nur {len(tests)} Tests erkannt"
        assert all(e.end >= e.start for e in tests)
