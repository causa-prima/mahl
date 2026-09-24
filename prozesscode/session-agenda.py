#!/usr/bin/env python3
"""session-agenda.py – was verlangt zum Session-Start eine Entscheidung?

Einstiegspunkt des SessionStart-Hooks (ersetzt `session-start.sh`; Rangfolge und Begründung
kanonisch in `docs/kaizen/process.md`, Abschnitt „Session-Agenda").

Die Ausgabe zerfällt in fünf **Injektionsblöcke** (`INJEKTIONS_BLOECKE`), von denen jeder
EINZELN als SessionStart-Hook registriert ist – drei aus `principles.md`, die Allow-Liste
und die Agenda selbst.

Der Grund ist eine harte Grenze des Runtimes, die er kommentarlos durchsetzt (Einheit,
Empirie und Quellen an `CAP` unten). Bis S128 lief alles in EINEM Block mit 23.123 units –
die Agenda stand am Ende und kam damit in KEINER Session an, ohne dass es je auffiel. Weil
der Cap PRO registriertem Command gilt, löst die Aufteilung das.

Zwei Folgen davon durchziehen den Code:

- **Es gibt keine Reihenfolge mehr.** Hooks eines Events laufen parallel und treffen
  gemischt ein. Jeder Block nennt sich deshalb selbst; Position bedeutet nichts.
- **Jeder Block bewacht seine Größe.** `BUDGET` liegt unter `CAP`, damit Wachstum auffällt,
  solange noch Luft ist – und nicht durch sein Ausbleiben.

Innerhalb der Agenda:

- **Nächste Aufgabe** – GENAU EINE, nach fester Rangfolge. Ziel ist Fokus: Ein Session-Start
  mit fünf konkurrierenden Aufträgen zeigt in keine Richtung. Der Text ist BUCHSTÄBLICH das,
  was `--only <name>` für dieses Modul ausgäbe – dieselbe Zeichenkette, keine Zusammenfassung
  davor. Deshalb muss jeder Modulinhalt für sich selbsterklärend sein.
- **Einzeiler** – je unterdrücktem Modul eine Zeile MIT SEINEM MESSWERT und der Abrufbefehl.
  Ein unterdrückter Block darf nie verschwinden: Man kann nicht anfordern, wovon man nicht
  weiß, dass es existiert – und der User übersteuert regelmäßig (in S114/S115 nachweislich
  zugunsten des Drains gegen die fällige Retro).

Bewusst KEINE Extremschwellen in der Rangfolge (etwa „extrem volles Backlog schlägt Retro"):
Die verfügbaren Messpunkte können sie nicht kalibrieren – bei S116 zeigten beide Signale
gleichzeitig auf die Retro, die Erklärungen sind konfundiert. Eine unkalibrierbare Schwelle
liegt falsch, und falsch liegen kostet dasselbe wie keine Schwelle zu haben (eine Übersteuerung
durch den User), zusätzlich aber Pflege und Erklärung.

Schnittstelle:
    session-agenda.py --block <name>  EIN Injektionsblock – so ruft der Hook (fünfmal)
    session-agenda.py                 alle Blöcke am Stück (Sicht für Menschen; diese
                                      Ausgabe liegt mit Absicht über dem Cap und wird nie
                                      als Ganzes injiziert)
    session-agenda.py --only <id>     ein Modul in voller Tiefe (Übersteuern)
    session-agenda.py --list          Modulnamen

Ausfallverhalten: Jedes Modul scheitert EINZELN und sichtbar; die Agenda läuft weiter. Ein
Totalausfall wäre von „nichts zu tun" ununterscheidbar.
"""
import argparse
import io
import re
import subprocess
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path

from . import anchors
from . import open_questions
from . import ordinale
from . import td_anchors
from . import td_due
from .obs_parse import parse_entries
from .repo_kontext import current_session

# obs-drain trägt einen Bindestrich (CLI-Name) und ist deshalb nicht per `from . import`
# erreichbar – `import_module` nimmt den Namen dagegen als Zeichenkette. Der Trigger lebt
# trotzdem dort, nicht hier: Wer den Drain-Satz berechnet, entscheidet auch, ob er eine Session
# beansprucht – zwei Stimmen dazu wären eine Quelle für stille Divergenz.
_drain = import_module("prozesscode.obs-drain")

ROOT = Path(__file__).resolve().parent.parent

# Modul-Arten. RAHMEN und ZUSTAND werden immer gerendert, aber an verschiedenen Stellen:
# RAHMEN als eigener Block VOR der Agenda, ZUSTAND als Kopf INNERHALB der Agenda.
RAHMEN, ZUSTAND, AUFGABE, STUB = "rahmen", "zustand", "aufgabe", "stub"


@dataclass
class Block:
    """Ergebnis eines Moduls. `stub` ist die Einzeiler-Fassung, `inhalt` die volle."""
    stub: str
    inhalt: str = ""
    beansprucht: bool = False   # beansprucht den Aufgaben-Slot?


