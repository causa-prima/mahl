"""Tests für session-agenda.py – Rangfolge, Stubs und Ausfall-Isolation.

Vier Zusagen, die der Session-Start hält:
  1. GENAU EINE „Nächste Aufgabe", nach fester Rangfolge (retro > obs-drain > priorities >
     next-run), und ihr Text ist BUCHSTÄBLICH die Ausgabe von `--only <name>` – keine
     zusammenfassende Kopfzeile davor, die den Inhalt darunter doppelte.
  2. Jeder unterdrückte Kandidat bleibt als Stub MIT MESSWERT sichtbar – man kann nicht
     anfordern, wovon man nicht weiß, dass es existiert, und der User übersteuert regelmäßig.
  3. Zustand, Aufgabe und Einzeiler stehen zusammenhängend am SCHLUSS, hinter dem
     unveränderlichen Rahmen (principles, Allow-Liste).
  4. Ein ausgefallenes Modul reißt die Agenda nicht mit, sondern meldet sich als Warnzeile.
     Ein leerer Session-Start wäre von „nichts zu tun" ununterscheidbar.
"""
import functools
import json
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import pytest

agenda = import_module("prozesscode.session-agenda")

REPO_ROOT = Path(__file__).resolve().parents[1]


_BESTANDSSCANS = ("anker-defekt", "ordinale")


@pytest.fixture(autouse=True, scope="module")
def _bestand_nur_einmal_pruefen():
    """Die Module `anker-defekt` und `ordinale` prüfen je ~1,7 s den ganzen Repo-Bestand, und
    elf Tests fuhren beide neu – zusammen rund 36 s, gut 90 % der Werkzeug-Suite (S133
    gemessen). Innerhalb eines Laufs ändert sich der Bestand nicht; geprüft wird er daher
    einmal. Gecacht wird der Eintrag in `MODULE`, nicht die Funktion: Tests, die
    `modul_anker_defekt()` direkt mit ersetztem Bestand rufen, bleiben unberührt.
    Subprozess-Tests (echter CLI-Pfad) erreicht der Cache bewusst nicht."""
    mp = pytest.MonkeyPatch()
    mp.setattr(agenda, "MODULE", [(n, a, functools.cache(f) if n in _BESTANDSSCANS else f)
                                  for n, a, f in agenda.MODULE])
    yield
    mp.undo()
# Als Modul starten, nicht als Datei: die Agenda nutzt paketinterne Importe und findet ihren
# Paketkontext nur so. `cwd` macht `prozesscode` für den Subprozess auffindbar.
CLI = ["-m", "prozesscode.session-agenda"]


def blocks(**beansprucht: bool) -> dict:
    """Blöcke für alle Module; genannte beanspruchen den Aufgaben-Slot."""
    return {
        name: agenda.Block(stub=f"{name}-stub", inhalt=f"{name}-inhalt",
                           beansprucht=beansprucht.get(name, False))
        for name, _art, _f in agenda.MODULE
    }


# --- Rangfolge ---------------------------------------------------------------
def test_retro_outranks_the_drain():
    assert agenda.waehle_aufgabe(blocks(retro=True, **{"obs-drain": True})) == "retro"


def test_drain_wins_when_no_retro_is_due():
    gewaehlt = agenda.waehle_aufgabe(blocks(**{"obs-drain": True, "priorities": True}))
    assert gewaehlt == "obs-drain"


def test_priorities_outrank_the_next_run():
    gewaehlt = agenda.waehle_aufgabe(blocks(priorities=True, **{"next-run": True}))
    assert gewaehlt == "priorities"


def test_next_run_is_the_last_resort():
    assert agenda.waehle_aufgabe(blocks(**{"next-run": True})) == "next-run"


def test_nothing_claims_yields_no_task():
    assert agenda.waehle_aufgabe(blocks()) is None


def test_stub_only_modules_never_claim():
    """Fällige Fragen, TD oder ungeplante Szenarien verlangen eine Entscheidung, keinen
    Arbeitstag – sonst verdrängte eine 34 Sessions alte Frage eine laufende Story."""
    alle_stubs = {name: True for name, art, _ in agenda.MODULE if art == agenda.STUB}
    assert agenda.waehle_aufgabe(blocks(**alle_stubs)) is None


# --- Rendern -----------------------------------------------------------------
def test_the_task_is_rendered_in_full():
    out = agenda.rendere(blocks(retro=True), [])
    assert "--- Nächste Aufgabe ---" in out
    assert "retro-inhalt" in out


