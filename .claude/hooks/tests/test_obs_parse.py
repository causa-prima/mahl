"""Tests für obs_parse.py – Eintrags-Parsing, Scoring, Status-Filter, Session-Zählung."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
import obs_parse as op


def make(oid, status="NEU", impact="MITTEL", freq="gelegentlich", bezug="", title="T", files="`a.py`"):
    return f"""## {oid} – {title}
- Status: {status}
- Impact: {impact}    Häufigkeit: {freq}
- Beobachtung: irgendwas {files}
- Bezug: {bezug}
"""


def parse(*blocks):
    return op.parse_entries("\n".join(blocks))


def test_fields_parsed():
    e = parse(make("OBS-S091-4", freq="dauerhaft", bezug="OBS-S085-1"))[0]
    assert e["id"] == "OBS-S091-4" and e["session"] == 91 and e["sub"] == 4
    assert e["status"] == "NEU" and e["impact"] == 2 and e["freq"] == 3
    assert e["bezug"] == "OBS-S085-1" and e["files"] == {"a.py"}


def test_impact_range_averaged():
    e = parse(make("OBS-S090-1", impact="MITTEL–HOCH (von GERING revidiert)"))[0]
    assert e["impact"] == 2.5  # MITTEL(2)+HOCH(3) /2, Klammer ignoriert


def test_unknown_frequency_falls_back(capsys):
    # Unbekannter Häufigkeits-Wert -> niedrigste Stufe (1.0) UND sichtbare Warnung (nicht still).
    e = parse(make("OBS-S090-1", freq="jeder Backend-RED"))[0]
    assert e["freq"] == 1.0
    assert "WARNUNG" in capsys.readouterr().err


def test_status_filters():
    assert op.is_parked("IN BEOBACHTUNG – Pilot") and not op.is_parked("NEU")
    assert op.is_resolved("UMGESETZT (S091)") and op.is_resolved("VERWORFEN (x)")
    assert not op.is_resolved("NEU")


def test_current_session_none_when_no_sessions(tmp_path):
    # Ohne Sessions-Verzeichnis ist das Alter unbestimmbar -> None (nicht 0-Sentinel).
    assert op.current_session(tmp_path) is None
    d = tmp_path / op.SESSIONS_DIR
    d.mkdir(parents=True)
    (d / "session_095.md").write_text("x", encoding="utf-8")
    assert op.current_session(tmp_path) == 96  # max(95) + 1


def test_current_session_ignores_nonmatching_filenames(tmp_path):
    # Dateien ohne parsbare Session-Nummer werden ignoriert (kein Crash); nur valide zählen.
    d = tmp_path / op.SESSIONS_DIR
    d.mkdir(parents=True)
    (d / "session_notes.md").write_text("x", encoding="utf-8")   # keine Nummer -> ignoriert
    (d / "session_090.md").write_text("x", encoding="utf-8")
    assert op.current_session(tmp_path) == 91
    # Nur nicht-parsbare Dateien -> None (Alter unbestimmbar), kein Fehlwert.
    bad = tmp_path / "br"
    (bad / op.SESSIONS_DIR).mkdir(parents=True)
    (bad / op.SESSIONS_DIR / "session_notes.md").write_text("x", encoding="utf-8")
    assert op.current_session(bad) is None


# --- Wiedervorlage (IN BEOBACHTUNG bis S<NNN>): geparkte Items mit Ablaufdatum ----------

def test_wiedervorlage_parsed():
    e = parse(make("OBS-S085-3", status="IN BEOBACHTUNG bis S096"))[0]
    assert e["wiedervorlage"] == 96


def test_wiedervorlage_absent_is_none():
    assert parse(make("OBS-S090-1", status="NEU"))[0]["wiedervorlage"] is None
    assert parse(make("OBS-S090-2", status="IN BEOBACHTUNG"))[0]["wiedervorlage"] is None


def test_wiedervorlage_embedded_in_prose():
    # Erster 'bis S<NNN>'-Treffer zählt, auch wenn Status-Prosa davor steht.
    e = parse(make("OBS-S085-4", status="IN BEOBACHTUNG – Pilot läuft, bis S100 neu bewerten"))[0]
    assert e["wiedervorlage"] == 100


def test_wiedervorlage_first_of_multiple_wins():
    # Mehrere 'bis S<NNN>' in einer Status-Zeile -> der ERSTE Treffer zählt (re.search).
    e = parse(make("OBS-S085-3", status="IN BEOBACHTUNG bis S095 bis S100"))[0]
    assert e["wiedervorlage"] == 95


def test_is_due_parked_by_date():
    e = parse(make("OBS-S085-3", status="IN BEOBACHTUNG bis S096"))[0]
    assert op.is_due_parked(e, cur=96)        # cur == bis -> fällig
    assert op.is_due_parked(e, cur=97)        # cur > bis  -> fällig
    assert not op.is_due_parked(e, cur=95)    # cur < bis  -> noch geparkt


def test_is_due_parked_dated_not_due_when_cur_none():
    # cur None (Alter unbestimmbar) -> datiertes Item bleibt geparkt, wird NICHT still fällig.
    e = parse(make("OBS-S085-3", status="IN BEOBACHTUNG bis S096"))[0]
    assert not op.is_due_parked(e, cur=None)


def test_is_due_parked_missing_date_is_due_with_warning(capsys):
    # Geparkt ohne 'bis S<NNN>' -> sofort fällig (kann nicht still verschwinden) + Warnung.
    e = parse(make("OBS-S085-12", status="IN BEOBACHTUNG"))[0]
    assert op.is_due_parked(e, cur=96)
    assert "WARNUNG" in capsys.readouterr().err


def test_is_due_parked_false_for_neu():
    e = parse(make("OBS-S090-1", status="NEU"))[0]
    assert not op.is_due_parked(e, cur=999)


# --- Robustheit (von FuncReview4 angefragt) ----------------------------------------------

def test_separate_line_impact_freq_degrades_freq(capsys):
    # Impact/Häufigkeit auf SEPARATEN Zeilen: Impact bleibt korrekt, Häufigkeit fällt auf 1.0 + Warnung.
    block = ("## OBS-S090-1 – T\n- Status: NEU\n- Impact: HOCH\n"
             "- Häufigkeit: dauerhaft\n- Bezug:\n")
    e = op.parse_entries(block)[0]
    assert e["impact"] == 3.0 and e["freq"] == 1.0
    assert "WARNUNG" in capsys.readouterr().err


def test_files_tokenizer_paths_and_non_files():
    # Backtick-Tokens: Pfade/Dateinamen werden erkannt, Nicht-Dateien (kein '/' / keine Endung) nicht.
    e = parse(make("OBS-S090-1", files="`docs/x.md` und `FooClass` und `b.py`"))[0]
    assert e["files"] == {"docs/x.md", "b.py"}
