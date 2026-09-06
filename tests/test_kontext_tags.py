"""Tests für kontext_tags.py – die Tag-Liste als eine Quelle.

Drei Zusagen:
  1. Die erlaubten Tags stammen aus der Tabelle in `process.md`, nicht aus einer Kopie im
     Code – ein dort ergänzter Tag ist ohne Code-Edit gültig.
  2. Ist die Tabelle nicht auffindbar, scheitert das Modul LAUT. Eine leere Liste wäre der
     schlimmere Ausgang: Der Prüfer liefe weiter und meldete nie einen Verstoß.
  3. `unbekannte` unterscheidet erlaubte Tags, Mehrfach-Tags und Vorlagen-Platzhalter von
     echten Verstößen – sonst trägt sein grünes Ergebnis nichts.
"""
from importlib import import_module

import pytest

kontext_tags = import_module("prozesscode.kontext_tags")


TABELLE = """## Kontext-Tags

| Tag | Bedeutung |
|-----|-----------|
| `TDD` | Test-first-Disziplin |
| `Hook/Script` | Projekt-Automatisierung |
| `Sonstiges` | Passt in keinen anderen Tag |

## Nächster Abschnitt
"""


def schreibe_process(root, inhalt: str):
    ziel = root / "docs" / "kaizen"
    ziel.mkdir(parents=True)
    (ziel / "process.md").write_text(inhalt, encoding="utf-8")
    return root


# --- Quelle ------------------------------------------------------------------
def test_tags_kommen_aus_der_tabelle(tmp_path):
    root = schreibe_process(tmp_path, TABELLE)
    assert kontext_tags.erlaubte(root) == ("TDD", "Hook/Script", "Sonstiges")


def test_ergaenzter_tag_gilt_ohne_code_edit(tmp_path):
    erweitert = TABELLE.replace("| `Sonstiges` |", "| `Frisch` | neu |\n| `Sonstiges` |")
    root = schreibe_process(tmp_path, erweitert)
    assert "Frisch" in kontext_tags.erlaubte(root)


def test_echte_process_md_traegt_die_tabelle():
    """Gegen den realen Bestand – ein umformatierter Abschnitt fällt hier auf."""
    tags = kontext_tags.erlaubte()
    assert "Sonstiges" in tags and "Hook/Script" in tags


# --- Lauter Ausfall statt stiller ---------------------------------------------
def test_fehlender_abschnitt_scheitert_laut(tmp_path):
    root = schreibe_process(tmp_path, "# process\n\n## Etwas anderes\n")
    with pytest.raises(kontext_tags.TabelleFehlt):
        kontext_tags.erlaubte(root)


def test_leere_tabelle_scheitert_laut(tmp_path):
    root = schreibe_process(tmp_path, "## Kontext-Tags\n\nnoch nichts\n\n## Weiter\n")
    with pytest.raises(kontext_tags.TabelleFehlt):
        kontext_tags.erlaubte(root)


def test_fehlende_datei_scheitert_laut(tmp_path):
    with pytest.raises(kontext_tags.TabelleFehlt):
        kontext_tags.erlaubte(tmp_path)


# --- Prüfung ------------------------------------------------------------------
ERLAUBT = ("TDD", "Hook/Script", "Sonstiges")


def test_erlaubter_tag_ist_kein_verstoss():
    assert kontext_tags.unbekannte("TDD", ERLAUBT) == []


def test_erfundener_tag_ist_ein_verstoss():
    """Die Gegenprobe zum Test darüber: Ohne sie belegt ein grünes Ergebnis nichts."""
    assert kontext_tags.unbekannte("Kaizen", ERLAUBT) == ["Kaizen"]


def test_mehrfach_tags_werden_einzeln_geprueft():
    assert kontext_tags.unbekannte("Hook/Script, tech-debt", ERLAUBT) == ["tech-debt"]


@pytest.mark.parametrize("roh", ["–", "-", "", "KONTEXT", "<Tags oder –>",
                                 "<Kontext-Tag wie in lessons_learned>"])
def test_vorlagen_platzhalter_sind_kein_verstoss(roh):
    assert kontext_tags.unbekannte(roh, ERLAUBT) == []