# Claude Code verwirft Hook-stdout oberhalb dieser Grenze KOMMENTARLOS: Der Text wandert in
# eine Datei, injiziert wird eine 2.000er-Vorschau, der Hook bekommt Exit 0 und kein Signal.
# Empirisch bestimmt in anthropics/claude-code#84021 (10.000 kommt durch, 10.001 spillt);
# gemessen wird JS `.length`, also UTF-16 code units – NICHT Bytes und NICHT Zeichen.
# Die Grenze ist undokumentiert, nicht konfigurierbar (#50571, #51537) und gilt PRO
# registriertem Command – daher die Aufteilung auf mehrere SessionStart-Hooks.
CAP = 10_000
# Selbstauflage mit Luft: principles.md wächst mit jeder Retro. Wer erst bei CAP nachschneidet,
# erfährt vom Überlauf durch sein Ausbleiben. 80 % ist eine nachträglich verschobene Latte –
# bei 70 % riss der größte Block um 38 units, und die Alternative wäre ein Anker mitten in
# `KPI-kommunikation` gewesen: eine Gliederung, die dem Cap folgt statt dem Inhalt.
BUDGET = 8_000
# So viel injiziert der Runtime im Spill-Fall. Alles, was den Ausfall melden soll, muss
# hierhin passen, sonst verschwindet die Meldung mit dem Rest.
VORSCHAU = 2_000


def u16(text: str) -> int:
    """Länge in UTF-16 code units – die Einheit, in der der Cap misst.

    Astrale Zeichen (Emoji) zählen zwei. `len()` unterschätzt sie deshalb, `len(encode())`
    überschätzt jeden Umlaut. Beides führt zu einem Guard, der etwas anderes misst als die
    Grenze, gegen die er schützt.
    """
    return sum(2 if ord(z) > 0xFFFF else 1 for z in text)


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8") if pfad.is_file() else ""


def _laufe(*befehl: str) -> str:
    """Fremdes Programm ausführen (git); stdout zurück.

    Für eigene Paketmodule ist `_modulausgabe` zuständig – nicht dieser Weg.
    Fehler wirft – der Rahmen fängt ihn je Modul.
    """
    ergebnis = subprocess.run(befehl, capture_output=True, text=True, cwd=ROOT)
    if ergebnis.returncode != 0:
        raise RuntimeError(f"{' '.join(befehl)} → Exit {ergebnis.returncode}: "
                           f"{ergebnis.stderr.strip()[:200]}")
    return ergebnis.stdout.rstrip("\n")


def _modulausgabe(modul: str, *argv: str) -> str:
    """Die CLI eines eigenen Paketmoduls im selben Prozess aufrufen; ihre Ausgabe zurück.

    Statt `python3 -m prozesscode.<modul>`: Der Subprozess stammt aus der Zeit, als der
    Prozess-Code nicht als Paket importierbar war. Er kostet je Session-Start einen
    Interpreterstart pro Modul – und im Mutantenbaum von mutmut lädt er den instrumentierten
    Code ohne dessen Laufzeit und reißt den Lauf mit, bevor ein Mutant bewertet ist.

    Ein von Null verschiedener Rückgabewert wirft, wie beim Subprozess auch; der Rahmen
    fängt ihn je Modul ab, sodass ein Ausfall die übrigen Blöcke nicht mitnimmt.
    """
    modul_obj = import_module(f"prozesscode.{modul}")
    puffer = io.StringIO()
    try:
        with redirect_stdout(puffer):
            code = modul_obj.main(list(argv))
    except SystemExit as ende:  # argparse beendet bei --help und bei Argumentfehlern
        code = ende.code or 0
    if code:
        raise RuntimeError(f"prozesscode.{modul} {' '.join(argv)} → Exit {code}: "
                           f"{puffer.getvalue().strip()[:200]}")
    return puffer.getvalue().rstrip("\n")


# --- Rahmen-Blöcke -----------------------------------------------------------

_HTML_KOMMENTAR = re.compile(r"<!--.*?-->\n*", re.S)


def ohne_kommentare(text: str) -> str:
    """HTML-Kommentare entfernen.

    Sie tragen Pflege-Metadaten für den *Schreibenden* (`wann-lesen`, `wann-schreiben`,
    Aufnahmekriterium) – für den lesenden Agenten sind sie in jeder Session dieselben
    fünf Zeilen ohne Handlungsbezug. Das Kriterium, wann etwas nach `principles.md`
    gehört, steht ohnehin im Skill `kaizen`.
    """
    return _HTML_KOMMENTAR.sub("", text).strip()


PRINCIPLES = ROOT / "docs" / "kaizen" / "principles.md"

_ANKER = re.compile(r'^<a id="([^"]+)"></a>[ \t]*$', re.M)


def modul_principles() -> Block:
    text = _lies(PRINCIPLES)
    if not text:
        raise FileNotFoundError("docs/kaizen/principles.md fehlt")
    return Block(stub="principles.md", inhalt=ohne_kommentare(text))


def modul_bash_allowlist() -> Block:
    # Direkt importiert statt als Subprozess: Der Hook liegt seit S129 im Paket und ist
    # damit ladbar. Der Bindestrich im Modulnamen schließt `import` aus, `import_module`
    # nicht.
    hook = import_module("prozesscode.hooks.check-bash-permission")
    return Block(stub="Bash-Allow-Liste", inhalt=hook.allow_list_text())


# --- principles.md in Injektionsblöcke schneiden ------------------------------
# Die Datei ist mit 15.199 units allein 152 % des Caps – sie passt in keinen einzelnen
# Hook und muss geschnitten werden. Geschnitten wird an den ANKERN, nicht an Zeilen oder
# Positionen: Ein umbenannter Titel oder ein umsortierter Abschnitt bricht den Zuschnitt
# dann nicht. Das ist dieselbe Zusage, die `KPI-doku-referenzen` für Verweise macht.

