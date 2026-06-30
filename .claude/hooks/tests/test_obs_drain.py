"""Tests für obs-drain.py – Drainable-Filter, Rate-Clamp, Alters-Lane, Kolokation, render (Drain-only)."""
import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "obs-drain.py")
_spec = importlib.util.spec_from_file_location("obs_drain", _path)
od = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(od)


def make(oid, status="NEU", impact="MITTEL", freq="gelegentlich", bezug="", title="T", files="`a.py`"):
    return f"""## {oid} – {title}
- Status: {status}
- Impact: {impact}    Häufigkeit: {freq}
- Beobachtung: irgendwas {files}
- Bezug: {bezug}
"""


def parse(*blocks):
    return od.parse_entries("\n".join(blocks))


def test_only_status_filters_drainable():
    # Nur der Status entscheidet (NEU = drainbar); ein Bezug (LL/OBS/CM) ist nur Querverweis.
    entries = parse(
        make("OBS-S090-1"),                                  # NEU -> drainbar
        make("OBS-S090-2", status="UMGESETZT (S091)"),       # erledigt -> raus
        make("OBS-S090-3", status="VERWORFEN (Grund)"),      # verworfen -> raus
        make("OBS-S090-4", status="IN BEOBACHTUNG"),         # geparkt -> raus
        make("OBS-S090-5", bezug="LL-S088-1"),               # LL-Bezug, aber NEU -> drainbar
    )
    _, _, b, drainable = od.compute(entries)
    assert b == 2
    assert {e["id"] for e in drainable} == {"OBS-S090-1", "OBS-S090-5"}


def test_in_beobachtung_geparkt_excluded():
    entries = parse(
        make("OBS-S090-1", status="NEU"),
        make("OBS-S090-2", status="IN BEOBACHTUNG – Pilot läuft"),  # geparkt -> raus
    )
    _, _, b, drainable = od.compute(entries)
    assert b == 1 and drainable[0]["id"] == "OBS-S090-1"


def test_rate_clamp_lower_upper():
    # B=3: round(0.4*3)=1, aber Clamp hebt auf Untergrenze 3 -> count=3 (echte Rate-Assertion, nicht nur b).
    wert, oldest, b, _ = od.compute(parse(*[make(f"OBS-S090-{i}") for i in range(1, 4)]))
    assert b == 3 and len(wert) + (1 if oldest else 0) == 3
    small = parse(*[make(f"OBS-S090-{i}") for i in range(1, 6)])                     # B=5
    wert, oldest, b, _ = od.compute(small)
    assert b == 5 and len(wert) + 1 == 3                                             # clamp lo=3
    big = parse(*[make(f"OBS-S09{i//10}-{i%10}") for i in range(10, 40)])            # B=30
    wert, oldest, b, _ = od.compute(big)
    assert len(wert) + 1 == 7                                                        # clamp hi=7


def test_backlog_boundaries_zero_one_two():
    # Die drei kleinsten Backlog-Größen haben eigene Pfade (rest[:0] bei B=1).
    assert od.compute(parse()) == ([], None, 0, [])                                  # B=0: leer-Branch
    wert, oldest, b, _ = od.compute(parse(make("OBS-S090-1")))                       # B=1
    assert b == 1 and oldest["id"] == "OBS-S090-1" and wert == []                    #   nur Alters-Lane
    wert, oldest, b, _ = od.compute(parse(make("OBS-S090-2"), make("OBS-S090-1")))   # B=2
    assert b == 2 and oldest["id"] == "OBS-S090-1"                                   #   kleineres sub = älter
    assert [e["id"] for e in wert] == ["OBS-S090-2"]                                 #   1 Wert + 1 Alters


def test_oldest_is_alters_lane():
    entries = parse(make("OBS-S093-2"), make("OBS-S085-9"), make("OBS-S085-3"))
    _, oldest, _, _ = od.compute(entries)
    assert oldest["id"] == "OBS-S085-3"  # gleiche Session, kleineres sub = früher erfasst


def test_value_lane_tiebreak_older_first():
    # Gleicher Impact×Häufigkeit -> älteres (kleinere session/sub) zuerst in der Wert-Lane.
    wert, oldest, _, _ = od.compute(parse(*[make(f"OBS-S09{i}-1") for i in range(0, 6)]))  # S090..S095
    assert oldest["id"] == "OBS-S090-1"
    assert [e["id"] for e in wert][:2] == ["OBS-S091-1", "OBS-S092-1"]


def test_colocation_same_file():
    entries = parse(
        make("OBS-S090-1", files="`docs/x.md`"),
        make("OBS-S090-2", files="`docs/x.md`"),  # gleiche Datei
        make("OBS-S090-3", files="`other.py`"),
    )
    _, _, _, drainable = od.compute(entries)
    a = next(e for e in drainable if e["id"] == "OBS-S090-1")
    assert {c["id"] for c in od.colocation(a, drainable)} == {"OBS-S090-2"}


def test_render_contains_lanes(monkeypatch):
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S090-2"), make("OBS-S085-1")))
    assert "=== OBS-Drain vorgeschlagen ===" in out
    assert "Wert-Lane" in out and "Alters-Lane" in out
    assert "OBS-S085-1" in out and "Alter ~11 Sessions" in out  # 96 - 85 = 11


def test_render_empty_backlog():
    assert "Backlog leer" in od.render(od.Path("."), parse())


def test_render_b1_no_empty_value_lane_header(monkeypatch):
    # B=1: nur Alters-Lane, KEIN leerer "Wert-Lane:"-Header.
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S090-1")))
    assert "Wert-Lane" not in out
    assert "Alters-Lane" in out and "OBS-S090-1" in out


