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
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
agenda = import_module("session-agenda")


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


def test_frame_blocks_are_rendered_even_without_a_task():
    out = agenda.rendere(blocks(), [])
    assert "Nächste Aufgabe: keine erzwungen" in out
    assert "principles-inhalt" in out and "bash-allowlist-inhalt" in out


def test_frame_blocks_are_never_suppressed():
    """Sie sind Verhaltensrahmen; ihr Weglassen fiele lautlos aus."""
    out = agenda.rendere(blocks(retro=True), [])
    assert "principles-inhalt" in out


# --- Anordnung ---------------------------------------------------------------
def test_the_agenda_comes_last_behind_the_unchanging_frame():
    """Das einzig session-spezifische Stück steht direkt vor der ersten User-Nachricht;
    der über Sessions unveränderliche Rahmen davor ist überspringbar."""
    out = agenda.rendere(blocks(retro=True), [])
    assert out.index("principles-inhalt") < out.index("=== Session-Agenda ===")
    assert out.index("bash-allowlist-inhalt") < out.index("=== Session-Agenda ===")


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


# --- Ungeplante Szenarien ----------------------------------------------------
# Ein Szenario fällt auf zwei Wegen aus jedem Plan: seine Feature-Datei trägt keinen
# `@US-`Tag (die Lauf-Auflösung läuft über die aktuelle Story und erreicht sie nie), oder
# ihm fehlt der `# @run-N`-Kommentar. Ohne diese Meldung behauptet der Session-Start
# fälschlich Vollständigkeit („alle Läufe implementiert").
STORY_FEATURE = (
    "@US-904\nFeature: Zutaten\n\n"
    "  # @run-7 · Liste · Full-Stack\n  Scenario: Geplant\n    Given x\n"
)
CROSS_FEATURE = "@CROSS-interaction\nFeature: Querschnitt\n\n  Scenario: Waise\n    Given x\n"


def test_scenario_in_a_story_less_file_is_unplanned():
    anzahl, befunde = agenda.ungeplante_szenarien([("cross.feature", CROSS_FEATURE)], set())
    assert anzahl == 1
    assert any("Waise" in z for z in befunde)
    assert any("keinen `@US-`Tag" in z for z in befunde)


def test_clustered_story_scenario_is_not_unplanned():
    assert agenda.ungeplante_szenarien([("s.feature", STORY_FEATURE)], set())[0] == 0


def test_story_scenario_without_a_run_tag_is_unplanned():
    ohne_run = "@US-904\nFeature: Zutaten\n\n  Scenario: Ungeclustert\n    Given x\n"
    anzahl, befunde = agenda.ungeplante_szenarien([("s.feature", ohne_run)], set())
    assert anzahl == 1
    assert any("nie geclustert" in z for z in befunde)


def test_implemented_scenarios_are_not_reported():
    """Erledigtes ist kein offener Plan – sonst stünde die Meldung für immer da."""
    assert agenda.ungeplante_szenarien([("cross.feature", CROSS_FEATURE)], {"Waise"})[0] == 0


def test_no_findings_yields_no_stub():
    assert agenda.modul_ungeplante_szenarien.__doc__  # Modul existiert
    anzahl, befunde = agenda.ungeplante_szenarien([], set())
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