def _principles_teile() -> tuple[str, dict[str, str]]:
    """(Vorspann, Abschnittstext je Anker). Eine Zerlegung für alle Nutzer – zwei
    Zerlegungen könnten unbemerkt verschieden ausfallen."""
    text = ohne_kommentare(_lies(PRINCIPLES))
    if not text:
        raise FileNotFoundError("docs/kaizen/principles.md fehlt")
    treffer = list(_ANKER.finditer(text))
    vorspann = text[:treffer[0].start()].strip() if treffer else text
    teile: dict[str, str] = {}
    for i, marke in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        teile[marke.group(1)] = text[marke.start():ende].strip()
    return vorspann, teile


def principles_anker() -> list[str]:
    """Alle Anker in Dateireihenfolge."""
    return list(_principles_teile()[1])


# Welcher Abschnitt in welchen Block. Der AUFFANGBLOCK nimmt alles Ungenannte auf: Ein NEU
# angelegter Abschnitt darf nicht zwischen die Blöcke fallen – er verschwände lautlos, also
# in derselben Weise, gegen die diese ganze Aufteilung gebaut ist.
PRINCIPLES_VERTEILUNG: dict[str, list[str]] = {
    "verhalten": ["KPI-review-prozess", "KPI-prozess-disziplin"],
    "doku": ["KPI-doku-referenzen"],
    "kommunikation": [],
}
AUFFANGBLOCK = "kommunikation"


def principles_zuschnitt() -> dict[str, list[str]]:
    verteilt = {block: list(anker) for block, anker in PRINCIPLES_VERTEILUNG.items()}
    benannt = {a for anker in verteilt.values() for a in anker}
    verteilt[AUFFANGBLOCK] += [a for a in principles_anker() if a not in benannt]
    return verteilt


def _principles_block(name: str) -> str:
    vorspann, teile = _principles_teile()
    anker = principles_zuschnitt()[name]
    stuecke = [teile[a] for a in anker if a in teile]
    # Der Vorspann (Dateititel) hängt am ersten Block – in jedem Block stünde er viermal.
    if name == next(iter(PRINCIPLES_VERTEILUNG)) and vorspann:
        stuecke.insert(0, vorspann)
    return "\n\n".join(stuecke)


# --- Zustand (Kopf der Agenda) -----------------------------------------------

def modul_memory_state() -> Block:
    """Phase, Story und nächster Lauf – winzig und immer relevant.

    Trägt bewusst KEINEN Stub: Der Block wird ungekürzt gerendert, eine Kurzfassung
    daneben wäre dieselbe Information zweimal.
    """
    text = _modulausgabe("next_run", "--render", str(ROOT / "docs" / "AGENT_MEMORY.md"))
    zeilen = [z for z in text.splitlines()
              if z.startswith(("**Phase:", "**Aktuelle Story:", "**Nächster Lauf:"))]
    return Block(stub="", inhalt="\n".join(zeilen) or "(kein Zustand lesbar)")


def modul_repo_state() -> Block:
    """Arbeitsbaum und letzte Commits.

    Beantwortet „liegt noch etwas offen, wo stehe ich" ohne Tool-Call – der Agent hat das
    bis S128 in fast jeder Session selbst abgefragt, und zwar als Erstes. Der Arbeitsbaum
    steht dabei VOR den Commits: Uncommittetes ist das, was eine Entscheidung verlangt,
    die Historie nur Orientierung. Bewusst ohne Stub (wie `memory-state`) – der Block ist
    winzig und immer relevant, eine Kurzfassung daneben wäre dieselbe Information zweimal.
    """
    status = _laufe("git", "status", "--short")
    offen = status.splitlines()
    zeilen = ["**Arbeitsbaum:** " + ("sauber" if not offen
                                     else f"{len(offen)} Datei(en) uncommitted")]
    # Gedeckelt: Bei einem großen Umbau ersetzte die Dateiliste sonst die Agenda.
    zeilen += [f"  {z}" for z in offen[:8]]
    if len(offen) > 8:
        zeilen.append(f"  … und {len(offen) - 8} weitere (git status)")
    zeilen.append("**Letzte Commits:** " + " | ".join(
        _laufe("git", "log", "--oneline", "-3").splitlines()))
    return Block(stub="", inhalt="\n".join(zeilen))


# --- Aufgaben-Kandidaten (in Rangfolge) --------------------------------------
# `inhalt` ist hier zugleich die Ausgabe von `--only <name>` UND der Aufgabentext der
# Agenda. Er muss deshalb ohne jede Rahmenzeile sagen, worum es geht und was zu tun ist.

def modul_retro() -> Block:
    text = _modulausgabe("jenga_score")
    faellig = "RETRO FÄLLIG" in text
    score = text.splitlines()[0] if text else "Jenga-Score unbekannt"
    return Block(
        stub=f"{score} (fällig ≤ 0)",
        inhalt=f"Retro – {score}\n→ Session mit Skill `kaizen` beginnen.",
        beansprucht=faellig,
    )


def modul_obs_drain() -> Block:
    """Der Drain beansprucht den Slot, wenn `obs-drain.triggers()` erfüllt ist.

    Die Entscheidung lebt bewusst dort, nicht hier: Wer den Drain-Satz berechnet, weiß auch, ob
    er eine Session wert ist. Herleitung: docs/kaizen/process.md, „Lanes und Trigger".
    """
    text = _modulausgabe("obs-drain")
    eintraege = parse_entries(_lies(ROOT / "docs" / "kaizen" / "observations.md"))
    b = sum(1 for e in eintraege if e["status"].upper().startswith("NEU"))
    wuerdig = sum(len(u) for u in _drain.wert_einheiten(
        [e for e in eintraege if e["status"].upper().startswith("NEU")]))
    return Block(
        stub=f"OBS-Drain: Backlog {b} drainbar, davon {wuerdig} behandlungswürdig",
        inhalt=text,
        beansprucht=_drain.triggers(eintraege, current_session(ROOT)),
    )


