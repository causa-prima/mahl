"""Tests für commit_msg.py – Form des Abschluss-Commits.

Der Trailer `Session-Ende: <NNN>` vergibt jede Tracker-ID; eine vertippte oder doppelte Marke
bricht die Nummernableitung still. Der Hook prüft deshalb die Marke selbst, nicht nur die Länge.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

import commit_msg


def pruefe(text: str, erwartete_session=126, head_session=None):
    """Prüfung mit fest vorgegebenem Repo-Zustand – kein git-Aufruf im Test."""
    return commit_msg.befunde(text, erwartete_session=erwartete_session, head_session=head_session)


ABSCHLUSS = "Zutaten-Endpoint auf Domänentypen umgestellt\n\nWarum es nötig war.\n\nSession-Ende: 126\n"


# --- Betreff -----------------------------------------------------------------
def test_valid_closing_message_passes():
    assert pruefe(ABSCHLUSS) == []


def test_subject_over_72_chars_is_rejected():
    lang = "x" * 73
    assert any("Betreff" in b for b in pruefe(f"{lang}\n\nRumpf.\n\nSession-Ende: 126\n"))


def test_subject_of_exactly_72_chars_passes():
    assert pruefe(f"{'x' * 72}\n\nRumpf.\n\nSession-Ende: 126\n") == []


def test_empty_message_is_rejected():
    assert any("Betreff" in b for b in pruefe("\n\n\n"))


# --- Zwischen-Commits --------------------------------------------------------
def test_commit_without_trailer_needs_no_body():
    """Nicht jeder Commit beendet eine Session – ein Zwischen-Commit darf betrefflos bleiben."""
    assert pruefe("Tippfehler in doc.py\n") == []


# --- Trailer -----------------------------------------------------------------
def test_trailer_twice_is_rejected():
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\nSession-Ende: 126\n"
    assert any("genau einmal" in b for b in pruefe(text))


def test_wrong_session_number_is_rejected():
    """Der Fehler aus LL-S106-2: von der letzten abgeschlossenen Session weitergezählt."""
    befunde = pruefe("Titel\n\nRumpf.\n\nSession-Ende: 127\n")
    assert any("127" in b and "126" in b for b in befunde)


def test_amending_the_closing_commit_is_allowed():
    """Beim Nachbessern trägt HEAD die Nummer bereits – erwartet wäre sonst schon die nächste."""
    assert pruefe("Titel\n\nRumpf.\n\nSession-Ende: 126\n",
                  erwartete_session=127, head_session=126) == []


def test_trailer_without_body_is_rejected():
    """Die Marke allein ist keine Session-Historie."""
    assert any("Rumpf" in b for b in pruefe("Titel\n\nSession-Ende: 126\n"))


def test_misspelled_trailer_is_rejected():
    """Ohne gültige Marke ist eine fast-richtige Zeile ein Vertipper, kein Prosa-Satz."""
    assert any("Schreibweise" in b for b in pruefe("Titel\n\nRumpf.\n\nSession Ende: 126\n"))


def test_indented_trailer_is_rejected():
    assert any("Schreibweise" in b for b in pruefe("Titel\n\nRumpf.\n\n  Session-Ende: 126\n"))


def test_trailer_outside_the_last_block_is_rejected():
    """Git parst nur den LETZTEN Absatz als Trailer-Block. Steht die Marke davor, findet
    `--format='%(trailers:key=Session-Ende)'` sie nicht – die Nummer ist dann nur noch per
    grep erreichbar, und jeder dokumentierte Abrufbefehl liefert still leer."""
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\n\nCo-Authored-By: X <x@y>\n"
    assert any("letzten Absatz" in b for b in pruefe(text))


def test_trailer_together_with_other_trailers_passes():
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\nCo-Authored-By: X <x@y>\n"
    assert pruefe(text) == []


def test_prose_mention_alongside_a_valid_trailer_passes():
    """Ein Commit, der die Konvention beschreibt, nennt sie zwangsläufig im Fließtext."""
    text = ("Titel\n\nDer Trailer Session-Ende: <NNN> vergibt die Nummer.\n\nSession-Ende: 126\n")
    assert pruefe(text) == []


# --- Umgebung ----------------------------------------------------------------
def test_comment_lines_are_ignored():
    """git hängt Kommentare und den --verbose-Diff an die Vorlage an."""
    text = ("Titel\n\nRumpf.\n\nSession-Ende: 126\n"
            "# Bitte gib eine Commit-Beschreibung ein.\n"
            "# ------------------------ >8 ------------------------\n"
            "diff --git a/x b/x\n+Session-Ende: 999\n")
    assert pruefe(text) == []


def test_marker_waives_the_number_check():
    text = "Titel\n\nNachtrag zu einer alten Serie. session-ok\n\nSession-Ende: 99\n"
    assert pruefe(text) == []


def test_unknown_expected_session_skips_the_number_check():
    """Frisches Repo ohne Historie – die Nummer ist nicht prüfbar, die Form schon."""
    assert pruefe("Titel\n\nRumpf.\n\nSession-Ende: 1\n", erwartete_session=None) == []
