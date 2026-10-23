"""Tests für commit_msg.py – Form des Abschluss-Commits.

Der Trailer `Session-Ende: <NNN>` vergibt jede Tracker-ID; eine vertippte oder doppelte Marke
bricht die Nummernableitung still. Der Hook prüft deshalb die Marke selbst, nicht nur die Länge.
"""
import subprocess

import pytest
from conftest import cli_aufruf, git_repo

from prozesscode import commit_msg


def pruefe(text: str, erwartete_session=126, head_session=None):
    """Prüfung mit fest vorgegebenem Repo-Zustand – kein git-Aufruf im Test."""
    return commit_msg.befunde(text, erwartete_session=erwartete_session, head_session=head_session)


def git_trailer(text: str) -> str:
    """Die Trailer, die git selbst in der Nachricht findet."""
    return subprocess.run(["git", "interpret-trailers", "--parse"], input=text,
                          capture_output=True, text=True, check=True).stdout


ABSCHLUSS = "Zutaten-Endpoint auf Domänentypen umgestellt\n\nWarum es nötig war.\n\nSession-Ende: 126\n"
MIT_CO_AUTOR = "Titel\n\nRumpf.\n\nSession-Ende: 126\nCo-Authored-By: X <x@y>\n"
OHNE_TRAILER_BLOCK = ("Titel\n\nRumpf.\n\nAbhängigkeiten-Durchsicht: 2026-10\nSession-Ende: 126\n"
                      "Co-Authored-By: X <x@y>\n")
FREMD_DANACH = "Titel\n\nRumpf.\n\nSession-Ende: 126\nNoch ein Satz.\n"
# Ohne Leerzeile und ohne abschließenden Zeilenumbruch: Der Absatz der Marke reicht bis in den
# Betreff, und die letzte Zeile ist nicht leer.
AM_BETREFF = "Titel\nRumpf.\nSession-Ende: 126"


# --- Betreff -----------------------------------------------------------------
def test_valid_closing_message_passes():
    assert pruefe(ABSCHLUSS) == []


def test_subject_over_72_chars_is_rejected():
    lang = "x" * 73
    assert pruefe(f"{lang}\n\nRumpf.\n\nSession-Ende: 126\n") == [
        commit_msg._BETREFF_LANG.format(laenge=73, maximum=72)]


def test_subject_of_exactly_72_chars_passes():
    assert pruefe(f"{'x' * 72}\n\nRumpf.\n\nSession-Ende: 126\n") == []


def test_empty_message_is_rejected():
    assert pruefe("\n\n\n") == [commit_msg._BETREFF_FEHLT]


# --- Zwischen-Commits --------------------------------------------------------
def test_commit_without_trailer_needs_no_body():
    """Nicht jeder Commit beendet eine Session – ein Zwischen-Commit darf betrefflos bleiben."""
    assert pruefe("Tippfehler in doc.py\n") == []


# --- Trailer -----------------------------------------------------------------
def test_trailer_twice_is_rejected():
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\nSession-Ende: 126\n"
    assert pruefe(text) == [commit_msg._MEHRFACH.format(anzahl=2)]


def test_wrong_session_number_is_rejected():
    """Der Fehler aus LL-S106-2: von der letzten abgeschlossenen Session weitergezählt."""
    assert pruefe("Titel\n\nRumpf.\n\nSession-Ende: 127\n") == [
        commit_msg._NUMMER_FALSCH.format(nummer=127, erwartet=126, marker=commit_msg.MARKER)]


def test_amending_the_closing_commit_is_allowed():
    """Beim Nachbessern trägt HEAD die Nummer bereits – erwartet wäre sonst schon die nächste."""
    assert pruefe("Titel\n\nRumpf.\n\nSession-Ende: 126\n",
                  erwartete_session=127, head_session=126) == []


def test_trailer_without_body_is_rejected():
    """Die Marke allein ist keine Session-Historie."""
    assert pruefe("Titel\n\nSession-Ende: 126\n") == [commit_msg._RUMPF_LEER]


def test_misspelled_trailer_is_rejected():
    """Ohne gültige Marke ist eine fast-richtige Zeile ein Vertipper, kein Prosa-Satz."""
    assert pruefe("Titel\n\nRumpf.\n\nSession Ende: 126\n") == [commit_msg._VERTIPPT]