JETZT = "Fällig: jetzt"


def prioritaets_eintraege(abschnitt: str) -> list[list[str]]:
    """Die Liste als Zeilenblöcke; ein Eintrag beginnt mit `- **` und läuft bis zum nächsten."""
    eintraege: list[list[str]] = []
    for zeile in abschnitt.splitlines():
        if zeile.startswith("- **"):
            eintraege.append([zeile])
        elif eintraege and zeile.strip():
            eintraege[-1].append(zeile)
    return eintraege


def rendere_prioritaeten(eintraege: list[list[str]]) -> str:
    """Obersten Eintrag voll, den Rest als Kurzform.

    Die Liste als Ganzes ist ein Terminplan, kein Auftrag – neun Punkte im Volltext wären
    wieder die konkurrierenden Aufträge, gegen die die Rangfolge gebaut ist. Voll gezeigt
    wird der erste `Fällig: jetzt`-Punkt (das ist der Auslöser), sonst der erste überhaupt.
    Kurzform = alles vor dem ersten ` · `, also Titel + Fälligkeit.
    """
    if not eintraege:
        return "(keine Prioritäten notiert)"
    jetzt = [e for e in eintraege if JETZT in e[0]]
    oben = (jetzt or eintraege)[0]
    zeilen = [f"Nächste Priorität ({len(jetzt)} von {len(eintraege)} tragen `{JETZT}`):", ""]
    zeilen += oben
    rest = [e for e in eintraege if e is not oben]
    if rest:
        zeilen += ["", "Danach (Kurzform; Volltext: docs/AGENT_MEMORY.md → Nächste Prioritäten):"]
        zeilen += [f"  {e[0].split(' · ')[0]}" for e in rest]
    return "\n".join(zeilen)


def modul_priorities() -> Block:
    """Die „Nächste Prioritäten"-Liste. Beansprucht den Slot, wenn ein Punkt `Fällig: jetzt` trägt."""
    text = _modulausgabe("next_run", "--render", str(ROOT / "docs" / "AGENT_MEMORY.md"))
    # TD-Punkte stehen in AGENT_MEMORY nur als Platzhalter (ID + Done); Titel und Fälligkeit
    # werden hier aus tech-debt.md aufgelöst, damit sie nur an einer Stelle leben und nicht
    # driften können (OBS-S118-1). Fällt das Auflösen aus, bleibt der Platzhalter stehen –
    # sichtbar, statt den Punkt zu verschlucken.
    try:
        from . import td_entry
        text = td_entry.memory_aufloesen(
            text, td_entry.td_path().read_text(encoding="utf-8"))
    except Exception as fehler:  # noqa: BLE001 – ein Modulfehler darf die Agenda nicht kippen
        text += f"\n\n(Warnung: TD-Platzhalter nicht aufgelöst – {fehler.__class__.__name__})"

    eintraege = prioritaets_eintraege(_abschnitt(text, "## Nächste Prioritäten"))
    jetzt = sum(1 for e in eintraege if JETZT in e[0])
    # Wortwahl mit Bedacht (S125): Der Stub wird ohne den erklärenden AGENT_MEMORY-Header
    # injiziert. „4× `Fällig: jetzt`" liest sich dort wie „seit vier Sessions überfällig" –
    # der Anker sagt aber nur, dass kein Ereignis mehr aussteht. Dass diese Punkte hinter
    # Retro und Drain warten, ist die designte Rangfolge und kein Rückstand.
    return Block(
        stub=f"Prioritäten: {len(eintraege)} offen, davon {jetzt} anstehend "
             f"(`{JETZT}` = wartet auf kein Ereignis mehr – nicht „überfällig“)",
        inhalt=rendere_prioritaeten(eintraege),
        beansprucht=jetzt > 0,
    )


def modul_next_run() -> Block:
    """Offene Läufe DER AKTUELLEN STORY.

    Ohne `--story` zählt `next_run.py` auch Szenarien fremder Feature-Dateien mit; ungetaggte
    Szenarien (z.B. in `interaction.feature`, Scope „nach MVP") gelten dort als eigener offener
    Einzel-Lauf. Die Aufgabe behauptete dann einen Lauf, den die laufende Story nicht hat.
    """
    from prozesscode import next_run
    story = next_run.extract_story(_lies(ROOT / "docs" / "AGENT_MEMORY.md"))
    if story is None:
        return Block(stub="Nächster Lauf: keine aktuelle Story")
    text = _modulausgabe("next_run", "--open", "--story", story)
    offen = not text.startswith("(keine")
    return Block(stub=f"Nächster Lauf ({story}): {'offen' if offen else 'alle implementiert'}",
                 inhalt=f"Offene Läufe der Story {story}:\n{text}"
                        + ("\n→ Skill `implementing-scenario` (ein Szenario pro Durchlauf)."
                           if offen else ""),
                 beansprucht=offen)


# --- Reine Stub-Module -------------------------------------------------------

