"""Tests für tracker_diff.py – was ein Tracker-Schreibbefehl ändern würde, fertig zum Zeichnen.

Gegen das echte Artefakt (CGP-echtes-artefakt): Die Werkzeuge laufen mit ihrem echten `main()`,
die Fixtures sind Kopien der Bestandsdateien. Umgebogen werden nur die Pfade – auf die Kopien,
damit kein Lauf die echten Tracker berührt.
"""
import io
import json
import re
import shutil
import sys
from importlib import import_module
from pathlib import Path

import pytest

from prozesscode import td_entry as tde

obs_mod = import_module("prozesscode.obs")
td_diff = import_module("prozesscode.tracker_diff")

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture
def kopien(tmp_path, monkeypatch):
    """Kopien von tech-debt.md, AGENT_MEMORY.md und observations.md; die Werkzeuge lesen nur sie."""
    for datei in (tde.TD_FILE, tde.MEMORY_FILE, "docs/kaizen/observations.md"):
        ziel = tmp_path / datei
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / datei, ziel)
    monkeypatch.setattr(tde, "td_path", lambda root=None: tmp_path / tde.TD_FILE)
    monkeypatch.setattr(tde, "memory_path", lambda root=None: tmp_path / tde.MEMORY_FILE)
    monkeypatch.setattr(obs_mod, "obs_path",
                        lambda root=None: tmp_path / "docs/kaizen/observations.md")
    # Diese Tests prüfen die Darstellung, nicht die Edit-Prüfungen – die laufen gegen die echten
    # Tracker (eigener Block unten). An den Kopien schlügen sie teils an (Verweise im Repo),
    # teils gar nicht (Zuständigkeit am Repo-Pfad); beides sagte hier nichts aus.
    monkeypatch.setattr(td_diff, "edit_pruefungen", lambda _geschrieben, ohne=frozenset(): [])
    return tmp_path


def _erste_td_id(root: Path) -> str:
    return next(iter(tde.entry_spans((root / tde.TD_FILE).read_text(encoding="utf-8"))))


def _text(zeile, *, ohne=()) -> str:
    """Der gezeigte Text einer Zeile, ohne die Stücke mit einem der Stile in `ohne`."""
    return "".join(s["text"] for s in zeile if not set(s["stil"]) & set(ohne))


def _stuecke(zeile, stil) -> list[str]:
    return [s["text"] for s in zeile if stil in s["stil"]]


# --- Was der Befehl schriebe ------------------------------------------------------
def test_ein_geaenderter_titel_zeigt_nur_die_geaenderten_woerter(kopien):
    tid = _erste_td_id(kopien)
    befund = td_diff.befund(f'python3 -m prozesscode.td set {tid} --titel "Neuer Titel"', kopien)
    assert befund["fehler"] is None
    [datei] = befund["dateien"]
    assert datei["datei"] == tde.TD_FILE
    [block] = datei["bloecke"]
    assert block["art"] == "geaendert"
    [zeile] = block["zeilen"]
    assert _text(zeile, ohne=("weg",)) == f"{tid} — Neuer Titel"
    assert _stuecke(zeile, "neu") == ["Neuer Titel"]
    assert tid not in "".join(_stuecke(zeile, "weg"))


def test_ein_geaendertes_feld_steht_unter_der_ueberschrift_seines_eintrags(kopien):
    tid = _erste_td_id(kopien)
    eintrag = tde.get((kopien / tde.TD_FILE).read_text(encoding="utf-8"), tid)
    problem = re.search(r"^\*\*Problem:\*\* (.*)$", eintrag, re.M).group(1)
    befund = td_diff.befund(
        f"python3 -m prozesscode.td set {tid} --problem '{problem} Dazu ein Satz.'", kopien)
    kopf, feld = befund["dateien"][0]["bloecke"]
    assert kopf["art"] == "kopf"
    assert _text(kopf["zeilen"][0]).startswith(f"{tid} — ")
    assert feld["art"] == "geaendert"
    assert _stuecke(feld["zeilen"][0], "fett")[0] == "Problem:"


