"""Tests für checks/guard_log.py – Auslöse-Protokoll der Guards.

Drei Zusagen: Jede Auslösung landet mit Guard-Namen und Zeitstempel im Protokoll, ein
Schreibfehler reißt den Guard nie mit (fail-open), und die Auswertung übersteht kaputte
Zeilen. Wozu das Protokoll dient und warum es nicht rückwirkend aus den Session-Logs
gelesen wird: im Modul-Docstring.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from checks import guard_log


def test_eine_ausloesung_landet_als_zeile(tmp_path, monkeypatch):
    ziel = tmp_path / "guard-triggers.jsonl"
    monkeypatch.setattr(guard_log, "LOG", ziel)
    guard_log.protokolliere("check-anchors")
    eintraege = [json.loads(z) for z in ziel.read_text(encoding="utf-8").splitlines()]
    assert len(eintraege) == 1
    assert eintraege[0]["guard"] == "check-anchors"
    assert eintraege[0]["ts"]


def test_mehrere_ausloesungen_haengen_an(tmp_path, monkeypatch):
    ziel = tmp_path / "guard-triggers.jsonl"
    monkeypatch.setattr(guard_log, "LOG", ziel)
    guard_log.protokolliere("a")
    guard_log.protokolliere("b")
    guard_log.protokolliere("a")
    assert [json.loads(z)["guard"] for z in ziel.read_text().splitlines()] == ["a", "b", "a"]


def test_ein_schreibfehler_reisst_den_guard_nicht_mit(tmp_path, monkeypatch):
    """Fail-open, und zwar zwingend: Das Protokoll ist Beiwerk. Würde ein volles Dateisystem
    einen blockierenden Guard zum Absturz bringen, hätte die Messung den Mechanismus
    beschädigt, den sie überwachen soll."""
    monkeypatch.setattr(guard_log, "LOG", tmp_path / "gibt-es-nicht" / "tief" / "x.jsonl")
    monkeypatch.setattr(guard_log.Path, "mkdir",
                        lambda *_a, **_k: (_ for _ in ()).throw(OSError("kein Platz")))
    guard_log.protokolliere("check-anchors")   # darf nicht werfen


def test_der_zaehlstand_liest_zurueck_was_geschrieben_wurde(tmp_path, monkeypatch):
    ziel = tmp_path / "guard-triggers.jsonl"
    monkeypatch.setattr(guard_log, "LOG", ziel)
    for name in ("a", "b", "a", "a"):
        guard_log.protokolliere(name)
    assert guard_log.zaehlstand() == {"a": 3, "b": 1}


def test_zaehlstand_ohne_datei_ist_leer(tmp_path, monkeypatch):
    monkeypatch.setattr(guard_log, "LOG", tmp_path / "noch-nichts.jsonl")
    assert guard_log.zaehlstand() == {}


def test_kaputte_zeilen_kippen_die_auswertung_nicht(tmp_path, monkeypatch):
    """Ein abgebrochener Schreibvorgang darf nicht den ganzen Bestand unlesbar machen."""
    ziel = tmp_path / "guard-triggers.jsonl"
    ziel.write_text('{"ts": "x", "guard": "a"}\nkein json\n{"ts": "y", "guard": "a"}\n')
    monkeypatch.setattr(guard_log, "LOG", ziel)
    assert guard_log.zaehlstand() == {"a": 2}


def test_beobachtet_seit_nennt_den_aeltesten_eintrag(tmp_path, monkeypatch):
    """Ohne Zeitraum ist „nie gefeuert" wertlos – am ersten Tag hat nichts gefeuert."""
    ziel = tmp_path / "guard-triggers.jsonl"
    ziel.write_text('{"ts": "2026-08-01T10:00:00", "guard": "a"}\n'
                    '{"ts": "2026-09-01T10:00:00", "guard": "a"}\n')
    monkeypatch.setattr(guard_log, "LOG", ziel)
    assert guard_log.beobachtet_seit() == "2026-08-01T10:00:00"


def test_beobachtet_seit_ohne_daten_ist_none(tmp_path, monkeypatch):
    monkeypatch.setattr(guard_log, "LOG", tmp_path / "leer.jsonl")
    assert guard_log.beobachtet_seit() is None