def modul_open_questions() -> Block:
    """Fällige offene Fragen – mit Fragetext, nicht nur mit ID.

    Als reiner Einzeiler („3 Fragen fällig, Volltext: <Datei>") war das Modul wirkungslos:
    Es setzte voraus, dass jemand die Datei aufschlägt, und genau das geschah 32 Sessions
    lang nicht (S115/S118). Deshalb steht die **Frage selbst** im Startkontext – so viel,
    dass sie ohne weiteren Lesevorgang vorgelegt werden kann.

    Bewusst nicht der ganze Eintragskörper: Der trägt Herleitung, verworfene Varianten und
    Recherche-Ergebnisse (ausgearbeitete Einträge kommen auf zwanzig Zeilen und mehr) und
    würde den Startkontext dominieren, ohne die Vorlage-Entscheidung zu verbessern. Der Hintergrund steht in der
    Datei, auf die die letzte Zeile zeigt.
    """
    fragen = open_questions.parse(_lies(ROOT / open_questions.OQ_FILE))
    cur = current_session(ROOT)
    faellig = open_questions.due(fragen, td_anchors.lade_kontext(ROOT), cur)
    if not faellig:
        return Block(stub="")

    abschnitte = [
        f"  {f['id']} — {f['title']}\n"
        f"    Frage:  {f['frage']}\n"
        f"    Fällig: {'; '.join(f['gruende'])}"
        for f in faellig
    ]
    return Block(
        stub=f"Offene Fragen: {len(faellig)} fällig (mit dem User klären, nicht selbst entscheiden)",
        inhalt="Offene Fragen – vorzulegen, nicht selbst zu entscheiden:\n"
               + "\n\n".join(abschnitte)
               + f"\n\n  Hintergrund je Frage: {open_questions.OQ_FILE}",
    )


def ungeclusterte_szenarien(dateien: list[tuple[str, str]],
                         implementiert: set[str]) -> tuple[int, list[str]]:
    """(Anzahl, Befundzeilen) für offene Szenarien ohne `# @run-N`-Clustering.

    Rein textbasiert, damit die Erkennung ohne Repo-Fixture testbar bleibt.
    """
    from prozesscode._feature import parse_feature

    befunde: list[str] = []
    anzahl = 0
    for name, text in dateien:
        _, _, szenarien = parse_feature(text)
        offen = [s for s in szenarien
                 if s["title"] not in implementiert and s["run"] is None]
        if not offen:
            continue
        anzahl += len(offen)
        befunde.append(f"  {name} (kein `# @run-N` – nie geclustert):")
        befunde += [f"    - „{s['title']}\"" for s in offen]
    return anzahl, befunde


def modul_ungeclusterte_szenarien() -> Block:
    """Offene Szenarien ohne `# @run-N` – der Resolver legt sie als Einzel-Läufe vor.

    **Wann** sie drankommen, ist seit dem Phasen-Anker geklärt: Jedes Szenario trägt über die
    Datei-Direktive `# @phase:` oder seinen Run-Tag eine Phase, und `next_run.py` legt es vor,
    sobald das Projekt sie erreicht hat und die `braucht:`-Kanten erfüllt sind. Offen bleibt
    **wie**: Ohne Clustering fehlen Label, Schicht und Batch-Bildung, `implementing-scenario`
    bekommt also je Szenario einen eigenen Lauf statt eines zusammenhängenden. Das ist kein
    Verstoß (der Guard lässt es durch), aber vor der Implementierung einer solchen Datei gehört
    ein `gherkin-workshop`-Lauf darüber.
    """
    from prozesscode import next_run
    dateien = [(p.name, _lies(p)) for p in sorted((ROOT / "features").glob("**/*.feature"))]
    anzahl, befunde = ungeclusterte_szenarien(dateien, next_run._gather_implemented())
    if not anzahl:
        return Block(stub="")
    return Block(
        stub=f"Ungeclusterte Szenarien: {anzahl} offen, ohne `# @run-N` – je ein Einzel-Lauf",
        inhalt=("Offene Szenarien ohne Lauf-Clustering. Ihre Einplanung ist geklärt (Phase +\n"
                "`braucht:`-Kanten in der Feature-Datei); der Resolver legt sie vor, sobald das\n"
                "Projekt ihre Phase erreicht. Ohne `# @run-N` wird dabei aber jedes Szenario ein\n"
                "eigener Lauf – ohne Label, Schicht und Batch. Vor der Implementierung einer\n"
                "solchen Datei einen `gherkin-workshop`-Lauf darüber führen.\n" + "\n".join(befunde)),
    )


def modul_td_due() -> Block:
    treffer = td_due.faellige(ROOT)
    if not treffer:
        return Block(stub="")
    zeilen = [f"  - {tid}: {'; '.join(gruende)}" for tid, gruende in treffer]
    return Block(
        stub=f"Technische Schuld: {len(treffer)} fällig geworden",
        inhalt="Technische Schuld – Anker eingetreten oder defekt:\n" + "\n".join(zeilen),
    )