def test_the_task_carries_no_summarising_headline():
    """Der Aufgabentext IST die `--only`-Ausgabe. Eine Kopfzeile aus dem Stub davor wäre
    dieselbe Information zweimal – genau die Doppelung, die S117 beanstandet wurde."""
    out = agenda.rendere(blocks(retro=True), [])
    assert "retro-stub" not in out


def test_suppressed_candidates_stay_visible_as_stubs():
    out = agenda.rendere(blocks(retro=True), [])
    assert "obs-drain-stub" in out and "priorities-stub" in out
    assert "obs-drain-inhalt" not in out  # unterdrückt heißt: nur der Einzeiler


def test_the_retrieval_command_is_offered_once():
    out = agenda.rendere(blocks(retro=True), [])
    assert out.count(agenda.ABRUF) == 1


def test_the_retrieval_command_explains_its_placeholder():
    """`--only <name>` allein sagt nicht, welche Werte gültig sind (S117-Rückmeldung)."""
    out = agenda.rendere(blocks(retro=True), [])
    assert "<name> = das Wort vor dem Doppelpunkt" in out


def test_silent_modules_produce_no_stub_line():
    """Ein Modul ohne Meldung (leerer Stub) darf keine leere Zeile erzeugen."""
    b = blocks()
    b["td-due"] = agenda.Block(stub="")
    assert "td-due" not in agenda.rendere(b, [])


def test_the_task_slot_stays_filled_without_a_claim():
    out = agenda.rendere(blocks(), [])
    assert "Nächste Aufgabe: keine erzwungen" in out


def test_the_agenda_no_longer_carries_the_frame():
    """Seit S128 sind die Rahmen EIGENE Injektionsblöcke, nicht Teil der Agenda.

    Bis dahin rendete `rendere()` principles.md und Allow-Liste mit – zusammen 23.123
    UTF-16 units, also weit über dem 10.000er-Cap, an dem der Runtime den GESAMTEN
    Block gegen eine 2.000er-Vorschau tauscht. Die Agenda stand am Ende und kam damit
    in keiner Session an. Ein Rahmen HIER wäre der Rückfall in genau diesen Zustand.
    """
    out = agenda.rendere(blocks(retro=True), [])
    assert "principles-inhalt" not in out
    assert "bash-allowlist-inhalt" not in out


def test_the_frame_is_never_suppressed_but_lives_in_its_own_blocks():
    """Die Zusage bleibt – sie wandert nur auf die Block-Ebene."""
    namen = {name for name, _t, _f in agenda.INJEKTIONS_BLOECKE}
    assert {"verhalten", "doku", "kommunikation", "bash-allowlist"} <= namen


# --- Anordnung ---------------------------------------------------------------
# Über BLOCKgrenzen hinweg gibt es keine Anordnung mehr: Hooks eines Events laufen
# parallel und kommen gemischt an. Was ANORDNUNG heißt, gilt nur noch INNERHALB eines
# Blocks; die Identität über Blöcke hinweg trägt die Kopfzeile, nicht die Position.

def test_state_task_and_stubs_are_contiguous():
    """Zustand, Aufgabe und Einzeiler gehören zusammen – bis S117 lag der Zustand hinter
    130 Zeilen principles.md und war vom Rest getrennt."""
    out = agenda.rendere(blocks(retro=True), [])
    assert out.index("memory-state-inhalt") < out.index("--- Nächste Aufgabe ---")
    assert out.index("--- Nächste Aufgabe ---") < out.index("Nachrangig –")


def test_the_subordinate_section_states_its_rank_in_its_label():
    """Der Rang gehört ins LABEL, nicht in die Trennerform.

    Zwischenstand in S117: Der Trenner wurde weggelassen, damit der Abschnitt nicht
    gleichrangig wirkt – dann lief er optisch in der Aufgabe weiter, weil ihr die untere
    Grenze fehlte. Ein neutrales Label („Ebenfalls offen") war das eigentliche Problem.
    """
    out = agenda.rendere(blocks(retro=True), [])
    assert f"--- {agenda.NACHRANG} ---" in out
    assert "Ebenfalls offen" not in out