def test_der_diff_schreibt_nichts(kopien):
    """Gegenprobe zum Zweck: Der Befehl wird ausgewertet, nicht ausgeführt."""
    vorher = {p: p.read_text(encoding="utf-8") for p in kopien.rglob("*.md")}
    td_diff.befund(f'python3 -m prozesscode.td set {_erste_td_id(kopien)} --titel "X"', kopien)
    assert {p: p.read_text(encoding="utf-8") for p in kopien.rglob("*.md")} == vorher


def test_jede_geschriebene_datei_erscheint_einzeln(kopien):
    """`td set … --faellig jetzt` schreibt zusätzlich den Prioritäten-Punkt in AGENT_MEMORY."""
    tid = _erste_td_id(kopien)
    befund = td_diff.befund(f'python3 -m prozesscode.td set {tid} --faellig "jetzt – Test" '
                            f'--done "erledigt, wenn X"', kopien)
    assert [d["datei"] for d in befund["dateien"]] == [tde.TD_FILE, tde.MEMORY_FILE]


def test_ein_neuer_eintrag_kommt_als_neue_zeilen(kopien):
    befund = td_diff.befund(
        "python3 -m prozesscode.obs add --titel T --quelle User --impact MITTEL "
        "--haeufigkeit gelegentlich --kategorie TOOLING --kontext Doku --beobachtung B "
        "--zusammen-erledigen keiner --aufschubgrund 'User – später'", kopien)
    bloecke = befund["dateien"][0]["bloecke"]
    assert {b["art"] for b in bloecke} == {"neu"}
    zeilen = [_text(z) for b in bloecke for z in b["zeilen"]]
    assert "• Beobachtung: B" in zeilen


def test_ein_neuer_eintrag_ist_als_ganzer_eintrag_markiert(kopien):
    """Der Mod zeigt dann einen Hinweis „neuer Eintrag" statt jede Zeile grün zu hinterlegen (S143)."""
    befund = td_diff.befund(
        "python3 -m prozesscode.obs add --titel T --quelle User --impact MITTEL "
        "--haeufigkeit gelegentlich --kategorie TOOLING --kontext Doku --beobachtung B "
        "--zusammen-erledigen keiner --aufschubgrund 'User – später'", kopien)
    [block] = [b for b in befund["dateien"][0]["bloecke"]
               if any(_text(z).startswith("OBS-") for z in b["zeilen"])]
    assert block["eintrag"] is True


def test_ein_entfernter_eintrag_ist_als_ganzer_eintrag_markiert(kopien):
    tid = _erste_td_id(kopien)
    befund = td_diff.befund(f"python3 -m prozesscode.td remove {tid}", kopien)
    assert befund["fehler"] is None
    [block] = [b for b in befund["dateien"][0]["bloecke"] if b["art"] == "weg"]
    assert block["eintrag"] is True


def test_neue_zeilen_in_einem_eintrag_sind_kein_ganzer_eintrag():
    """Gegenprobe: Ein hinzugefügtes Feld bleibt eine grün hinterlegte Zeile."""
    alt = "## OBS-S1-1 – Titel\n- Status: NEU\n"
    neu = "## OBS-S1-1 – Titel\n- Status: NEU\n- Bezug: LL-S1-1\n"
    [kopf, block] = td_diff.bloecke(alt, neu)
    assert (kopf["art"], block["art"]) == ("kopf", "neu")
    assert block["eintrag"] is False


def test_ein_scheiternder_befehl_nennt_den_grund_statt_eines_diffs(kopien):
    befund = td_diff.befund("python3 -m prozesscode.td set TD-S000-0 --titel X", kopien)
    assert befund["dateien"] == []
    assert "TD-S000-0" in befund["fehler"]


# --- Edit-Prüfungen vor der Freigabe (OBS-S136-3) ------------------------------------
# Gegen die echten Tracker im Repo statt gegen Kopien: Die Edit-Prüfungen entscheiden ihre
# Zuständigkeit am Pfad relativ zum Repo, eine Kopie unter tmp_path sähen sie nie – der Test
# wäre grün, ohne dass eine Prüfung lief. Sicher, weil befund() nichts schreibt (siehe
# test_der_diff_schreibt_nichts).

def _obs_add(beobachtung: str) -> str:
    return ("python3 -m prozesscode.obs add --titel T --quelle User --impact MITTEL "
            "--haeufigkeit gelegentlich --kategorie TOOLING --kontext Doku "
            f"--beobachtung '{beobachtung}' --zusammen-erledigen keiner "
            "--aufschubgrund 'User – später'")