def modul_anker_defekt() -> Block:
    """Abschnitts-Anker, deren Verweise nicht mehr auflösen.

    Auffangnetz für alles, was an der Edit-Kette vorbeigeht: `check-anchors.py` läuft als
    PreToolUse nur auf Edit/Write. Verschwindet eine ganze Datei – per `rm`, `mv`, durch
    einen Merge oder von Hand –, sterben ihre Anker lautlos, und die Verweise darauf werden
    tot, ohne dass irgendetwas anschlägt.
    """
    try:
        bestand = anchors.lies_bestand(ROOT)
        tot = anchors.tote_verweise(bestand)
        pfade = anchors.falsche_pfade(bestand)
        dopp = anchors.doppelte(bestand)
    except Exception as fehler:  # noqa: BLE001
        # Nie stumm ausfallen: Ein Prüfer ohne Ausgabe meldet für immer „alles gut", und sein
        # Ausfall löst per Definition nichts aus (CM-S116-1). Also wird der Fehler die Meldung.
        return Block(stub=f"⚠️ Anker-Prüfung fiel aus: {fehler}")

    zeilen = [f"  - {d}:{n} → `{z}` hat kein Ziel" for d, n, z in tot[:10]]
    zeilen += [f"  - {d}:{n} → `{z}` verlinkt {gemeint}, liegt in {echt}"
               for d, n, z, gemeint, echt in pfade[:10]]
    zeilen += [f"  - `{a}` ist doppelt vergeben: {', '.join(ds)}" for a, ds in dopp[:10]]
    if not zeilen:
        return Block(stub="")
    anzahl = len(tot) + len(pfade) + len(dopp)
    return Block(
        stub=f"Anker-Verweise: {anzahl} defekt",
        inhalt=("Anker-Verweise defekt – vermutlich wurde eine Datei gelöscht, umbenannt "
                "oder außerhalb der Edit-Kette geändert:\n" + "\n".join(zeilen)
                + "\n  Vollbild: python3 -m prozesscode.anchors check"),
    )


def modul_ordinale() -> Block:
    """Selbstvergebene Gliederungsnummern im Bestand.

    Dieselbe Lücke wie beim Anker-Modul, andere Klasse: `check-ordinale.py` läuft als
    PreToolUse nur auf Edit/Write. Kommt eine Datei per Merge, `mv` oder von Hand herein,
    bringt sie ihre Nummern ungeprüft mit – und niemand merkt es, weil der Hook sie nie sah.
    """
    try:
        funde = ordinale.bestand(ROOT)
    except Exception as fehler:  # noqa: BLE001
        # Nie stumm ausfallen – siehe modul_anker_defekt (CM-S116-1).
        return Block(stub=f"⚠️ Ordinal-Prüfung fiel aus: {fehler}")

    if not funde:
        return Block(stub="")
    zeilen = [f"  - {d}:{n} [{art}] `{z[:90]}`" for d, n, z, art in funde[:10]]
    return Block(
        stub=f"Gliederungsnummern: {len(funde)} Fundstelle(n)",
        inhalt=("Selbstvergebene Gliederungsnummern im Bestand – vermutlich außerhalb der "
                "Edit-Kette hereingekommen:\n" + "\n".join(zeilen)
                + "\n  Vollbild: python3 -m prozesscode.ordinale"),
    )


def modul_commit_hook() -> Block:
    """Ist der `commit-msg`-Hook überhaupt scharf?

    `core.hooksPath` liegt in `.git/config` und ist nicht versionierbar. Ein frischer Klon
    committet also ungeprüft – und gerade die Abschluss-Marke, an der jede Tracker-ID hängt,
    fiele still durch. Die Prüfung kostet einen git-Aufruf und meldet sich nur im Defektfall.
    """
    try:
        ergebnis = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
        pfad = ergebnis.stdout.strip()
    except (OSError, subprocess.SubprocessError) as fehler:
        # Nie stumm ausfallen – siehe modul_anker_defekt (CM-S116-1).
        return Block(stub=f"⚠️ Hook-Prüfung fiel aus: {fehler}")

    if pfad and (ROOT / pfad / "commit-msg").is_file():
        return Block(stub="")
    return Block(
        stub="⚠️ commit-msg-Hook inaktiv",
        inhalt=("Die Form der Commit-Nachricht wird nicht geprüft – `core.hooksPath` zeigt "
                f"{'nirgendwohin' if not pfad else f'auf {pfad}, dort fehlt der Hook'}. "
                "Ohne ihn kann die Abschluss-Marke `Session-Ende: <NNN>` still falsch werden, "
                "und daran hängt jede Tracker-ID.\n"
                "  Einrichten: git config core.hooksPath .githooks"),
    )


# --- Registry ----------------------------------------------------------------
# Reihenfolge INNERHALB von AUFGABE ist die Rangfolge. Sie steht bewusst an dieser einen
# sichtbaren Stelle – verstreut über die Module würde sie zur Folklore.
MODULE: list[tuple[str, str, callable]] = [
    ("principles", RAHMEN, modul_principles),
    ("bash-allowlist", RAHMEN, modul_bash_allowlist),
    ("memory-state", ZUSTAND, modul_memory_state),
    ("repo-state", ZUSTAND, modul_repo_state),
    ("retro", AUFGABE, modul_retro),
    ("obs-drain", AUFGABE, modul_obs_drain),
    ("priorities", AUFGABE, modul_priorities),
    ("next-run", AUFGABE, modul_next_run),
    # ZUSTAND statt STUB (S119, Beschluss E4): Ein STUB erscheint nur als Einzeiler im
    # Nachrang-Bereich – die Frage selbst käme nie in den Startkontext, und genau daran ist
    # der Mechanismus 32 Sessions lang gescheitert. Keine AUFGABE: Offene Fragen sind kein
    # Arbeitsauftrag für die Session, sie sollen vorgelegt werden.
    ("open-questions", ZUSTAND, modul_open_questions),
    ("td-due", STUB, modul_td_due),
    ("ungeclusterte-szenarien", STUB, modul_ungeclusterte_szenarien),
    # STUB, nicht AUFGABE: ein defekter Verweis ist ein Befund, kein Arbeitsauftrag für die
    # Session. Er meldet sich nur, wenn wirklich etwas kaputt ist.
    ("anker-defekt", STUB, modul_anker_defekt),
    ("ordinale", STUB, modul_ordinale),
    ("commit-hook", STUB, modul_commit_hook),
]