def test_the_task_section_is_bounded_at_the_bottom():
    """Gegenprobe: Ohne folgenden Trenner endete der Aufgabentext nirgends sichtbar."""
    out = agenda.rendere(blocks(retro=True), [])
    nach_aufgabe = out[out.index("retro-inhalt") + len("retro-inhalt"):]
    assert nach_aufgabe.lstrip().startswith("--- ")


def test_the_state_block_gets_no_title_of_its_own():
    """Sein Titel war die Aneinanderreihung derselben drei Zeilen (S117-Rückmeldung)."""
    out = agenda.rendere(blocks(retro=True), [])
    assert "=== memory-state" not in out
    assert out.count("memory-state-inhalt") == 1


def test_the_state_block_is_never_a_stub_line():
    b = blocks()
    b["memory-state"] = agenda.Block(stub="", inhalt="Phase: X")
    assert "  - memory-state:" not in agenda.rendere(b, [])


# --- Ausfall-Isolation (Gegenprobe) ------------------------------------------
def test_a_failing_module_does_not_take_down_the_agenda(monkeypatch):
    kaputt = [(name, art, (lambda: (_ for _ in ()).throw(RuntimeError("kaputt")))
               if name == "retro" else f)
              for name, art, f in agenda.MODULE]
    monkeypatch.setattr(agenda, "MODULE", kaputt)
    bloecke, warnungen = agenda.sammle()
    assert "retro" not in bloecke
    assert any("retro" in w and "kaputt" in w for w in warnungen)
    assert "obs-drain" in bloecke  # der Rest lief weiter


def test_the_warning_names_the_single_module_retrieval(monkeypatch):
    kaputt = [(name, art, (lambda: (_ for _ in ()).throw(RuntimeError("x")))
               if name == "td-due" else f)
              for name, art, f in agenda.MODULE]
    monkeypatch.setattr(agenda, "MODULE", kaputt)
    _, warnungen = agenda.sammle()
    assert any("--only td-due" in w for w in warnungen)


def test_warnings_are_rendered_into_the_agenda():
    out = agenda.rendere(blocks(), ["WARNUNG: Modul `x` ausgefallen"])
    assert "WARNUNG: Modul `x` ausgefallen" in out


# --- Der Retro-Anspruch hängt am Befund, nicht am Exit-Code ------------------
# Ein Agenda-Modul wertet ausschließlich das stdout seines Scripts aus; Exit ≠ 0 heißt
# einheitlich „ausgefallen". Ein Score-Script, das seinen Befund über den Exit-Code
# meldete, fiele deshalb GENAU DANN aus, wenn eine Retro fällig ist – der lauteste Fall
# würde der stummste.
def _score_ausgabe(text: str):
    """Ersetzt `_modulausgabe` durch eine feste Antwort."""
    return lambda modul, *argv: text


def test_retro_is_claimed_when_the_score_report_says_it_is_due(monkeypatch):
    monkeypatch.setattr(agenda, "_modulausgabe",
                        _score_ausgabe("Jenga-Score: -14 / 100  [RETRO FÄLLIG]"))
    block = agenda.modul_retro()
    assert block.beansprucht
    assert "-14" in block.stub


def test_retro_is_not_claimed_when_the_score_is_healthy(monkeypatch):
    monkeypatch.setattr(agenda, "_modulausgabe",
                        _score_ausgabe("Jenga-Score: 42 / 100  [OK]"))
    assert not agenda.modul_retro().beansprucht


def test_a_crash_of_the_score_script_still_fails_the_module(monkeypatch):
    """Gegenprobe: Der Ausfallpfad muss weiterhin greifen, sonst prüft der Rest nichts."""
    def _kracht(modul, *argv):
        raise RuntimeError(f"prozesscode.{modul} → Exit 1")

    monkeypatch.setattr(agenda, "_modulausgabe", _kracht)
    try:
        agenda.modul_retro()
    except RuntimeError:
        return
    raise AssertionError("Exit 1 muss als Ausfall gelten")


# --- Ungeclusterte Szenarien -------------------------------------------------
# Seit der Resolver über Phase und `braucht:`-Kanten auflöst, fällt kein Szenario mehr aus dem
# Plan, nur weil seine Datei keinen `@US-`Tag trägt. Offen bleibt allein das Clustering: Ohne
# `# @run-N` legt der Resolver jedes Szenario als Einzel-Lauf vor – ohne Label, Schicht und Batch.
STORY_FEATURE = (
    "@US-904\nFeature: Zutaten\n\n  # @phase: SKELETON\n\n"
    "  # @run-7 · Liste · Full-Stack\n  Scenario: Geplant\n    Given x\n"
)
CROSS_FEATURE = (
    "@CROSS-interaction\nFeature: Querschnitt\n\n  # @phase: V1\n\n"
    "  Scenario: Waise\n    Given x\n"
)