def test_text_der_eine_edit_pruefung_verletzt_wird_vor_der_freigabe_abgewiesen():
    # // Given ein Eintrag, der auf einen Abschnitt per Nummer statt per Name verweist
    befehl = _obs_add("siehe [Schritt 5](process.md#KPR-drain)")  # ordinal-ok – Testeingabe
    # // When der Mod den Befehl vor dem Freigabedialog berechnet
    befund = td_diff.befund(befehl)
    # // Then weist er ihn mit der Meldung der Gliederungsprüfung ab, statt einen Diff zu zeigen
    assert befund["dateien"] == []
    assert befund["fehler"].startswith(td_diff.PRUEFUNG_SCHLAEGT_AN)
    assert "Gliederungsnummer" in befund["fehler"]


def test_sauberer_obs_text_besteht_die_edit_pruefungen():
    # // Given ein gewöhnlicher neuer Eintrag ohne Regelverstoß
    # // When der Mod ihn gegen den echten Tracker berechnet
    befund = td_diff.befund(_obs_add("Ein Werkzeug meldet zu wenig."))
    # // Then lässt keine Edit-Prüfung ihn scheitern – auch die für Handeinträge gebauten nicht
    assert befund["fehler"] is None
    assert befund["dateien"]


def test_sauberer_td_text_besteht_die_edit_pruefungen():
    # // Given ein neuer TD-Eintrag mit gültiger Fälligkeit (td pflegt AGENT_MEMORY nicht mit)
    befehl = ("python3 -m prozesscode.td add --titel T --faellig 'Phase:MVP – vorher nicht nötig' "
              "--problem P --behebung B --aufschubgrund 'User – später'")
    # // When der Mod ihn gegen den echten Tracker berechnet
    befund = td_diff.befund(befehl)
    # // Then lässt keine Edit-Prüfung ihn scheitern
    assert befund["fehler"] is None


def _erste_id(datei: str, muster: str) -> str:
    ids = re.findall(muster, (REPO / datei).read_text(encoding="utf-8"), re.M)
    assert ids, f"Testvoraussetzung: {datei} braucht mindestens einen Eintrag"
    return ids[0]


@pytest.fixture
def verweis_auf(tmp_path, monkeypatch):
    """Ein Mini-Repo, in dem genau eine Datei auf die übergebene ID verweist.

    Die Verweissuche liest ihre Repo-Wurzel aus einer Modulvariablen; umgebogen auf tmp_path
    findet sie genau diesen Verweis, unabhängig davon, was der echte Bestand gerade enthält –
    sonst müsste der Test still überspringen, sobald kein Eintrag mehr referenziert ist.
    """
    refs = import_module("prozesscode.hooks.check-dangling-refs")
    monkeypatch.setattr(refs, "_REPO_ROOT", tmp_path)

    def anlegen(eid: str) -> None:
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "verweis.md").write_text(f"Siehe {eid}.\n", encoding="utf-8")
    return anlegen


def test_td_remove_eines_referenzierten_eintrags_wird_vor_der_freigabe_abgewiesen(verweis_auf):
    # // Given ein TD-Eintrag, auf den noch verwiesen wird
    tid = _erste_id(tde.TD_FILE, r"^## (TD-S\d{3}-\d+)")
    verweis_auf(tid)
    # // When `td remove` ihn löschen will
    befund = td_diff.befund(f"python3 -m prozesscode.td remove {tid}")
    # // Then greift die Verweisprüfung, die bisher nur bei Edit lief
    assert "Dangling-Referenzen" in befund["fehler"]
    assert "docs/verweis.md" in befund["fehler"]


def test_trotz_verweisen_wird_von_der_verweispruefung_nicht_kassiert(verweis_auf):
    # // Given ein OQ-Eintrag, auf den noch verwiesen wird
    oid = _erste_id("docs/open-questions.md", r"^## (OQ-S\d{3}-\d+)")
    verweis_auf(oid)
    # // When er ausdrücklich trotz Verweisen gelöscht wird
    befund = td_diff.befund(f"python3 -m prozesscode.oq remove {oid} --trotz-verweisen")
    # // Then lässt die Prüfkette den Befehl durch – über die echte Kette, nicht über eine Attrappe
    assert befund["fehler"] is None


