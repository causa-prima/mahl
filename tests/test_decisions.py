"""Tests für decisions.py – Erkennung von ADR-Referenzen im Code (OBS-S108-1).

Bislang gab es für `decisions.py` keine Tests, obwohl `check` als qa-check-Schritt 6 läuft.
Diese Datei deckt zunächst die Referenz-Erkennung ab: den Teil, dessen Lücke in run-7 einen
qa-check-Rerun kostete.

Kern der Lücke: Das alte Muster verlangte die ID **unmittelbar** nach `//` (nur Whitespace
dazwischen). Eine in Prosa eingebettete Referenz war damit unsichtbar – und Unsichtbarkeit
heißt hier „gilt als nicht vorhanden", also gerade kein Fehler, sondern stilles Grün.
"""
from importlib import import_module

from conftest import cli_aufruf

dec = import_module("prozesscode.decisions")


# --- der Fall, der schon immer funktionierte ---------------------------------
def test_id_directly_after_comment_marker():
    assert dec.adr_refs_in_line("// ADR-S111-1") == ["ADR-S111-1"]


def test_no_space_after_marker():
    assert dec.adr_refs_in_line("//ADR-S111-1") == ["ADR-S111-1"]


def test_suffix_variants_are_kept():
    assert dec.adr_refs_in_line("// ADR-S040-1-DEP") == ["ADR-S040-1-DEP"]
    assert dec.adr_refs_in_line("// ADR-S018-2-SUP") == ["ADR-S018-2-SUP"]


# --- die Lücke aus OBS-S108-1 -----------------------------------------------
def test_reference_embedded_in_prose_is_found():
    """`// siehe ADR-…` – das Wort dazwischen machte die Referenz vorher unsichtbar."""
    assert dec.adr_refs_in_line("// siehe ADR-S111-1") == ["ADR-S111-1"]


def test_all_references_in_one_comment_are_found():
    """Der run-7-Fall: zwei kombinierte ADRs, von denen vorher keine erfasst wurde."""
    line = "// Wertebasiert 200/409 nach ADR-S111-1 und ADR-S111-2, nicht 404."
    assert dec.adr_refs_in_line(line) == ["ADR-S111-1", "ADR-S111-2"]


def test_xml_doc_comment_is_a_comment_too():
    assert dec.adr_refs_in_line("/// Umsetzung von ADR-S051-2.") == ["ADR-S051-2"]


def test_trailing_comment_after_code():
    line = "    return Result.Ok(x);  // begründet in ADR-S111-3"
    assert dec.adr_refs_in_line(line) == ["ADR-S111-3"]


# --- Abgrenzungen ------------------------------------------------------------
def test_line_without_comment_yields_nothing():
    """Eine ID im Code (z.B. in einem String) ist keine Referenz-Auszeichnung."""
    assert dec.adr_refs_in_line('var tag = "ADR-S111-1";') == []


def test_id_before_the_comment_marker_is_not_a_reference():
    """Nur der Kommentarteil zählt – sonst würde Code-Text als Referenz gelesen."""
    assert dec.adr_refs_in_line('var s = "ADR-S001-1"; // kein ADR-Verweis hier') == []


def test_plain_line_yields_nothing():
    assert dec.adr_refs_in_line("public static int Foo() => 1;") == []


def test_malformed_ids_are_ignored():
    assert dec.adr_refs_in_line("// ADR-111-1 und ADR-SXXX-1") == []


# --- check: Befunde zeigen, Gültiges zählen (S133) ------------------------------------
# Gegen die echte adr.md; nur die Code-Verweise werden vorgegeben. ADR-S100-1 ist Accepted,
# ADR-S000-1 Superseded, ADR-S999-9 gibt es nicht.
def _check(monkeypatch, refs):
    monkeypatch.setattr(dec, "find_code_refs", lambda: refs)
    return cli_aufruf(monkeypatch, dec, "check")


def test_check_zeigt_bei_lauter_gueltigen_verweisen_nur_die_zaehlzeile(monkeypatch, capsys):
    """Bis S133 stand hier jede Fundstelle mit „✓ Accepted" – 195 Zeilen ohne einen Befund,
    die qa-check in jedem Übergabe-Lauf in den Subagenten-Kontext schrieb."""
    code = _check(monkeypatch, [("a.cs", 1, "ADR-S100-1"), ("b.cs", 2, "ADR-S100-1")])
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert ausgabe.strip().splitlines() == ["✓ 2 ADR-Verweise im Code, alle gültig"]


def test_check_zeigt_abgeloeste_adr_als_warnung_trotz_exit_0(monkeypatch, capsys):
    """⚠ ist kein Fehler, aber ein Befund – er darf beim Kürzen nicht mit wegfallen."""
    code = _check(monkeypatch, [("a.cs", 1, "ADR-S100-1"), ("b.cs", 7, "ADR-S000-1")])
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert "b.cs:7" in ausgabe and "ADR-S000-1" in ausgabe and "Superseded" in ausgabe
    assert "a.cs:1" not in ausgabe


def test_check_zeigt_unbekannte_adr_und_scheitert(monkeypatch, capsys):
    code = _check(monkeypatch, [("a.cs", 1, "ADR-S100-1"), ("c.cs", 3, "ADR-S999-9")])
    ausgabe = capsys.readouterr().out
    assert code == 1
    assert "c.cs:3" in ausgabe and "nicht gefunden" in ausgabe
    assert "a.cs:1" not in ausgabe