ABRUF = "python3 -m prozesscode.session-agenda --only <name>"

# Das Label trägt den Rang. „Ebenfalls offen" tat das nicht und las sich neben der Aufgabe
# gleichrangig; „außer der User sagt es an" statt „nicht bearbeiten", weil die Liste der
# Übersteuerungs-Pfad ist und kein Verbot.
NACHRANG = "Nachrangig – nicht Gegenstand dieser Session, außer der User sagt es an"


def abruf(name: str) -> str:
    """Abrufbefehl für ein konkretes Modul – hält den Platzhalter an einer Stelle."""
    return ABRUF.replace("<name>", name)


def _abschnitt(text: str, ueberschrift: str) -> str:
    """Text von einer `##`-Überschrift bis zur nächsten gleicher Ebene (ohne die Überschrift)."""
    zeilen = text.splitlines()
    try:
        start = zeilen.index(ueberschrift) + 1
    except ValueError:
        return ""
    ende = start
    while ende < len(zeilen) and not zeilen[ende].startswith("## "):
        ende += 1
    return "\n".join(zeilen[start:ende]).strip()


def sammle() -> tuple[dict[str, Block], list[str]]:
    """Alle Module ausführen. (Blöcke je ID, Warnungen für ausgefallene Module)."""
    bloecke: dict[str, Block] = {}
    warnungen: list[str] = []
    for name, _art, funktion in MODULE:
        try:
            bloecke[name] = funktion()
        except Exception as exc:  # noqa: BLE001 – ein Modul darf die Agenda nie mitreißen
            warnungen.append(f"WARNUNG: Agenda-Modul `{name}` ausgefallen ({exc}) – "
                             f"Einzelabruf: {abruf(name)}")
    return bloecke, warnungen


def waehle_aufgabe(bloecke: dict[str, Block]) -> str | None:
    """Erster beanspruchender AUFGABE-Kandidat in Rangfolge."""
    for name, art, _ in MODULE:
        if art == AUFGABE and (block := bloecke.get(name)) and block.beansprucht:
            return name
    return None


def rendere(bloecke: dict[str, Block], warnungen: list[str]) -> str:
    """Der Agenda-Block: Zustand, Aufgabe, Einzeiler.

    Die RAHMEN-Module stehen seit S128 NICHT mehr hier – sie sind eigene Injektionsblöcke
    (siehe INJEKTIONS_BLOECKE). Zusammen ergaben sie 23.123 units und damit das Zweifache
    des Caps, an dem der Runtime den ganzen Block gegen eine Vorschau tauscht; die Agenda
    stand am Ende und kam deshalb in keiner Session an.
    """
    aufgabe = waehle_aufgabe(bloecke)
    teile: list[str] = []

    for name, art, _ in MODULE:
        if art == ZUSTAND and (block := bloecke.get(name)) and block.inhalt:
            teile += [block.inhalt, ""]

    if aufgabe:
        # KEINE zusammenfassende Kopfzeile: Sie doppelte den Modulinhalt darunter.
        teile += ["--- Nächste Aufgabe ---", "", bloecke[aufgabe].inhalt]
    else:
        teile.append("--- Nächste Aufgabe: keine erzwungen, frei für das, was ansteht. ---")

    stubs = [
        f"  - {name}: {block.stub}"
        for name, art, _ in MODULE
        if art in (AUFGABE, STUB) and name != aufgabe
        and (block := bloecke.get(name)) and block.stub
    ]
    if stubs:
        # Trenner und Label haben verschiedene Aufgaben: Der Trenner markiert die GRENZE (ohne
        # ihn liefe der Abschnitt optisch in der Aufgabe weiter), das Label trägt den RANG. Ein
        # neutrales Label („Ebenfalls offen") in gleicher Trennerform las sich gleichrangig –
        # deshalb sagt das Label die Nachrangigkeit, nicht dessen Weglassen.
        teile += ["", f"--- {NACHRANG} ---",
                  f"Volltext je Eintrag: {ABRUF}  (<name> = das Wort vor dem Doppelpunkt)"] + stubs

    teile += warnungen
    # KEINE Abschlussmarke hier: Die setzt `rendere_block` für alle fünf Blöcke einheitlich.
    # Bis zur Prüfung in S128 tat es beides, und der Agenda-Block endete auf zwei ineinander
    # liegenden Rahmen.
    return "\n".join(teile)


# --- Injektions-Blöcke -------------------------------------------------------
# EIN Block = EINE SessionStart-Registrierung in settings.json = EIN eigener 10.000er-Cap.
# Der Cap gilt pro registriertem Command (belegt in #84021: zwei gemeinsam registrierte
# 5.149er-Proben kamen beide intakt an). Wer hier einen Block ergänzt oder zwei zusammenlegt,
# muss settings.json mitziehen – sonst fällt der nicht registrierte Block lautlos aus.

def _block_verhalten() -> str:
    return _principles_block("verhalten")


def _block_doku() -> str:
    return _principles_block("doku")