def test_ohne_trotz_verweisen_bleibt_das_loeschen_gesperrt(verweis_auf):
    # // Given derselbe referenzierte OQ-Eintrag
    oid = _erste_id("docs/open-questions.md", r"^## (OQ-S\d{3}-\d+)")
    verweis_auf(oid)
    # // When er ohne den Schalter gelöscht werden soll
    befund = td_diff.befund(f"python3 -m prozesscode.oq remove {oid}")
    # // Then weist schon das Werkzeug ihn ab (Gegenstück zum vorigen Test)
    assert "wird noch referenziert" in befund["fehler"]


def test_die_auslassung_nennt_einen_check_den_es_gibt():
    # Ein umbenannter Check machte die Auslassung lautlos wirkungslos; collect_reasons wirft
    # zwar bei unbekannten Namen, aber erst, wenn jemand --trotz-verweisen benutzt.
    assert td_diff._OHNE_TROTZ_VERWEISEN <= set(td_diff._dispatch.CHECKS)


def test_jede_geschriebene_datei_geht_durch_die_pruefkette(monkeypatch):
    # // Given ein Befehl, der zwei Dateien schreibt (`td set --faellig jetzt` pflegt AGENT_MEMORY mit)
    tid = _erste_id(tde.TD_FILE, r"^## (TD-S\d{3}-\d+)")
    geprueft: list[str] = []
    monkeypatch.setattr(td_diff._dispatch, "collect_reasons", lambda data, ohne=frozenset():
                        geprueft.append(Path(data["tool_input"]["file_path"]).name) or [])
    # // When der Mod ihn berechnet
    td_diff.befund(f'python3 -m prozesscode.td set {tid} --faellig "jetzt – Test" --done "X"')
    # // Then wird jede der beiden Dateien geprüft, nicht nur die erste
    assert sorted(geprueft) == ["AGENT_MEMORY.md", "tech-debt.md"]


def test_ein_werfender_check_faellt_nicht_still_aus(monkeypatch):
    # // Given eine Prüfkette mit einem Check, der wirft (fail-open: er darf nichts blockieren)
    class Kaputt:
        @staticmethod
        def check(_data):
            raise RuntimeError("defekt")
    monkeypatch.setattr(td_diff._dispatch, "CHECKS", ["check-kaputt"])
    monkeypatch.setattr(td_diff._dispatch, "import_module", lambda _name: Kaputt)
    # // When ein Tracker-Befehl berechnet wird
    befund = td_diff.befund(_obs_add("Ein Werkzeug meldet zu wenig."))
    # // Then blockiert er nicht, aber die Warnung im Pane nennt den ausgefallenen Check
    assert befund["fehler"] is None
    assert "check-kaputt" in befund["warnung"]


def test_ungueltige_argumente_nennen_die_meldung_von_argparse(kopien):
    befund = td_diff.befund("python3 -m prozesscode.obs add --titel nur", kopien)
    assert befund["dateien"] == []
    assert "required" in befund["fehler"]


@pytest.mark.parametrize("befehl", [
    "ls -la",
    "python3 -m prozesscode.td get TD-S080-1",
    "python3 -m prozesscode.td list",
    'python3 -m prozesscode.td set "unbalanciert',
])
def test_kein_tracker_schreibbefehl_liefert_nichts(kopien, befehl):
    assert td_diff.befund(befehl, kopien) is None


def test_shell_metazeichen_tragen_eine_warnung(kopien):
    """Die Shell wertet `$(…)` aus, bevor das Script es sieht – der Diff zeigt es literal."""
    befund = td_diff.befund(
        f'python3 -m prozesscode.td set {_erste_td_id(kopien)} --titel "$(date)"', kopien)
    assert "Shell" in befund["warnung"]


# --- Bausteine: Wort-Diff und Markdown ---------------------------------------------
def test_wort_diff_markiert_nur_die_geaenderten_woerter():
    zeile = td_diff.wort_diff("eins zwei drei", "eins vier drei")
    assert _text(zeile, ohne=("weg",)) == "eins vier drei"
    assert _stuecke(zeile, "weg") == ["zwei"]
    assert _stuecke(zeile, "neu") == ["vier"]