def test_uncluster_scenario_is_reported_regardless_of_story_tag():
    anzahl, befunde = agenda.ungeclusterte_szenarien([("cross.feature", CROSS_FEATURE)], set())
    assert anzahl == 1
    assert any("Waise" in z for z in befunde)
    assert any("nie geclustert" in z for z in befunde)


def test_clustered_story_scenario_is_not_unplanned():
    assert agenda.ungeclusterte_szenarien([("s.feature", STORY_FEATURE)], set())[0] == 0


def test_story_scenario_without_a_run_tag_is_unplanned():
    ohne_run = "@US-904\nFeature: Zutaten\n\n  # @phase: SKELETON\n\n  Scenario: Ungeclustert\n    Given x\n"
    anzahl, befunde = agenda.ungeclusterte_szenarien([("s.feature", ohne_run)], set())
    assert anzahl == 1
    assert any("nie geclustert" in z for z in befunde)


def test_implemented_scenarios_are_not_reported():
    """Erledigtes ist kein offener Plan – sonst stünde die Meldung für immer da."""
    assert agenda.ungeclusterte_szenarien([("cross.feature", CROSS_FEATURE)], {"Waise"})[0] == 0


def test_no_findings_yields_no_stub():
    assert callable(agenda.modul_ungeclusterte_szenarien)  # Modul existiert
    anzahl, befunde = agenda.ungeclusterte_szenarien([], set())
    assert anzahl == 0 and befunde == []


# --- Prioritäten: oberster voll, Rest kurz -----------------------------------
# Neun Punkte im Volltext wären wieder die konkurrierenden Aufträge, gegen die die Rangfolge
# gebaut ist; alle nur als Kurzform machte die Aufgabe unbearbeitbar.
LISTE = (
    "- **Erster** — `Fällig: Phase:MVP` · Quelle: q1 · Done: d1\n"
    "  Zusatzzeile zum ersten.\n"
    "\n"
    "- **Zweiter** — `Fällig: jetzt` · Quelle: q2 · Done: d2\n"
    "\n"
    "- **Dritter** — `Fällig: jetzt` · Quelle: q3 · Done: d3\n"
)


def test_entries_keep_their_continuation_lines():
    eintraege = agenda.prioritaets_eintraege(LISTE)
    assert [e[0].split(" — ")[0] for e in eintraege] == ["- **Erster**", "- **Zweiter**",
                                                         "- **Dritter**"]
    assert eintraege[0][1].strip() == "Zusatzzeile zum ersten."


def test_the_first_due_now_entry_is_shown_in_full():
    """`jetzt` ist der Auslöser – nicht die Dokumentreihenfolge."""
    out = agenda.rendere_prioritaeten(agenda.prioritaets_eintraege(LISTE))
    assert "- **Zweiter** — `Fällig: jetzt` · Quelle: q2 · Done: d2" in out


def test_the_remaining_entries_are_shortened_to_title_and_due_date():
    out = agenda.rendere_prioritaeten(agenda.prioritaets_eintraege(LISTE))
    assert "- **Dritter** — `Fällig: jetzt`" in out
    assert "q3" not in out and "d3" not in out       # Quelle/Done fallen weg
    assert "Zusatzzeile zum ersten." not in out      # Prosa der Kurzform ebenfalls


def test_the_shortened_entries_point_at_their_full_text():
    """Sonst wäre der Volltext von Punkt 3 nirgends erreichbar."""
    assert "docs/AGENT_MEMORY.md" in agenda.rendere_prioritaeten(
        agenda.prioritaets_eintraege(LISTE))


def test_without_a_due_now_entry_the_first_one_is_shown_in_full():
    """`--only priorities` ist der Übersteuerungs-Pfad und muss auch ohne `jetzt` etwas zeigen."""
    ohne = "- **Einziger** — `Fällig: Phase:MVP` · Quelle: q · Done: d\n"
    assert "Quelle: q" in agenda.rendere_prioritaeten(agenda.prioritaets_eintraege(ohne))


def test_an_empty_list_says_so_instead_of_rendering_nothing():
    assert agenda.rendere_prioritaeten([]) == "(keine Prioritäten notiert)"