def test_render_colocation_excludes_selected(monkeypatch):
    # +Koloc weist nur Items aus, die NICHT schon im Drain-Satz stehen.
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(
        make("OBS-S090-1", files="`f1.py`"),   # Alters-Lane, selektiert
        make("OBS-S090-2", files="`x.py`"),    # Wert-Lane, selektiert
        make("OBS-S090-3", files="`f3.py`"),   # Wert-Lane, selektiert
        make("OBS-S090-4", files="`x.py`"),    # teilt x.py mit -2, aber UNselektiert
    ))
    assert "+Koloc: OBS-S090-4" in out      # -2 weist das unselektierte -4 aus
    assert "+Koloc: OBS-S090-2" not in out  # kein selektiertes Item als Koloc


def test_due_parked_filters_and_sorts():
    # Fällig = geparkt UND Wiedervorlage erreicht (oder ohne Datum). Sortiert nach session/sub.
    entries = parse(
        make("OBS-S090-1", status="NEU"),                       # NEU -> nicht hier
        make("OBS-S085-4", status="IN BEOBACHTUNG bis S099"),   # noch geparkt
        make("OBS-S085-3", status="IN BEOBACHTUNG bis S096"),   # fällig (96>=96)
        make("OBS-S080-1", status="IN BEOBACHTUNG"),            # ohne Datum -> sofort fällig
    )
    due = od.due_parked(entries, cur=96)
    assert [e["id"] for e in due] == ["OBS-S080-1", "OBS-S085-3"]


def test_render_due_parked_resurfaces(monkeypatch):
    # Fällige geparkte Items tauchen wieder auf; noch nicht fällige bleiben weg.
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(
        make("OBS-S090-1"),                                     # NEU
        make("OBS-S085-3", status="IN BEOBACHTUNG bis S096"),   # fällig
        make("OBS-S085-4", status="IN BEOBACHTUNG bis S099"),   # noch geparkt
    ))
    assert "Fällige Wiedervorlagen" in out
    assert "OBS-S085-3" in out and "OBS-S085-4" not in out


def test_render_hygiene_reminder_for_resolved(monkeypatch):
    # Aufgelöste, noch nicht archivierte Items -> Hygiene-Reminder (aus Retro Section 10 hierher verschoben).
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(
        make("OBS-S090-1"),
        make("OBS-S088-1", status="UMGESETZT (S090)"),
    ))
    assert "ins Archiv verschieben" in out and "OBS-S088-1" in out


def test_render_overfull_backlog_warning(monkeypatch):
    # B > 12 (1,5× Gleichgewicht) -> sichtbare Überfüllungs-Warnung (Drain advisory, M-1).
    monkeypatch.setattr(od, "current_session", lambda root: 200)
    out = od.render(od.Path("."), parse(*[make(f"OBS-S1{i:02d}-1") for i in range(13)]))  # B=13
    assert "überfüllt" in out


def test_render_no_overfull_warning_when_healthy(monkeypatch):
    monkeypatch.setattr(od, "current_session", lambda root: 200)
    out = od.render(od.Path("."), parse(*[make(f"OBS-S1{i:02d}-1") for i in range(5)]))   # B=5
    assert "überfüllt" not in out


def test_render_b12_no_overfull_warning_fencepost(monkeypatch):
    # B=12 (genau an der Grenze; b>12 schlägt erst ab 13 an) -> noch KEINE Warnung.
    monkeypatch.setattr(od, "current_session", lambda root: 200)
    out = od.render(od.Path("."), parse(*[make(f"OBS-S1{i:02d}-1") for i in range(12)]))  # B=12
    assert "überfüllt" not in out


def test_render_resolved_only_is_not_empty_backlog(monkeypatch):
    # B=0, aber ein aufgelöstes (noch unarchiviertes) Item -> Hygiene-Reminder, nicht "Backlog leer".
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S088-1", status="UMGESETZT (S090)")))
    assert "Backlog leer" not in out
    assert "ins Archiv verschieben" in out and "OBS-S088-1" in out


def test_warn_far_parks_beyond_threshold(capsys):
    # Wiedervorlage > FAR_PARK Sessions voraus -> stderr-Warnung; an/unter der Schwelle: still.
    entries = parse(
        make("OBS-S085-1", status="IN BEOBACHTUNG bis S200"),   # 200-96 = 104 voraus -> Warnung
        make("OBS-S085-2", status=f"IN BEOBACHTUNG bis S{96 + od.FAR_PARK}"),  # genau Schwelle -> still
        make("OBS-S085-3", status="NEU"),                       # nicht geparkt -> ignoriert
    )
    od.warn_far_parks(entries, cur=96)
    err = capsys.readouterr().err
    assert "OBS-S085-1" in err and "bis S200" in err
    assert "OBS-S085-2" not in err


def test_warn_far_parks_silent_when_cur_none(capsys):
    # cur None (Alter unbestimmbar) -> keine Warnung (kein Fehlalarm).
    od.warn_far_parks(parse(make("OBS-S085-1", status="IN BEOBACHTUNG bis S200")), cur=None)
    assert capsys.readouterr().err == ""


def test_render_due_parked_without_neu(monkeypatch):
    # Auch ohne drainbare NEU-Items erscheinen fällige Wiedervorlagen (nicht "Backlog leer").
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S085-3", status="IN BEOBACHTUNG bis S096")))
    assert "Backlog leer" not in out
    assert "Fällige Wiedervorlagen" in out and "OBS-S085-3" in out