def test_kaum_aehnliche_zeilen_kommen_ganz_statt_als_wortsalat():
    """Ein ganz neuer Text teilt mit dem alten nur Füllwörter; verschränkt wäre er unlesbar."""
    alt = ("- Beobachtung: Gemessen in S130: der Lauf bewertet nur rund 241 von 583 Mutanten, "
           "der Rest bleibt offen, und der Hinweis führt nicht zum Ziel.")
    neu = "- Beobachtung: Gegenprobe für den Scroll-Test – bitte ablehnen."
    [weg, hinzu] = td_diff.bloecke(alt, neu)
    assert (weg["art"], hinzu["art"]) == ("weg", "neu")
    assert _text(hinzu["zeilen"][0]) == "• Beobachtung: Gegenprobe für den Scroll-Test – bitte ablehnen."


def test_aehnliche_zeilen_bekommen_den_wort_diff():
    """Gegenprobe zur Schwelle: Eine kleine Änderung in einer langen Zeile bleibt ein Wort-Diff."""
    alt = "**Problem:** Der Lauf bewertet nur rund 241 von 583 Mutanten, der Rest bleibt offen."
    neu = "**Problem:** Der Lauf bewertet nur rund 266 von 672 Mutanten, der Rest bleibt offen."
    [block] = td_diff.bloecke(alt, neu)
    assert block["art"] == "geaendert"


def test_wort_diff_behaelt_das_markdown_der_neuen_zeile():
    zeile = td_diff.wort_diff("**Fällig:** Phase:MVP – alt", "**Fällig:** Phase:MVP – neu")
    assert _stuecke(zeile, "fett") == ["Fällig:"]
    assert _text(zeile, ohne=("weg",)) == "Fällig: Phase:MVP – neu"


@pytest.mark.parametrize("roh, gezeigt, stile", [
    ("**fett** rest", "fett rest", {"fett": ["fett"]}),
    ("mit `qs` drin", "mit qs drin", {"code": ["qs"]}),
    ("*kursiv* x", "kursiv x", {"kursiv": ["kursiv"]}),
    ("[Text](https://x.y)", "Text", {}),
    ("## TD-S1-1 — Titel", "TD-S1-1 — Titel", {"fett": ["TD-S1-1 — Titel"]}),
    ("- Status: NEU", "• Status: NEU", {"fett": ["Status:"]}),
    ("  - frei ohne Feldnamen", "  • frei ohne Feldnamen", {}),
    ("**offen ohne Ende", "**offen ohne Ende", {}),
    ("check_name bleibt", "check_name bleibt", {}),
    ("`**kein fett in code**`", "**kein fett in code**", {"code": ["**kein fett in code**"]}),
])
def test_markdown_wird_aufgeloest_und_unbekanntes_bleibt_roh(roh, gezeigt, stile):
    zeile = td_diff.markdown(roh)
    assert _text(zeile) == gezeigt
    for stil, stuecke in stile.items():
        assert _stuecke(zeile, stil) == stuecke
    assert not {"fett", "code", "kursiv"} - set(stile) & {s for t in zeile for s in t["stil"]}


# --- Aufrufpfad ----------------------------------------------------------------------
@pytest.mark.aufrufpfad("tracker_diff")
def test_main_liest_den_befehl_von_stdin_und_gibt_json_aus(kopien, monkeypatch, capsys):
    tid = _erste_td_id(kopien)
    monkeypatch.setattr(sys, "stdin", io.StringIO(f'python3 -m prozesscode.td set {tid} --titel "Y"'))
    assert td_diff.main([]) == 0
    befund = json.loads(capsys.readouterr().out)
    assert befund["dateien"][0]["datei"].endswith(tde.TD_FILE)
    assert befund["dateien"][0]["bloecke"][0]["art"] == "geaendert"


@pytest.mark.aufrufpfad("tracker_diff")
def test_main_ohne_tracker_befehl_gibt_null_aus(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("ls"))
    assert td_diff.main([]) == 0
    assert json.loads(capsys.readouterr().out) is None


def test_die_werkzeuge_schreiben_nur_ueber_write_text():
    """Die Grundlage des Diffs: Was an `Path.write_text` vorbei schriebe, sähe er nicht."""
    for name in ("obs", "td", "oq", "lessons"):
        quelle = (REPO / "prozesscode" / f"{name}.py").read_text(encoding="utf-8")
        assert not re.search(r"\bopen\(|write_bytes|shutil\.", quelle), name
