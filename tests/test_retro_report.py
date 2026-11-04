"""Tests für retro_report.py – CM-Matching (volles Tripel, severity-exakt) und Finding-Parser."""
import sys
import textwrap
from pathlib import Path

import pytest

from prozesscode import retro_report as rr


def _cm(impact="HOCH", kategorie="AGENT", kontexte=None, status="AKTIV", cm_id=""):
    return rr.Countermeasure(
        problem="x", impact=impact, kategorie=kategorie,
        kontexte=kontexte if kontexte is not None else [], status=status, cm_id=cm_id,
    )


def _session(kontext: str, num=99):
    f = rr.Finding(session_num=num, impact="MITTEL", kategorie="PROZESS",
                   kontext=kontext, titel="t")
    return rr.SessionData(num=num, date="2026-01-01", findings=[f])


# --- cm_matches: Match auf das volle Tripel (Impact exakt) -------------------
def test_cm_matches_full_tuple():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.cm_matches(cm, "HOCH", "AGENT", "Review")


def test_cm_matches_requires_exact_severity():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    # MITTEL ≠ HOCH → bewusst kein Match (severity-agnostisch über-maskiert, s. Kommentar im Script)
    assert not rr.cm_matches(cm, "MITTEL", "AGENT", "Review")


def test_cm_matches_requires_kategorie():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "PROZESS", "Review")


def test_cm_matches_wildcard_kontext_matches_any_kontext():
    cm = _cm(impact="MITTEL", kategorie="PROZESS", kontexte=[])
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Tooling")
    assert rr.cm_matches(cm, "MITTEL", "PROZESS", "Gherkin")


def test_cm_matches_kontext_not_in_list():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert not rr.cm_matches(cm, "HOCH", "AGENT", "Tooling")


def test_has_cm_matches_full_tuple():
    cm = _cm(impact="HOCH", kategorie="AGENT", kontexte=["Review"])
    assert rr.has_cm("HOCH", "AGENT", "Review", [cm])
    assert not rr.has_cm("MITTEL", "AGENT", "Review", [cm])


# --- Parser: Titel mit '*' (z.B. JSX-Kommentar) darf nicht durchfallen --------
def test_finding_re_parses_title_with_asterisk():
    line = "- **[GERING] [TOOLING] [Tooling] StrykerJS JSX-`{/* x */}`-Kommentar**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("impact") == "GERING"
    assert "JSX" in m.group("titel")


def test_finding_re_parses_plain_title():
    line = "- **[HOCH] [PROZESS] [TDD] Ganz normaler Titel ohne Sonderzeichen**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("titel") == "Ganz normaler Titel ohne Sonderzeichen"


def test_finding_re_parses_slash_kontext():
    line = "- **[HOCH] [TOOLING] [Bash/Permission] Irgendein Titel**\n"
    m = rr.FINDING_RE.match(line)
    assert m is not None
    assert m.group("kontext") == "Bash/Permission"


# --- load_cm: Fließtext-Format (OBS-S085-14) ---------------------------------
_CM_SAMPLE = textwrap.dedent("""\
    # Countermeasures

    ## Aktive Maßnahmen

    ### CM-S070-3 – Multi-Kontext-Maßnahme
    **Impact:** HOCH | **Kategorie:** TOOLING | **Kontext:** Bash/Permission, Mutation-Testing | **Status:** AKTIV | **Seit:** S070
    **Problem:** Tatsächlicher Problemtext, nicht der Titel
    **Maßnahme:** irgendwas

    ### CM-S047-1 – Wildcard-Kontext
    **Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** – | **Status:** AKTIV | **Seit:** S047
    **Problem:** P
    **Maßnahme:** M

    ## Bewährte Maßnahmen

    ### CM-S078-2 – Offene Maßnahme
    **Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Skill-Nutzung | **Status:** OFFEN | **Seit:** S078
    **Problem:** P2
    **Maßnahme:** M2
    """)


def _write_cm(tmp_path):
    p = tmp_path / "countermeasures.md"
    p.write_text(_CM_SAMPLE, encoding="utf-8")
    return str(p)


