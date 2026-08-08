"""Tests für decisions.py – Erkennung von ADR-Referenzen im Code (OBS-S108-1).

Bislang gab es für `decisions.py` keine Tests, obwohl `check` als qa-check-Schritt 6 läuft.
Diese Datei deckt zunächst die Referenz-Erkennung ab: den Teil, dessen Lücke in run-7 einen
qa-check-Rerun kostete.

Kern der Lücke: Das alte Muster verlangte die ID **unmittelbar** nach `//` (nur Whitespace
dazwischen). Eine in Prosa eingebettete Referenz war damit unsichtbar – und Unsichtbarkeit
heißt hier „gilt als nicht vorhanden", also gerade kein Fehler, sondern stilles Grün.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
dec = import_module("decisions")


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
