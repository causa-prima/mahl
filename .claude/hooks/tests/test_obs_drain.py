"""Tests für obs-drain.py – Drainable-Filter, Rate-Clamp, Alters-Lane, Kolokation, render (Drain-only)."""
import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "obs-drain.py")
_spec = importlib.util.spec_from_file_location("obs_drain", _path)
od = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(od)


def make(oid, status="NEU", impact="MITTEL", freq="häufig", bezug="", title="T", files="`a.py`",
         zusammen=""):
    # Default MITTEL × häufig = Score 2 = gerade behandlungswürdig, damit Tests, die nicht das
    # Scoring prüfen, Einträge in der Wert-Lane sehen.
    return f"""## {oid} – {title}
- Status: {status}
- Impact: {impact}    Häufigkeit: {freq}
- Beobachtung: irgendwas {files}
- Bezug: {bezug}
- Zusammen-erledigen: {zusammen}
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


def ids(einheiten):
    """Flache ID-Liste über Einheiten (jede Einheit ist eine Liste von Einträgen)."""
    return [e["id"] for u in einheiten for e in u]


# --- Wert-Lane: behandlungswürdige Einheiten, gedeckelt auf die Session-Kapazität ---------
# Die frühere Rate clamp(round(0.4*B), 3, 7) ist entfallen (S122): Sie war an die Backlog-GRÖSSE
# gekoppelt und damit an eine Zahl, die nichts über den enthaltenen Wert sagt – ein Backlog aus
# lauter Bagatellen erzeugte denselben Sieben-Satz wie eines voller schwerer Befunde.
def test_value_lane_only_takes_behandlungswuerdige():
    wert, _, _, _ = od.compute(parse(
        make("OBS-S090-1", impact="HOCH", freq="dauerhaft"),      # 12
        make("OBS-S090-2", impact="MITTEL", freq="gelegentlich"), # 1  -> unter der Schwelle
        make("OBS-S090-3", impact="GERING", freq="dauerhaft"),    # 0  -> folgenlos
    ))
    assert ids(wert) == ["OBS-S090-1"]


def test_value_lane_is_not_capped():
    # Der Satz zeigt ALLES Behandlungswürdige. Ein Deckel begrenzte nur den Vorschlag, nicht die
    # Arbeit – er versteckte sie. Verdauliche Portionen macht der Skill, nicht dieser Satz.
    wert, _, _, _ = od.compute(parse(*[make(f"OBS-S09{i}-1") for i in range(0, 9)]))
    assert len(ids(wert)) == 9


def test_value_lane_sorted_by_unit_score_then_age():
    wert, _, _, _ = od.compute(parse(
        make("OBS-S090-1", impact="MITTEL", freq="häufig"),      # 2
        make("OBS-S091-1", impact="HOCH", freq="dauerhaft"),     # 12
        make("OBS-S092-1", impact="HOCH", freq="gelegentlich"),  # 3
    ))
    assert ids(wert) == ["OBS-S091-1", "OBS-S092-1", "OBS-S090-1"]


# --- Cluster: Einheiten über das `Zusammen-erledigen:`-Feld ------------------------------------------
def test_cluster_merges_related_entries_into_one_unit():
    wert, _, _, _ = od.compute(parse(
        make("OBS-S090-1", impact="MITTEL", freq="gelegentlich", zusammen="OBS-S090-2"),
        make("OBS-S090-2", impact="MITTEL", freq="gelegentlich"),
    ))
    # Einzeln je 1 (unter der Schwelle) – zusammen 2 und damit behandlungswürdig.
    assert len(wert) == 1 and set(ids(wert)) == {"OBS-S090-1", "OBS-S090-2"}


def test_cluster_is_transitive():
    wert, _, _, _ = od.compute(parse(
        make("OBS-S090-1", zusammen="OBS-S090-2"),
        make("OBS-S090-2", zusammen="OBS-S090-3"),
        make("OBS-S090-3"),
    ))
    assert len(wert) == 1 and len(ids(wert)) == 3


def test_cluster_warns_about_a_dead_edge(capsys):
    # Ein Ziel, das nicht mehr drainbar ist, verwirft cluster() – korrekt, aber es darf nicht
    # STUMM geschehen: Die Kante entsteht zwangsläufig, sobald der Partner archiviert wird,
    # und ein lautloser Ausfall wäre von "nie eine Kante gehabt" nicht unterscheidbar.
    od.cluster(od.compute(parse(
        make("OBS-S090-1", zusammen="OBS-S088-1"),
        make("OBS-S088-1", status="UMGESETZT (S089)"),
    ))[3])
    err = capsys.readouterr().err
    assert "OBS-S090-1" in err and "OBS-S088-1" in err


def test_cluster_is_silent_without_dead_edges(capsys):
    od.cluster(od.compute(parse(make("OBS-S090-1", zusammen="OBS-S090-2"),
                                make("OBS-S090-2", zusammen="OBS-S090-1")))[3])
    assert capsys.readouterr().err == ""


def test_cluster_ignores_links_to_non_drainable():
    # Verwandtschaft zu einem erledigten Eintrag ist als Kontext wertvoll, bildet aber keine
    # Einheit – sonst addierte ein längst gelöster Eintrag Score zu einem offenen.
    wert, _, _, _ = od.compute(parse(
        make("OBS-S090-1", zusammen="OBS-S088-1"),
        make("OBS-S088-1", status="UMGESETZT (S089)"),
    ))
    assert len(wert) == 1 and ids(wert) == ["OBS-S090-1"]


def test_gering_cluster_stays_below_threshold():
    # Fünf folgenlose Einträge sind zusammen immer noch folgenlos (GERING = 0).
    wert, _, _, _ = od.compute(parse(*[
        make(f"OBS-S090-{i}", impact="GERING", freq="dauerhaft", zusammen="OBS-S090-1")
        for i in range(1, 6)]))
    assert wert == []


# --- Alters-Lane: alle über ALT_AB, sonst das älteste --------------------------------------
def test_alters_lane_takes_all_beyond_threshold():
    entries = parse(
        make("OBS-S080-1", impact="GERING"), make("OBS-S081-1", impact="GERING"),
        make("OBS-S099-1", impact="GERING"),
    )
    _, alt, _, _ = od.compute(entries, cur=100)   # ALT_AB=15 -> S080/S081 sind 20/19 alt
    assert [e["id"] for e in alt] == ["OBS-S080-1", "OBS-S081-1"]


def test_alters_lane_falls_back_to_single_oldest():
    entries = parse(make("OBS-S093-2", impact="GERING"), make("OBS-S085-9", impact="GERING"),
                    make("OBS-S085-3", impact="GERING"))
    _, alt, _, _ = od.compute(entries, cur=95)    # keiner älter als 15
    assert [e["id"] for e in alt] == ["OBS-S085-3"]  # gleiche Session, kleineres sub = früher


def test_alters_lane_excludes_entries_already_in_value_lane():
    entries = parse(make("OBS-S080-1", impact="HOCH", freq="dauerhaft"))
    wert, alt, _, _ = od.compute(entries, cur=100)
    assert ids(wert) == ["OBS-S080-1"] and alt == []


def test_alters_lane_without_current_session():
    # cur None (Alter unbestimmbar) -> Rückfall auf "das älteste", nie auf "alle".
    _, alt, _, _ = od.compute(parse(make("OBS-S080-1", impact="GERING"),
                                    make("OBS-S099-1", impact="GERING")), cur=None)
    assert [e["id"] for e in alt] == ["OBS-S080-1"]


def test_backlog_boundaries_zero_one():
    assert od.compute(parse())[2] == 0
    wert, alt, b, _ = od.compute(parse(make("OBS-S090-1", impact="GERING")), cur=95)
    assert b == 1 and ids(wert) == [] and [e["id"] for e in alt] == ["OBS-S090-1"]


# --- Trigger: beansprucht der Drain die Session? -------------------------------------------
# Ersetzt "B >= 13" (S117). Die Backlog-Zahl misst Menge, nicht Wert – ein Berg aus Bagatellen
# beanspruchte damit dieselbe Session wie ein Satz schwerer Befunde.
def test_trigger_fires_on_value():
    entries = parse(make("OBS-S090-1", impact="HOCH", freq="dauerhaft"))  # 12 >= 9
    assert od.triggers(entries, cur=95) is True


def test_trigger_silent_below_value_threshold():
    entries = parse(make("OBS-S090-1", impact="HOCH", freq="häufig"))     # 6 < 9
    assert od.triggers(entries, cur=95) is False


def test_trigger_caps_at_top_n_units():
    # Beliebig viele MITTEL×häufig (je 2) dürfen NICHT auslösen: Top-5 gedeckelt = 10 ... aber
    # 5*2=10 >= 9 wäre ein Fehltrigger. Deshalb hier die kleinste Klasse: MITTEL×gelegentlich (1).
    entries = parse(*[make(f"OBS-S0{90+i}-1", impact="MITTEL", freq="gelegentlich")
                      for i in range(0, 9)])
    assert od.triggers(entries, cur=95) is False   # Top-5-Summe = 5 < 9


def test_trigger_fires_on_age_even_without_value():
    # Die Alters-Lane hängt sonst am Wert-Trigger: ohne eigenen Auslöser könnten Bagatellen
    # unbegrenzt wachsen, weil nie ein Drain liefe, der sie herausholt.
    entries = parse(*[make(f"OBS-S08{i}-1", impact="GERING") for i in range(0, 5)])
    assert od.triggers(entries, cur=100) is True


def test_trigger_silent_with_few_old_entries():
    entries = parse(*[make(f"OBS-S08{i}-1", impact="GERING") for i in range(0, 3)])  # 3 < 4
    assert od.triggers(entries, cur=100) is False


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
    out = od.render(od.Path("."), parse(
        make("OBS-S090-2"),                     # behandlungswürdig -> Wert-Lane
        make("OBS-S085-1", impact="GERING"),    # folgenlos -> nur über die Alters-Lane
    ))
    assert out.startswith("OBS-Drain – Backlog:")  # selbsterklärend ohne Rahmenzeile
    assert "Wert-Lane" in out and "Alters-Lane" in out
    assert "OBS-S085-1" in out and "Alter ~11 Sessions" in out  # 96 - 85 = 11


def test_render_empty_backlog():
    assert "Backlog leer" in od.render(od.Path("."), parse())


# --- Vorprägungs-Marker (OBS-S112-8) -----------------------------------------
# Das Feld ist beim normalen `get` verborgen, damit es die Kandidatenbildung nicht prägt.
# Genau dadurch kann es vergessen werden – deshalb muss der Drain-Satz auf seine Existenz
# hinweisen, analog zum `+Koloc:`-Marker.
def test_parse_flags_an_entry_with_vorpraegung():
    entries = parse(make("OBS-S090-1") + "- Vorprägung: Ansatz Z.\n")
    assert entries[0]["vorpraegung"] is True


def test_parse_flags_absence_too():
    assert parse(make("OBS-S090-1"))[0]["vorpraegung"] is False


def test_render_marks_entries_with_vorpraegung(monkeypatch):
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S090-1") + "- Vorprägung: Ansatz Z.\n"))
    assert "+Vorprägung" in out


def test_render_leaves_plain_entries_unmarked(monkeypatch):
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    assert "+Vorprägung" not in od.render(od.Path("."), parse(make("OBS-S090-1")))


# Offene Fragen sind seit S117 kein Teil dieses Scripts mehr (eigenes Modul
# `open_questions.py`, Tests in `test_open_questions.py`).


def test_render_no_empty_value_lane_header(monkeypatch):
    # Nichts Behandlungswürdiges: nur Alters-Lane, KEIN leerer "Wert-Lane:"-Header.
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(make("OBS-S090-1", impact="GERING")))
    assert "Wert-Lane" not in out
    assert "Alters-Lane" in out and "OBS-S090-1" in out


def test_render_colocation_excludes_selected(monkeypatch):
    # +Koloc weist nur Items aus, die NICHT schon im Drain-Satz stehen. Unselektiert bleibt, was
    # weder behandlungswürdig noch das älteste ist.
    monkeypatch.setattr(od, "current_session", lambda root: 96)
    out = od.render(od.Path("."), parse(
        make("OBS-S090-1", impact="HOCH", freq="dauerhaft", files="`x.py`"),  # Wert-Lane
        make("OBS-S090-2", files="`f2.py`"),                                  # Wert-Lane
        make("OBS-S089-1", impact="GERING", files="`alt.py`"),                # Alters-Lane (ältestes)
        make("OBS-S090-9", impact="GERING", files="`x.py`"),   # teilt x.py mit -1, in keiner Lane
    ))
    assert "+Koloc: OBS-S090-9" in out      # -1 weist das unselektierte -9 aus
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


def test_render_reports_the_backlog_size_without_a_priority_verdict(monkeypatch):
    """Bis S117 stand hier bei B > 12 eine Eskalationszeile („⚠ überfüllt … priorisieren").

    Sie sollte den Drain zum Tagesauftrag machen und hat das nie geschafft – das leistet
    seit S117 die Rangfolge in `session-agenda.py` (ab B ≥ 13 ist der Drain die einzige
    gezeigte Aufgabe). Der Messwert bleibt hier, das Urteil darüber nicht: Dieses Script
    weiß nicht, was sonst noch ansteht, und wäre in der Agenda eine zweite Stimme.
    """
    monkeypatch.setattr(od, "current_session", lambda root: 200)
    out = od.render(od.Path("."), parse(*[make(f"OBS-S1{i:02d}-1") for i in range(13)]))  # B=13
    assert "Backlog: 13 drainbar" in out
    assert "überfüllt" not in out and "priorisieren" not in out


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