# --- HTML-Kommentare ---------------------------------------------------------
def test_maintenance_comments_are_stripped():
    """`wann-lesen`/`wann-schreiben` richten sich an den Schreibenden, nicht an den Leser."""
    text = "# Principles\n\n<!--\nwann-lesen: …\n-->\n\n## Abschnitt\n- Regel\n"
    assert agenda.ohne_kommentare(text) == "# Principles\n\n## Abschnitt\n- Regel"


def test_text_without_comments_is_untouched_apart_from_trailing_space():
    assert agenda.ohne_kommentare("# T\n\n- Regel\n") == "# T\n\n- Regel"


# --- Abschnitts-Extraktion ---------------------------------------------------
def test_extracts_a_section_up_to_the_next_heading():
    text = "# T\n\n## A\nzeile a\n\n## B\nzeile b\n"
    assert agenda._abschnitt(text, "## A") == "zeile a"


def test_missing_section_yields_empty_string():
    assert agenda._abschnitt("# T\n", "## Fehlt") == ""


# --- Anker-Prüfung am Session-Start ------------------------------------------
# Der PreToolUse-Hook sieht nur Edit/Write. Verschwindet eine ganze Datei (rm, mv, ein Merge,
# eine Änderung von Hand), sterben ihre Anker lautlos und die Verweise darauf werden tot,
# ohne dass irgendetwas anschlägt. Dieses Modul ist das Auffangnetz dafür.
def test_anker_modul_schweigt_wenn_alles_aufloesbar(monkeypatch):
    monkeypatch.setattr(agenda.anchors, "lies_bestand", lambda _root=None: {})
    assert agenda.modul_anker_defekt().stub == ""


def test_anker_modul_meldet_toten_verweis(monkeypatch):
    monkeypatch.setattr(agenda.anchors, "lies_bestand", lambda _root=None: {
        "a.md": "Siehe [CGT-weg](b.md#CGT-weg).\n"})
    block = agenda.modul_anker_defekt()
    assert "CGT-weg" in block.inhalt and block.stub


def test_anker_modul_faellt_nie_still_aus(monkeypatch):
    """Ein Prüfer, der stumm ausfällt, meldet für immer „alles gut" – und sein Ausfall löst
    per Definition nichts aus (CM-S116-1). Deshalb wird der Fehler selbst zur Meldung."""
    def kracht(_root=None):
        raise OSError("Bestand nicht lesbar")
    monkeypatch.setattr(agenda.anchors, "lies_bestand", kracht)
    assert "Bestand nicht lesbar" in agenda.modul_anker_defekt().stub


# --- Gliederungsnummern am Session-Start -------------------------------------
# Dieselbe Lücke wie oben, andere Klasse: `check-ordinale.py` sieht nur Edit/Write. Kommt eine
# Datei per Merge oder `mv` herein, bringt sie ihre Nummern ungeprüft mit.
def test_ordinal_modul_schweigt_bei_sauberem_bestand(monkeypatch):
    monkeypatch.setattr(agenda.ordinale, "bestand", lambda _root=None: [])
    assert agenda.modul_ordinale().stub == ""


def test_ordinal_modul_meldet_fundstelle(monkeypatch):
    monkeypatch.setattr(agenda.ordinale, "bestand",
                        lambda _root=None: [("docs/a.md", 5, "## 5. Findings", "Überschrift")])
    block = agenda.modul_ordinale()
    assert "docs/a.md" in block.inhalt and block.stub


def test_ordinal_modul_faellt_nie_still_aus(monkeypatch):
    """Gleiche Begründung wie beim Anker-Modul: CM-S116-1."""
    def kracht(_root=None):
        raise OSError("Bestand nicht lesbar")
    monkeypatch.setattr(agenda.ordinale, "bestand", kracht)
    assert "Bestand nicht lesbar" in agenda.modul_ordinale().stub


def test_anker_modul_beansprucht_den_aufgaben_slot_nicht():
    """Ein defekter Verweis ist ein Befund, kein Arbeitsauftrag für die Session."""
    arten = {name: art for name, art, _f in agenda.MODULE}
    assert arten["anker-defekt"] == agenda.STUB


# --- Repo-Zustand ------------------------------------------------------------
def _git_antworten(monkeypatch, status: str, log: str = "abc1234 letzter Commit") -> None:
    monkeypatch.setattr(agenda, "_laufe",
                        lambda *befehl: status if "status" in befehl else log)


