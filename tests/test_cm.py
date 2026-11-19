"""Tests für cm.py – Maßnahmen einzeln abrufen und auflisten (OBS-S136-2).

Gegen das echte Artefakt (CGP-echtes-artefakt): `countermeasures.md` hat Kopf, Vorlage im
Eintragsformat und drei Status-Abschnitte – genau die Form, an der ein Parser scheitern kann.
Die erwarteten IDs werden aus der Datei selbst gelesen, damit eine Retro die Tests nicht bricht.
"""
import re
from importlib import import_module

import pytest

from conftest import cli_aufruf

cm = import_module("prozesscode.cm")

_KOPFZEILE = re.compile(r"^### (CM-S\d{3}-\d+) ", re.M)


def _bestand() -> str:
    return cm.cm_path().read_text(encoding="utf-8")


def _status_von(text: str, cm_id: str) -> str:
    block = text[text.index(f"### {cm_id} "):]
    return re.search(r"\*\*Status:\*\*\s*([^|*]+?)\s*\|", block).group(1)


def _gelistete_ids(ausgabe: str) -> list[str]:
    return re.findall(r"^(CM-S\d{3}-\d+)\s", ausgabe, re.M)


@pytest.mark.aufrufpfad("cm")
def test_list_nennt_jede_massnahme_der_datei_genau_einmal(monkeypatch, capsys):
    # // Given die echte Maßnahmen-Datei
    erwartet = _KOPFZEILE.findall(_bestand())
    # // When alle Maßnahmen gelistet werden
    assert cli_aufruf(monkeypatch, cm, "list") == 0
    # // Then steht jede ID genau einmal da, auch die mit seltenem Status (OBSOLET)
    assert _gelistete_ids(capsys.readouterr().out) == erwartet


def test_list_zeigt_status_und_titel(monkeypatch, capsys):
    # // Given eine Maßnahme der echten Datei
    text = _bestand()
    cm_id = _KOPFZEILE.findall(text)[0]
    titel = re.search(rf"^### {cm_id} [–-] (.+)$", text, re.M).group(1).strip()
    # // When gelistet wird
    cli_aufruf(monkeypatch, cm, "list")
    # // Then trägt ihre Zeile Status und Titel
    [zeile] = [z for z in capsys.readouterr().out.splitlines() if z.startswith(cm_id)]
    assert _status_von(text, cm_id) in zeile
    assert zeile.endswith(titel)


def test_list_filtert_nach_status(monkeypatch, capsys):
    # // Given die echte Datei mit aktiven und bewährten Maßnahmen
    text = _bestand()
    aktiv = [i for i in _KOPFZEILE.findall(text) if _status_von(text, i) == "AKTIV"]
    # // When nur die aktiven gelistet werden (Groß-/Kleinschreibung egal)
    cli_aufruf(monkeypatch, cm, "list", "--status", "aktiv")
    # // Then stehen genau sie da
    assert _gelistete_ids(capsys.readouterr().out) == aktiv


def test_get_liefert_den_eintrag_bis_vor_die_naechste_ueberschrift(monkeypatch, capsys):
    # // Given zwei aufeinanderfolgende Maßnahmen
    erste, zweite = _KOPFZEILE.findall(_bestand())[:2]
    # // When die erste abgerufen wird
    assert cli_aufruf(monkeypatch, cm, "get", erste) == 0
    ausgabe = capsys.readouterr().out
    # // Then beginnt die Ausgabe mit ihrer Kopfzeile und endet vor der nächsten
    assert ausgabe.startswith(f"### {erste} ")
    assert f"### {zweite} " not in ausgabe
    assert "**Status:**" in ausgabe
    #   und ohne die Leerzeilen, die in der Datei vor der nächsten Überschrift stehen
    assert not ausgabe.endswith("\n\n")


def test_list_ohne_treffer_nennt_den_status_und_scheitert(monkeypatch, capsys):
    # // When nach einem Status gefiltert wird, den keine Maßnahme trägt
    assert cli_aufruf(monkeypatch, cm, "list", "--status", "VERTIPPT") == 1
    # // Then bleibt die Ausgabe leer, und die Fehlermeldung nennt den Status
    ausgabe = capsys.readouterr()
    assert ausgabe.out == ""
    assert "VERTIPPT" in ausgabe.err


def test_ohne_befehl_zeigt_die_befehle_statt_abzustuerzen(monkeypatch, capsys):
    # // When das Werkzeug ohne Befehl aufgerufen wird
    # // Then endet es als Bedienfehler (argparse), der die Befehle nennt
    assert cli_aufruf(monkeypatch, cm) == 2
    assert "list" in capsys.readouterr().err


def test_eintrag_ohne_statuszeile_wird_mit_fragezeichen_gelistet():
    # // Given ein Eintrag, dem die Statuszeile fehlt (Tippfehler in der Retro)
    text = "### CM-S001-1 – Ohne Status\n\nNur Text.\n"
    # // When er gelesen wird
    [(cm_id, titel, status, _block)] = cm.eintraege(text)
    # // Then bleibt er in der Liste, mit sichtbar unbekanntem Status
    assert (cm_id, titel, status) == ("CM-S001-1", "Ohne Status", "?")


def test_get_einer_unbekannten_id_nennt_den_weg_zur_liste(monkeypatch, capsys):
    # // When eine ID abgerufen wird, die es nicht gibt
    assert cli_aufruf(monkeypatch, cm, "get", "CM-S000-0") == 1
    # // Then sagt die Meldung, wie man die vorhandenen findet
    fehler = capsys.readouterr().err
    assert "CM-S000-0" in fehler
    assert "prozesscode.cm list" in fehler
