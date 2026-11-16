"""Tests für checks/unsichtbare_zeichen.py – kein unsichtbares Zeichen als Literal in C#/TS-Tests.

CM-S047-1, Hotspot unsichtbare Zeichen: Ein `'\\u200B'` im Tool-Aufruf kommt schon im Hook-Input
als echtes, unsichtbares Zeichen an. Ein Editor, der es entfernt,
macht aus dem Test still einen Leer-String-Test. CGG-naming verlangt deshalb den
Codepunkt-Ausdruck. Der Check sieht, was der Hook-Input trägt: das Literal.

Die Testdaten selbst stehen als chr(…) – nach derselben Regel.
"""
import pytest

from conftest import make_input
from prozesscode.hooks.checks import unsichtbare_zeichen as uz

TS_TEST = "Client/src/pages/RecipesPage.test.tsx"
E2E = "Client/e2e/recipes.spec.ts"
CS_TEST = "Server.Tests/Domain/QuantityAmountTests.cs"

NULLBREITE = chr(0x200B)
NBSP = chr(0x00A0)
NEL = chr(0x0085)
WARNUNG = chr(0x26A0) + chr(0xFE0F)   # Warnzeichen plus Variationsselektor


@pytest.mark.parametrize("pfad, zeichen, beschreibung", [
    (TS_TEST, NULLBREITE, "U+200B ZERO WIDTH SPACE"),
    (E2E, NBSP, "U+00A0 NO-BREAK SPACE"),
    (CS_TEST, NEL, "U+0085 (Steuerzeichen)"),
])
def test_unsichtbares_zeichen_in_einem_test_wird_abgewiesen(pfad, zeichen, beschreibung):
    # Given
    inp = make_input(pfad, f"const eingabe = 'a{zeichen}b'\n")
    # When
    meldungen = uz.check(inp)
    # Then
    assert meldungen == [uz.MELDUNG.format(funde=f"  - Zeile 1: {beschreibung}")]


def test_jeder_fund_steht_mit_seiner_zeile_im_neuen_inhalt():
    # Given
    inp = make_input(TS_TEST, f"// Given\nconst a = '{NULLBREITE}'\nconst b = '{NBSP}{NBSP}'\n")
    # When
    meldungen = uz.check(inp)
    # Then – je Zeile und Zeichen ein Fund, Wiederholung in derselben Zeile einmal
    assert meldungen == [uz.MELDUNG.format(funde="  - Zeile 2: U+200B ZERO WIDTH SPACE\n"
                                                  "  - Zeile 3: U+00A0 NO-BREAK SPACE")]


def test_zeilentrenner_zeichen_zaehlen_nicht_als_zeilenende():
    """`splitlines()` trennt an U+2028 – der Fund verschwände samt Zeilennummer."""
    inp = make_input(TS_TEST, "a\nb" + chr(0x2028) + "c\n")
    assert uz.check(inp) == [uz.MELDUNG.format(funde="  - Zeile 2: U+2028 LINE SEPARATOR")]


def test_gewoehnlicher_leerraum_und_umlaute_sind_erlaubt():
    inp = make_input(CS_TEST, "\tvar s = \"Möhre  Öl\";\r\n// Given\n")
    assert uz.check(inp) == []


def test_emoji_bestandteile_sind_nicht_ausgenommen():
    """Bewusst ohne Emoji-Ausnahme: Ein Verbinder ohne Emoji ist die gefährliche Testeingabe,
    und eine Ausnahme nur für Variationsselektoren wäre inkonsistent (ZWJ, Keycap folgen
    derselben Logik). Ein Emoji im Test steht als Codepunkt-Ausdruck."""
    familie = chr(0x1F468) + chr(0x200D) + chr(0x1F469)
    inp = make_input(TS_TEST, f"expect(text).toBe('{WARNUNG} {familie}')\n")
    assert uz.check(inp) == [uz.MELDUNG.format(
        funde="  - Zeile 1: U+FE0F VARIATION SELECTOR-16\n  - Zeile 1: U+200D ZERO WIDTH JOINER")]


def test_byte_order_mark_am_anfang_wird_gemeldet():
    """Kein Test im Bestand trägt ein BOM (S149 geprüft) – eines wäre selbst eine Auffälligkeit,
    deshalb ohne Sonderfall."""
    inp = make_input(CS_TEST, chr(0xFEFF) + "public class T {}\n", tool="Write")
    assert uz.check(inp) == [uz.MELDUNG.format(funde="  - Zeile 1: U+FEFF ZERO WIDTH NO-BREAK SPACE")]


def test_codepunkt_ausdruck_ist_der_ausweg_und_wird_nicht_gemeldet():
    inp = make_input(TS_TEST, "const nullbreite = String.fromCodePoint(0x200B)\n")
    assert uz.check(inp) == []


@pytest.mark.parametrize("pfad", [
    "Client/src/pages/RecipesPage.tsx",          # Produktcode: nicht Gegenstand dieses Checks
    "Server/Domain/Recipe.cs",
    "tests/test_eslint_lint.py",                 # Python-Tests tragen „⚠️" in Meldungstexten
])
def test_ausserhalb_von_csharp_und_typescript_tests_wird_nicht_geprueft(pfad):
    assert uz.check(make_input(pfad, f"x = '{NULLBREITE}'\n")) == []