def test_ein_sauberer_arbeitsbaum_wird_als_sauber_gemeldet(monkeypatch):
    _git_antworten(monkeypatch, "")
    assert "sauber" in agenda.modul_repo_state().inhalt


def test_uncommittete_dateien_werden_gezaehlt_und_benannt(monkeypatch):
    _git_antworten(monkeypatch, " M a.py\n M b.py")
    inhalt = agenda.modul_repo_state().inhalt
    assert "2 Datei(en) uncommitted" in inhalt
    assert "a.py" in inhalt and "b.py" in inhalt


def test_eine_lange_dateiliste_wird_gedeckelt(monkeypatch):
    """Bei einem großen Umbau ersetzte die Liste sonst die Agenda – im selben Block."""
    _git_antworten(monkeypatch, "\n".join(f" M datei{i}.py" for i in range(20)))
    inhalt = agenda.modul_repo_state().inhalt
    assert "20 Datei(en) uncommitted" in inhalt
    assert "und 12 weitere" in inhalt
    assert "datei19.py" not in inhalt


def test_der_repo_zustand_erzeugt_keine_stub_zeile(monkeypatch):
    """Wie `memory-state`: klein und immer relevant – eine Kurzfassung daneben wäre
    dieselbe Information ein zweites Mal."""
    _git_antworten(monkeypatch, "")
    assert agenda.modul_repo_state().stub == ""


# --- Injektions-Blöcke: der 10.000-u16-Cap -----------------------------------
# Der Runtime verwirft zu große Hook-Ausgaben kommentarlos; Mechanik, Einheit und Quellen
# stehen an `CAP` in session-agenda.py. Hier wird geprüft, was daraus folgt.

def test_u16_zaehlt_astrale_zeichen_doppelt():
    """Die Messgröße ist UTF-16 units – sonst misst der Guard etwas anderes als der Cap.

    Gegenprobe zum naheliegenden Fehler, in Zeichen oder Bytes zu messen: 😀 ist EIN
    Zeichen und VIER UTF-8-Bytes, zählt für den Cap aber ZWEI.
    """
    assert agenda.u16("A") == 1
    assert agenda.u16("ä") == 1          # 2 Bytes, aber 1 unit
    assert agenda.u16("😀") == 2         # 1 Zeichen, 4 Bytes, aber 2 units


def test_jeder_injektionsblock_bleibt_unter_dem_cap():
    """Am ECHTEN Bestand, nicht an Fixtures – der Cap greift auf die reale Ausgabe."""
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        groesse = agenda.u16(agenda.rendere_block(name))
        assert groesse <= agenda.CAP, f"Block {name}: {groesse} u16 > {agenda.CAP}"


def test_jeder_injektionsblock_haelt_das_budget_mit_luft():
    """Unter dem Cap reicht nicht: principles.md wächst mit jeder Retro.

    Reißt ein Block das Budget, ist das eine Aufforderung zum Nachschneiden, solange
    noch Luft ist – nicht erst, wenn der Block bereits stumm verschwunden ist.
    """
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        groesse = agenda.u16(agenda.rendere_block(name))
        assert groesse <= agenda.BUDGET, (
            f"Block {name}: {groesse} u16 > Budget {agenda.BUDGET} "
            f"({groesse / agenda.CAP:.0%} des Caps) – neu schneiden")


def test_kein_abschnitt_von_principles_faellt_zwischen_die_bloecke():
    """Vollständigkeit gegen den Zuschnitt: Jeder Anker landet in genau einem Block.

    Der Zuschnitt nennt Anker beim Namen. Ohne diesen Test verschwände ein NEU
    hinzugefügter Abschnitt lautlos – derselbe stumme Ausfall, den die Aufteilung
    gerade behebt, eine Ebene tiefer.
    """
    verteilt = agenda.principles_zuschnitt()
    zugeordnet = [a for anker in verteilt.values() for a in anker]
    assert sorted(zugeordnet) == sorted(agenda.principles_anker())
    assert len(zugeordnet) == len(set(zugeordnet)), "ein Anker in mehreren Blöcken"