def test_indented_trailer_is_rejected():
    assert pruefe("Titel\n\nRumpf.\n\n  Session-Ende: 126\n") == [commit_msg._VERTIPPT]


def test_trailer_outside_the_last_block_is_rejected():
    """Git parst nur den LETZTEN Absatz als Trailer-Block. Steht die Marke davor, findet
    `--format='%(trailers:key=Session-Ende)'` sie nicht – die Nummer ist dann nur noch per
    grep erreichbar, und jeder dokumentierte Abrufbefehl liefert still leer."""
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\n\nCo-Authored-By: X <x@y>\n"
    assert pruefe(text) == [commit_msg._NICHT_ZULETZT]


def test_trailer_together_with_other_trailers_passes():
    assert pruefe(MIT_CO_AUTOR) == []


def test_a_non_trailer_line_in_the_last_block_is_rejected():
    """Ein Schlüssel mit Umlaut ist kein Trailer – und eine solche Zeile macht den ganzen
    letzten Absatz für git zu Fließtext. Die Meldung nennt die Zeile, sonst sucht man sie."""
    assert pruefe(OHNE_TRAILER_BLOCK) == [
        commit_msg._KEIN_TRAILER.format(zeile="Abhängigkeiten-Durchsicht: 2026-10")]


def test_a_non_trailer_line_after_the_marker_is_rejected():
    assert pruefe(FREMD_DANACH) == [commit_msg._KEIN_TRAILER.format(zeile="Noch ein Satz.")]


def test_a_marker_attached_to_the_subject_is_rejected():
    """Der erste Absatz ist für git der Titel – eine Marke darin ist nie ein Trailer."""
    assert pruefe(AM_BETREFF) == [commit_msg._KEIN_TRAILER.format(zeile="Titel")]


def test_a_continuation_line_is_rejected_although_git_reads_it():
    """Bewusst strenger als git: Unsere Trailer brechen nie um, eine eingerückte Zeile im
    Trailer-Absatz ist eher ein Versehen als ein mehrzeiliger Wert."""
    text = "Titel\n\nRumpf.\n\nSession-Ende: 126\nCo-Authored-By: X\n  <x@y>\n"
    assert "Session-Ende: 126" in git_trailer(text)
    assert pruefe(text) == [commit_msg._KEIN_TRAILER.format(zeile="  <x@y>")]


@pytest.mark.parametrize("text", [OHNE_TRAILER_BLOCK, FREMD_DANACH, AM_BETREFF, ABSCHLUSS,
                                  MIT_CO_AUTOR])
def test_the_hook_agrees_with_git_on_the_trailer_block(text):
    """Gegen das echte Artefakt: Der Hook meldet genau dann nichts, wenn git die Marke liest –
    für die Formen, die unsere Commits tragen (Fortsetzungszeilen und `Signed-off-by:`-Mischung
    nimmt git an, der Hook bewusst nicht)."""
    geparst = git_trailer(text)
    befunde = pruefe(text)
    assert (befunde == []) == ("Session-Ende: 126" in geparst), f"Hook: {befunde}, git: {geparst!r}"


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


# --- Aufruf als Hook ---------------------------------------------------------
def test_head_session_reads_the_marker_of_the_last_commit(tmp_path):
    root = git_repo(tmp_path, ["Alt\n\nRumpf.\n\nSession-Ende: 7\n",
                               "Neu\n\nRumpf.\n\nSession-Ende: 8\nCo-Authored-By: X <x@y>\n"])
    assert commit_msg._head_session(root) == 8


def test_head_session_reads_the_whole_message(tmp_path):
    """Wie die Nummernableitung per `--grep`: Auch eine Marke im ersten Absatz eines alten
    Commits zählt."""
    assert commit_msg._head_session(git_repo(tmp_path, ["Alt\nSession-Ende: 8"])) == 8


def test_head_session_bounds_the_wait_for_git(monkeypatch, tmp_path):
    """Ein hängendes git darf den Commit nicht unbegrenzt aufhalten."""
    aufrufe = []
    monkeypatch.setattr(subprocess, "run", lambda *_a, **kwargs: aufrufe.append(kwargs) or
                        subprocess.CompletedProcess([], 0, stdout=""))
    commit_msg._head_session(tmp_path)
    assert [a.get("timeout") for a in aufrufe] == [commit_msg._GIT_TIMEOUT_S]