def test_load_cm_parses_ids_and_fields(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert [c.cm_id for c in cms] == ["CM-S070-3", "CM-S047-1", "CM-S078-2"]
    first = cms[0]
    assert first.impact == "HOCH"
    assert first.kategorie == "TOOLING"
    assert first.status == "AKTIV"
    assert first.seit_session == 70


def test_load_cm_splits_multi_kontext(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert cms[0].kontexte == ["Bash/Permission", "Mutation-Testing"]


def test_load_cm_dash_kontext_is_wildcard(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    wildcard = next(c for c in cms if c.cm_id == "CM-S047-1")
    assert wildcard.kontexte == []  # – → leer → Wildcard (matcht jeden Kontext)
    assert rr.cm_matches(wildcard, "HOCH", "PROZESS", "BeliebigerKontext")


def test_load_cm_problem_line_overrides_title(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    assert cms[0].problem == "Tatsächlicher Problemtext, nicht der Titel"


def test_load_cm_parses_status_across_sections(tmp_path):
    cms = rr.load_cm(_write_cm(tmp_path))
    offen = next(c for c in cms if c.cm_id == "CM-S078-2")
    assert offen.status == "OFFEN"


# --- archive_start_sessions: speist die CM-Eskalation (Section 9) -------------

def test_archive_start_sessions(tmp_path):
    d = tmp_path / "archive"
    d.mkdir()
    for s in (70, 78, 85):
        (d / f"session_{s:03d}_to_{s + 8:03d}.md").write_text("x", encoding="utf-8")
    (d / "README.md").write_text("x", encoding="utf-8")  # Nicht-Pattern-Datei wird ignoriert
    assert sorted(rr.archive_start_sessions(str(d))) == [70, 78, 85]


# --- unbekannte_tags: Bestandsprüfung gegen process.md ------------------------
# Der Wert liegt darin, dass die Prüfung auch CMs erreicht: countermeasures.md wird von Hand
# editiert, an obs.py/lessons.py vorbei – eine Validierung beim Anlegen sieht sie nie.
def test_unbekannter_tag_in_einem_finding_wird_gemeldet():
    treffer = rr.unbekannte_tags([_session("Kaizen")], [])
    assert [tag for _, tag in treffer] == ["Kaizen"]


def test_bekannter_tag_wird_nicht_gemeldet():
    """Gegenprobe – ohne sie wäre ein leeres Ergebnis nicht von 'prüft nichts' zu trennen."""
    assert rr.unbekannte_tags([_session("Hook/Script")], []) == []


def test_unbekannter_tag_in_einer_cm_wird_gemeldet():
    cm = _cm(kontexte=["Hook/Script", "tech-debt"], cm_id="CM-S999-1")
    assert rr.unbekannte_tags([], [cm]) == [("CM-S999-1", "tech-debt")]


def test_cm_ohne_kontext_ist_kein_verstoss():
    """Leere Kontextliste heißt Wildcard, nicht 'fehlerhaft'."""
    assert rr.unbekannte_tags([], [_cm(kontexte=[])]) == []


# --- render_pattern: was die Retro zum Prüfen eines Kandidaten braucht ---------
def _periode(num: int, *titel: str, impact="MITTEL", kategorie="AGENT", kontext="Doku"):
    findings = [rr.Finding(session_num=num, impact=impact, kategorie=kategorie,
                           kontext=kontext, titel=t) for t in titel]
    return rr.SessionData(num=num, date="2026-01-01", findings=findings)


def test_load_cm_behaelt_den_kurztitel_neben_dem_problemtext(tmp_path):
    """Die Problem-Zeile überschreibt `problem`; der Kurztitel wird für die Anzeige gebraucht."""
    cms = rr.load_cm(_write_cm(tmp_path))
    assert cms[0].titel == "Multi-Kontext-Maßnahme"


def test_neuer_kandidat_zeigt_jedes_mitglied_nicht_nur_die_aeltesten():
    """S127: Ein 4×-Cluster zeigte nur zwei Alt-Mitglieder – das aus der aktuellen Periode fehlte."""
    archiv = [[_periode(10, "LL-S010-1 – alt eins", "LL-S010-2 – alt zwei")]]
    aktuell = [_periode(20, "LL-S020-1 – neu")]
    ausgabe = rr.render_pattern(aktuell, archiv, [])
    for titel in ("alt eins", "alt zwei", "LL-S020-1 – neu"):
        assert titel in ausgabe


def test_mitglied_der_aktuellen_periode_ist_markiert_alte_nicht():
    archiv = [[_periode(10, "LL-S010-1 – alt")]]
    aktuell = [_periode(20, "LL-S020-1 – neu")]
    zeilen = rr.render_pattern(aktuell, archiv, []).splitlines()
    neu = next(z for z in zeilen if "LL-S020-1" in z)
    alt = next(z for z in zeilen if "LL-S010-1" in z)
    assert rr.MARKE_AKTUELL in neu
    assert rr.MARKE_AKTUELL not in alt


def test_abgedeckter_kandidat_nennt_die_abdeckende_cm():
    """Nur so fällt auf, wenn das Tripel zufällig von einer fachfremden CM abgedeckt wird."""
    cm = _cm(impact="MITTEL", kategorie="AGENT", kontexte=["Doku"], cm_id="CM-S105-1")
    cm.titel = "Postgres-Init-Config"
    aktuell = [_periode(20, "LL-S020-1 – eins", "LL-S020-2 – zwei")]
    zeile = next(z for z in rr.render_pattern(aktuell, [], [cm]).splitlines()
                 if "[MITTEL] [AGENT] [Doku]" in z)
    assert "CM-S105-1" in zeile
    assert "Postgres-Init-Config" in zeile


def test_fenster_nimmt_nur_die_letzten_archiv_perioden():
    """Das Fenster sind aktuelle Periode + PATTERN_WINDOW Archiv-Perioden – eine ältere zählt nicht mit."""
    # Given – eine Periode mehr als das Fenster, jede mit einem Mitglied desselben Tripels
    archiv = [[_periode(10 * (i + 1), f"LL-S0{i + 1}0-1 – periode {i + 1}")]
              for i in range(rr.PATTERN_WINDOW + 1)]
    aktuell = [_periode(90, "LL-S090-1 – aktuell")]
    # When
    ausgabe = rr.render_pattern(aktuell, archiv, [])
    # Then
    assert "periode 1" not in ausgabe
    assert all(f"periode {i}" in ausgabe for i in range(2, rr.PATTERN_WINDOW + 2))
    assert f"letzte {rr.PATTERN_WINDOW} Archiv-Perioden ({rr.PATTERN_WINDOW + 1} Sessions gesamt)" in ausgabe


# --- Laden aus dem Archiv: Form des Bestands ------------------------------------
_KOPF = (Path(__file__).resolve().parent.parent
         / ".claude" / "skills" / "kaizen" / "references" / "lessons_learned_template.md")


def _periodendatei(pfad, *sessions: int) -> None:
    """Archiv-Datei wie im Bestand: echter Datei-Header (mit Beispielzeilen), dann Sessions."""
    rumpf = "".join(
        f"\n## Session {n} – 2026-10-0{i + 1}\n\n"
        f"- **[HOCH] [AGENT] [Doku] LL-S{n}-1 – Eintrag {n}**\n  Was: w\n  Warum: x\n"
        for i, n in enumerate(sessions))
    pfad.write_text(_KOPF.read_text(encoding="utf-8") + rumpf, encoding="utf-8")


def test_archiv_perioden_sind_nach_dateiname_sortiert_und_ohne_fremde_dateien(tmp_path):
    # Given – wie docs/kaizen/archive/: Perioden, ein OBS-Archiv ohne Sessions, eine .legacy-Datei
    _periodendatei(tmp_path / "session_133_to_139.md", 133, 139)
    _periodendatei(tmp_path / "session_127_to_132.md", 127, 132)
    (tmp_path / "observations_archive.md").write_text("# OBS-Archiv\n\n## OBS-S100-1 – x\n",
                                                      encoding="utf-8")
    _periodendatei(tmp_path / "session_001_to_046.legacy", 1)
    # When
    perioden = rr.load_archive_periods(str(tmp_path))
    # Then – älteste zuerst; die Beispielzeilen des Headers zählen nicht als Session oder Finding
    assert [[s.num for s in p] for p in perioden] == [[127, 132], [133, 139]]
    assert [len(s.findings) for p in perioden for s in p] == [1, 1, 1, 1]


def test_load_all_vereint_archiv_und_aktuelle_periode_aufsteigend(tmp_path):
    # Given
    archiv = tmp_path / "archive"
    archiv.mkdir()
    _periodendatei(archiv / "session_133_to_139.md", 133)
    aktuell = tmp_path / "lessons_learned.md"
    _periodendatei(aktuell, 141, 140)
    # When
    nummern = [s.num for s in rr.load_all(str(aktuell), str(archiv))]
    # Then
    assert nummern == [133, 140, 141]


@pytest.mark.aufrufpfad("retro_report")
def test_bericht_ueber_main_nennt_periodengrenze_und_kandidat(tmp_path, monkeypatch, capsys):
    # Given – Bestand in echter Form: Archiv bis S139, aktuelle Periode S140/S141
    archiv = tmp_path / "archive"
    archiv.mkdir()
    _periodendatei(archiv / "session_133_to_139.md", 133)
    aktuell = tmp_path / "lessons_learned.md"
    _periodendatei(aktuell, 140, 141)
    cm = tmp_path / "countermeasures.md"
    cm.write_text(_CM_SAMPLE, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["retro_report", "--current", str(aktuell),
                                      "--archive", str(archiv), "--cm", str(cm)])
    # When
    code = rr.main()
    # Then
    ausgabe = capsys.readouterr().out
    assert code == 0
    assert "Letzte Retro: nach Session 139  |  Neue Sessions ab: 140" in ausgabe
    assert "[HOCH] [AGENT] [Doku] – 3×" in ausgabe
    # die Liste aus KPR-wirksamkeitskriterium ist verdrahtet – das Sample trägt kein Kriterium
    assert "CM-S070-3 (seit S70) – Multi-Kontext-Maßnahme" in ausgabe


# --- AKTIV ohne Wirksamkeitskriterium (process.md, KPR-wirksamkeitskriterium) ----
_CM_KRITERIUM = textwrap.dedent("""\
    ## Aktive Maßnahmen

    ### CM-S140-1 – Mit Kriterium
    **Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** Gherkin | **Status:** AKTIV | **Seit:** S140
    **Problem:** P
    **Maßnahme:** M. **Wirksamkeit prüfen:** BEWÄHRT, wenn …

    ### CM-S082-1 – Ohne Kriterium
    **Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Gherkin | **Status:** AKTIV | **Seit:** S082
    **Problem:** P
    **Maßnahme:** M ohne Kriterium

    ## Bewährte Maßnahmen

    ### CM-S124-3 – Bewährt ohne Kriterium
    **Impact:** MITTEL | **Kategorie:** TOOLING | **Kontext:** Doku | **Status:** BEWÄHRT | **Seit:** S124
    **Problem:** P
    **Maßnahme:** M
    """)


def test_nur_aktive_massnahmen_ohne_kriterium_werden_gelistet(tmp_path):
    # Given
    p = tmp_path / "countermeasures.md"
    p.write_text(_CM_KRITERIUM, encoding="utf-8")
    # When
    ausgabe = rr.render_ohne_kriterium(rr.load_cm(str(p)))
    # Then – BEWÄHRT braucht keins mehr, die mit Kriterium bleibt draußen
    assert "CM-S082-1" in ausgabe
    assert "Ohne Kriterium" in ausgabe
    assert "CM-S140-1" not in ausgabe
    assert "CM-S124-3" not in ausgabe


def test_ohne_luecke_meldet_die_liste_das_ausdruecklich(tmp_path):
    """Gegenprobe – ein leerer Abschnitt wäre nicht von „prüft nichts" zu unterscheiden."""
    p = tmp_path / "countermeasures.md"
    p.write_text(_CM_KRITERIUM.split("### CM-S082-1")[0], encoding="utf-8")
    assert "Jede AKTIV-Maßnahme trägt ein Wirksamkeitskriterium" in rr.render_ohne_kriterium(
        rr.load_cm(str(p)))


def test_abgedeckter_kandidat_zeigt_nur_die_mitglieder_der_aktuellen_periode():
    """Alte Mitglieder lagen früheren Retros vor; neu zu prüfen sind nur die aktuellen."""
    cm = _cm(impact="MITTEL", kategorie="AGENT", kontexte=["Doku"], cm_id="CM-S105-1")
    archiv = [[_periode(10, "LL-S010-1 – alt")]]
    aktuell = [_periode(20, "LL-S020-1 – neu")]
    ausgabe = rr.render_pattern(aktuell, archiv, [cm])
    assert "LL-S020-1 – neu" in ausgabe
    assert "LL-S010-1" not in ausgabe