def test_ein_neuer_abschnitt_landet_im_auffangblock(monkeypatch):
    """Gegenprobe: Ein Anker, den der Zuschnitt nicht kennt, darf nicht verschwinden."""
    monkeypatch.setattr(agenda, "principles_anker",
                        lambda: ["KPI-review-prozess", "KPI-brandneu"])
    verteilt = agenda.principles_zuschnitt()
    assert "KPI-brandneu" in verteilt[agenda.AUFFANGBLOCK]


def test_jeder_block_nennt_sich_selbst():
    """Hooks eines Events laufen PARALLEL – die Ankunftsreihenfolge ist zufällig.

    In #84021 gemessen: vier Teile kamen als 2,1,4,3 an. Wer auf die Position vertraut,
    setzt falsch zusammen – schlimmer als Truncation, weil nichts zu fehlen scheint.
    """
    anzahl = len(agenda.INJEKTIONS_BLOECKE)
    for i, (name, titel, _f) in enumerate(agenda.INJEKTIONS_BLOECKE, start=1):
        kopf = agenda.rendere_block(name).splitlines()[0]
        assert titel in kopf
        assert f"{i}/{anzahl}" in kopf


def test_jeder_block_warnt_vor_der_ankunftsreihenfolge():
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        assert "Reihenfolge" in agenda.rendere_block(name)


def test_jeder_block_nennt_seinen_eigenen_abrufbefehl():
    """Rückfall, falls ein Block DOCH spillt: Die Vorschau umfasst die ersten 2.000
    units, der Kopf überlebt sie also. Er nennt den GEZIELTEN Abruf – „lies die
    Datei" führte zur Volldatei zurück und damit zum Problem, das wir gerade lösen.
    """
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        kopf = agenda.rendere_block(name)[:2000]
        assert f"--block {name}" in kopf


def test_ein_zu_grosser_block_warnt_innerhalb_der_vorschau(monkeypatch):
    """Die Gegenprobe zum Guard: Wird er ausgelöst, wenn der Fall wirklich eintritt?

    Ohne diesen Test prüft der Guard nur, dass der heutige Bestand passt – und fiele
    beim einzigen Fall, für den er gebaut ist, selbst lautlos aus.
    """
    monkeypatch.setattr(agenda, "modul_bash_allowlist",
                        lambda: agenda.Block(stub="x", inhalt="A" * 12_000))
    kopf = agenda.rendere_block("bash-allowlist")[:2000]
    assert "ÜBERSCHREITET" in kopf


def test_kein_agenda_modul_startet_einen_subprozess_auf_eigenen_code(monkeypatch):
    """`_laufe` ist für fremde Programme da (git) – eigene Module werden importiert.

    Der Subprozess stammt aus der Zeit vor dem Paket-Umzug. Er kostet je Session-Start
    einen Interpreterstart pro Modul, und im Mutantenbaum von mutmut lädt er den
    instrumentierten Code ohne dessen Laufzeit und reißt den Lauf mit – fünf Agenda-Module
    fielen dort aus, bevor ein einziger Mutant bewertet war.
    """
    gesehen: list[tuple[str, ...]] = []
    echt = agenda._laufe
    monkeypatch.setattr(agenda, "_laufe",
                        lambda *befehl: (gesehen.append(befehl), echt(*befehl))[1])
    agenda.sammle()
    eigen = [b for b in gesehen if b[0] != "git"]
    assert not eigen, f"Subprozess auf eigenen Code: {eigen}"


def test_die_allow_liste_kommt_ohne_subprozess(monkeypatch):
    """Der Block holt die Liste als Funktionsaufruf, nicht über `python3 -m …`.

    Der Subprozess war nötig, solange der Hook unter `.claude/hooks/` lag und nicht
    importierbar war. Er hat zwei Kosten: Ein Prozessstart je Session-Start, und unter
    mutmut lädt der Subprozess den instrumentierten Hook ohne die mutmut-Laufzeit – der
    Lauf brach dort ab, bevor ein Mutant bewertet war (dieselbe Ursache wie in
    `test_bash_permission_runner.py`).
    """
    monkeypatch.setattr(agenda, "_laufe", lambda *b: pytest.fail(f"Subprozess: {b}"))
    block = agenda.modul_bash_allowlist()
    assert "Allow-Liste" in block.inhalt


def test_unbekannter_blockname_wird_abgewiesen():
    with pytest.raises(KeyError):
        agenda.rendere_block("gibt-es-nicht")