def test_head_session_without_marker_is_none(tmp_path):
    assert commit_msg._head_session(git_repo(tmp_path, ["Zwischenstand\n\nRumpf.\n"])) is None


def test_head_session_outside_a_repo_is_none(tmp_path):
    assert commit_msg._head_session(tmp_path) is None


@pytest.mark.parametrize("fehler", [FileNotFoundError("git"),
                                    subprocess.TimeoutExpired("git", 10)])
def test_head_session_without_a_working_git_is_none(monkeypatch, tmp_path, fehler):
    def scheitert(*_args, **_kwargs):
        raise fehler
    monkeypatch.setattr(subprocess, "run", scheitert)
    assert commit_msg._head_session(tmp_path) is None


def _hook(monkeypatch, tmp_path, nachricht: str) -> int:
    """Der Hook gegen ein Repo, dessen letzte abgeschlossene Session 5 ist. Das Repo liegt in
    einem Unterordner, damit die Nachrichtendatei nicht selbst im Repo landet."""
    (tmp_path / "repo").mkdir()
    root = git_repo(tmp_path / "repo", ["Abschluss\n\nRumpf.\n\nSession-Ende: 5\n"])
    monkeypatch.setattr(commit_msg, "repo_root", lambda: root)
    datei = tmp_path / "COMMIT_EDITMSG"
    datei.write_text(nachricht, encoding="utf-8")
    return cli_aufruf(monkeypatch, commit_msg, str(datei))


@pytest.mark.parametrize("nummer", [6, 5])   # 6: die nächste Session, 5: ein Amend
def test_the_hook_passes_the_next_session_and_an_amend(monkeypatch, tmp_path, capsys, nummer):
    assert _hook(monkeypatch, tmp_path, f"Titel\n\nRumpf.\n\nSession-Ende: {nummer}\n") == 0
    assert capsys.readouterr().err == ""


def test_the_hook_blocks_and_lists_each_finding(monkeypatch, tmp_path, capsys):
    assert _hook(monkeypatch, tmp_path, f"{'x' * 73}\n\nRumpf.\n\nSession-Ende: 9\n") == 1
    assert capsys.readouterr().err.splitlines() == [
        commit_msg._KOPF,
        "  - " + commit_msg._BETREFF_LANG.format(laenge=73, maximum=72),
        "  - " + commit_msg._NUMMER_FALSCH.format(nummer=9, erwartet=6, marker=commit_msg.MARKER),
    ]


def test_the_hook_reads_a_message_with_umlauts(monkeypatch, tmp_path, capsys):
    """An einem Umlaut scheitert ein Trailer-Schlüssel – der Hook muss ihn über den echten Pfad
    lesen können, sonst bleibt der Fall unerkannt."""
    assert _hook(monkeypatch, tmp_path, OHNE_TRAILER_BLOCK.replace("126", "6")) == 1
    assert capsys.readouterr().err.splitlines() == [
        commit_msg._KOPF,
        "  - " + commit_msg._KEIN_TRAILER.format(zeile="Abhängigkeiten-Durchsicht: 2026-10"),
    ]


# --- Umwege: Abweichungen und Sackgassen tragen Ursache und Folge -------------
# Ein notierter Umweg ohne Ursachenprüfung wiederholt sich: Die mutmut-Sperrklinke stand in vier
# Session-Commits als Abweichung, untersucht wurde sie nie (LL-S139-1). Der Hook erzwingt die
# Frage dort, wo jede Session vorbeikommt.
GANZ = "Ursache: X (geprüft: Version) Folge: behoben"

# Echter Abschnitt aus dem S136-Commit (30e4ea1), gekürzt – Form des Bestands: Liste mit
# Fortsetzungszeilen, zwei Abschnitte, Fließtext dazwischen.
S136 = ("Doku-Review in drei Läufen\n\nDrei Läufe.\n\n"
        "Sackgassen:\n"
        "- InMemory-Paket als tot entfernt: 54 von 56 Backend-Tests scheiterten zur\n"
        "  Laufzeit, das Paket hatte eine EF-Core-Versionsschere kaschiert.\n"
        "- DisableTransitiveProjectReferences eingeschaltet: Server baut nicht mehr.\n\n"
        "Abweichungen:\n"
        "- Die mutmut-Sperrklinke kommt auf check-bash-permission nicht über 266 von 672\n"
        "  Mutanten.\n\n"
        "Session-Ende: 126\n")