def _block_kommunikation() -> str:
    return _principles_block("kommunikation")


def _block_allowlist() -> str:
    return modul_bash_allowlist().inhalt


def _block_agenda() -> str:
    return rendere(*sammle())


INJEKTIONS_BLOECKE: list[tuple[str, str, callable]] = [
    ("verhalten", "Verhalten & Disziplin", _block_verhalten),
    ("doku", "Doku & Referenzen", _block_doku),
    ("kommunikation", "Kommunikation & Argumentation", _block_kommunikation),
    ("bash-allowlist", "Bash-Allow-Liste", _block_allowlist),
    # Zuletzt und bewusst allein: Die Agenda ist der einzige Block, der von Session zu
    # Session stark schwankt (der Drain-Satz wächst mit dem Backlog). Ein stabiler Block
    # daneben würde sein Budget an dieses Schwanken koppeln.
    ("agenda", "Session-Agenda", _block_agenda),
]


def _blockkopf(name: str, titel: str, nummer: int, gesamt: int, inhalt: str) -> list[str]:
    """Kopf eines Injektionsblocks – muss in die 2.000er-Vorschau passen.

    Er leistet dreierlei, und alles drei nur, weil er die Kürzung überlebt: Er sagt, WER
    der Block ist (die Ankunftsreihenfolge sagt es nicht), er MELDET den Überlauf (der
    Runtime tut es nicht), und er nennt den GEZIELTEN Nachladebefehl (die Volldatei zu
    lesen wäre der Rückfall in das Problem, das die Aufteilung gerade löst).
    """
    zeilen = [f"=== Session-Start {nummer}/{gesamt}: {titel} ==="]
    groesse = u16(inhalt)
    if groesse > CAP:
        zeilen.append(
            f"!!! ÜBERSCHREITET den Injektions-Cap ({groesse} von {CAP} u16): Alles ab rund "
            f"{VORSCHAU} units fehlt im Kontext, und der Runtime meldet das nicht. "
            f"Diesen Block neu schneiden.")
    elif groesse > BUDGET:
        zeilen.append(
            f"! Budget knapp ({groesse} von {BUDGET} u16, Cap {CAP}) – neu schneiden, "
            f"bevor der Block still verschwindet.")
    zeilen.append(
        f"(Die {gesamt} Blöcke laufen parallel und treffen in BELIEBIGER Reihenfolge ein – "
        f"die Nummer ist Identität, keine Position. Fehlt hier Text oder siehst du nur eine "
        f"„saved to\"-Vorschau: python3 -m prozesscode.session-agenda --block {name})")
    return zeilen


def rendere_block(name: str) -> str:
    namen = [n for n, _t, _f in INJEKTIONS_BLOECKE]
    if name not in namen:
        raise KeyError(f"Unbekannter Injektionsblock: {name}. Bekannt: {', '.join(namen)}")
    nummer = namen.index(name) + 1
    _name, titel, funktion = INJEKTIONS_BLOECKE[nummer - 1]
    inhalt = funktion()
    kopf = _blockkopf(name, titel, nummer, len(namen), inhalt)
    return "\n".join([*kopf, inhalt, "=" * 30])


def rendere_alles() -> str:
    """Alle Blöcke am Stück – für den manuellen Blick, NICHT für die Injektion.

    Setzt dieselben Blöcke zusammen, die injiziert werden: Zwei Renderpfade könnten
    auseinanderlaufen, und geprüft würde dann nicht, was ankommt.
    """
    return "\n".join(rendere_block(n) for n, _t, _f in INJEKTIONS_BLOECKE)


def main() -> int:
    # `or ""`: Im Mutantenbaum von mutmut ist `__doc__` None (S133, s. td_due.main).
    ap = argparse.ArgumentParser(description=(__doc__ or "").partition("\n")[0])
    gruppe = ap.add_mutually_exclusive_group()
    gruppe.add_argument("--block", metavar="NAME",
                        help="einen Injektionsblock ausgeben (so ruft der SessionStart-Hook)")
    gruppe.add_argument("--only", metavar="ID", help="ein Modul in voller Tiefe ausgeben")
    gruppe.add_argument("--list", action="store_true", help="Modulnamen listen")
    args = ap.parse_args()

    if args.list:
        for name, art, _ in MODULE:
            print(f"{name:16} {art}")
        return 0

    if args.block:
        try:
            print(rendere_block(args.block))
        except KeyError as exc:
            print(exc.args[0], file=sys.stderr)
            return 1
        return 0

    if args.only:
        treffer = [m for m in MODULE if m[0] == args.only]
        if not treffer:
            print(f"Unbekanntes Modul: {args.only}. Bekannt: "
                  f"{', '.join(m[0] for m in MODULE)}", file=sys.stderr)
            return 1
        try:
            block = treffer[0][2]()
        except Exception as exc:  # noqa: BLE001
            print(f"Modul `{args.only}` ausgefallen: {exc}", file=sys.stderr)
            return 1
        print(block.inhalt or f"({args.only}: nichts zu melden)")
        return 0

    # Ohne Argument: alle Blöcke am Stück. Das ist die Sicht für Menschen und für Prüfungen –
    # sie zeigt, was zusammen ankommt. Injiziert wird trotzdem NIE diese Ausgabe (sie ist mit
    # Absicht über dem Cap), sondern je Block ein eigener Hook.
    print(rendere_alles())
    return 0


if __name__ == "__main__":
    sys.exit(main())