@pytest.mark.aufrufpfad("session-agenda")
def test_die_cli_liefert_je_blockname_verschiedene_bloecke():
    """Geprüft wird der Pfad, den der HOOK nimmt – die CLI, nicht die Funktion.

    Beim Bau war `--block` geparst, aber nie ausgewertet: Jeder der fünf Hooks hätte
    dieselbe Agenda injiziert, principles.md und Allow-Liste wären ersatzlos
    verschwunden. Alle 59 Funktionstests waren dabei grün, weil sie `rendere_block()`
    direkt aufriefen. Ein Test der Funktion ist kein Test der Wirkung.
    """
    ausgaben = {}
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        fertig = subprocess.run(
            [sys.executable, *CLI, "--block", name],
            capture_output=True, text=True, cwd=str(REPO_ROOT))
        assert fertig.returncode == 0, fertig.stderr
        ausgaben[name] = fertig.stdout
    assert len(set(ausgaben.values())) == len(ausgaben), "Blöcke liefern denselben Text"
    for name, text in ausgaben.items():
        assert f"--block {name}" in text


def test_die_cli_weist_einen_unbekannten_block_ab():
    """Gegenprobe: Ein Tippfehler in settings.json muss laut scheitern, nicht leer
    durchlaufen – ein leerer Block ist von einem fehlenden nicht zu unterscheiden."""
    fertig = subprocess.run(
        [sys.executable, *CLI, "--block", "gibt-es-nicht"],
        capture_output=True, text=True, cwd=str(REPO_ROOT))
    assert fertig.returncode == 1
    assert not fertig.stdout.strip()


def test_jeder_block_endet_auf_genau_einer_abschlussmarke():
    """S128, beim Prüflauf gefunden: Der Agenda-Block trug zwei ineinander liegende Rahmen,
    weil `rendere()` und `rendere_block()` beide eine Marke setzten."""
    for name, _titel, _f in agenda.INJEKTIONS_BLOECKE:
        zeilen = [z for z in agenda.rendere_block(name).splitlines() if z.strip()]
        marken = [z for z in zeilen if set(z.strip()) == {"="} and len(z.strip()) > 8]
        # Eine am Anfang (Kopfzeile zählt nicht, die trägt Text), eine am Schluss.
        assert marken == [zeilen[-1]], f"Block {name}: {len(marken)} Abschlussmarken"


def test_settings_registriert_genau_die_definierten_bloecke():
    """Die Kopplung, an der die Aufteilung sonst lautlos zerfällt.

    Ein Block ohne Registrierung wird nie injiziert; eine Registrierung ohne Block
    scheitert bei jedem Session-Start. Beides bliebe unbemerkt – der Session-Start
    meldet weder das eine noch das andere, und das ist die Ausgangslage von S128.
    """
    settings = json.loads(
        (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    befehle = [h["command"]
               for eintrag in settings["hooks"]["SessionStart"]
               for h in eintrag["hooks"]]
    registriert = [b.split("--block", 1)[1].strip() for b in befehle if "--block" in b]
    definiert = [name for name, _t, _f in agenda.INJEKTIONS_BLOECKE]
    assert sorted(registriert) == sorted(definiert)

    # Nicht jeder SessionStart-Hook ist ein Agenda-Block – aber jeder muss hier stehen, sonst
    # fiele ein versehentlich hinzugefügter Fremd-Eintrag nicht mehr auf.
    #   user-message: gibt JSON mit `systemMessage` aus (erreicht den USER, nicht den Agenten)
    #     und darf deshalb kein Agenda-Block sein – Blöcke geben Plain-Text aus, und sobald ein
    #     Hook JSON ausgibt, wird es als JSON statt als Kontext gelesen.
    erlaubt_ohne_block = {"prozesscode.user-message"}
    fremd = [b for b in befehle
             if "--block" not in b and not any(e in b for e in erlaubt_ohne_block)]
    assert fremd == [], f"unbekannter SessionStart-Hook ohne --block: {fremd}"


def test_die_bloecke_zusammen_ergeben_die_gesamtausgabe():
    """Eine Quelle, zwei Sichten: Der Gesamtmodus setzt dieselben Blöcke zusammen.

    Sonst driften Injektion und manueller Aufruf auseinander, und der Bestand, den ein
    Mensch prüft, wäre nicht der, den der Agent bekommt.
    """
    einzeln = "\n".join(agenda.rendere_block(n)
                        for n, _t, _f in agenda.INJEKTIONS_BLOECKE)
    assert agenda.rendere_alles() == einzeln