def umweg_befunde(text: str) -> list[str]:
    return [b for b in pruefe(text) if b.startswith("Umweg")]


def test_a_real_closing_message_without_causes_is_rejected_per_item():
    assert len(umweg_befunde(S136)) == 3


def test_items_with_cause_and_consequence_pass():
    text = (S136.replace("kaschiert.\n", f"kaschiert. {GANZ}\n")
                .replace("nicht mehr.\n", f"nicht mehr. {GANZ}\n")
                .replace("  Mutanten.\n", f"  Mutanten. {GANZ}\n"))
    assert umweg_befunde(text) == []


def test_a_continuation_line_belongs_to_its_item():
    text = f"Titel\n\nAbweichungen:\n- Lauf unvollständig.\n  {GANZ}\n"
    assert umweg_befunde(text) == []


def test_an_inline_section_is_one_item():
    text = "Titel\n\nAbweichung: Die Klinke kam nicht durch,\nalso nur Handproben.\n"
    assert umweg_befunde(text) == [commit_msg._UMWEG_OHNE.format(
        felder="`Ursache:` und `Folge:`", anfang="Die Klinke kam nicht durch,")]


def test_a_section_with_words_before_the_colon_counts():
    """„Sackgasse mit Kosten:" stand so in S135 – eine Überschrift mit Zusatz entgeht sonst."""
    assert umweg_befunde("Titel\n\nSackgasse mit Kosten: Der Entwurf war zu tief.\n")


def test_the_missing_field_is_named():
    text = "Titel\n\nAbweichungen:\n- Klinke ohne Aussage. Ursache: ungeklärt (geprüft: Version)\n"
    assert umweg_befunde(text) == [commit_msg._UMWEG_OHNE.format(
        felder="`Folge:`", anfang="Klinke ohne Aussage. Ursache: ungeklärt (geprüft: …")]


def test_a_blank_line_after_the_heading_does_not_hide_the_items():
    assert umweg_befunde("Titel\n\nAbweichungen:\n\n- Klinke ohne Aussage.\n") == [
        commit_msg._UMWEG_OHNE.format(felder="`Ursache:` und `Folge:`",
                                      anfang="Klinke ohne Aussage.")]


def test_an_empty_section_at_the_end_has_no_items():
    assert umweg_befunde("Titel\n\nAbweichungen:\n\n") == []


def test_a_section_right_below_the_subject_counts_but_the_subject_does_not():
    befunde = umweg_befunde("Abweichung: Titel\nSackgassen:\n- Entwurf zu tief.")
    assert [b.split("“")[0] for b in befunde] == ["Umweg ohne `Ursache:` und `Folge:`: „Entwurf zu tief."]


def test_a_start_of_exactly_the_maximum_length_is_not_shortened():
    punkt = "x" * commit_msg.ANFANG_MAX
    assert umweg_befunde(f"Titel\n\nAbweichung: {punkt}\n") == [commit_msg._UMWEG_OHNE.format(
        felder="`Ursache:` und `Folge:`", anfang=punkt)]


def test_prose_mentioning_a_deviation_is_not_a_section():
    assert umweg_befunde("Titel\n\nDie Abweichung vom Plan war gewollt, siehe oben.\n") == []


def test_the_hook_blocks_a_commit_with_an_unexplained_detour(monkeypatch, tmp_path, capsys):
    assert _hook(monkeypatch, tmp_path, "Titel\n\nAbweichungen:\n- Ohne Klinke.\n") == 1
    assert commit_msg._KOPF in capsys.readouterr().err


@pytest.mark.parametrize("konstante, ausweg", [
    ("_UMWEG_OHNE", "entfällt: <Grund>"),
    ("_VERTIPPT", "`Session-Ende: <NNN>`"),
    ("_NICHT_ZULETZT", "`Co-Authored-By:`"),
    ("_KEIN_TRAILER", "in den Rumpf verschieben"),
    ("_NUMMER_FALSCH", "`{marker}`"),
])
def test_each_finding_names_its_way_out(konstante, ausweg):
    """Die Tests oben vergleichen mit den Konstanten – eine geleerte bliebe dort grün."""
    assert ausweg in getattr(commit_msg, konstante)


def test_the_hook_needs_exactly_the_message_file(monkeypatch, capsys):
    assert cli_aufruf(monkeypatch, commit_msg) == 1
    assert capsys.readouterr().err == commit_msg._AUFRUF + "\n"
