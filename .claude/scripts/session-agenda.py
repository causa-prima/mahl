#!/usr/bin/env python3
"""session-agenda.py – was verlangt zum Session-Start eine Entscheidung?

Einstiegspunkt des SessionStart-Hooks (ersetzt `session-start.sh`; Rangfolge und Begründung
kanonisch in `docs/kaizen/process.md`, Abschnitt „Session-Agenda").

Die Ausgabe hat zwei Teile, in dieser Reihenfolge:

1. **Rahmen-Blöcke** (`principles`, Allow-Liste) – stehender Verhaltensrahmen, nie unterdrückt.
   Ihr Weglassen fiele lautlos aus. Sie stehen ZUERST, weil sie über Sessions unverändert
   bleiben und beim Lesen übersprungen werden dürfen.
2. **Session-Agenda** – Zustand, genau eine „Nächste Aufgabe" im Volltext, und die Einzeiler
   der übrigen Module. Sie steht am SCHLUSS, direkt vor der ersten Nachricht des Users: das
   einzig session-spezifische Stück gehört an die Stelle, an der es am ehesten wirkt.

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
    session-agenda.py              volle Agenda (der Hook)
    session-agenda.py --only <id>  ein Modul in voller Tiefe (Übersteuern)
    session-agenda.py --list       Modulnamen

Ausfallverhalten: Jedes Modul scheitert EINZELN und sichtbar; die Agenda läuft weiter. Ein
Totalausfall wäre von „nichts zu tun" ununterscheidbar.
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anchors  # noqa: E402
import open_questions  # noqa: E402
import ordinale  # noqa: E402
import td_anchors  # noqa: E402
import td_due  # noqa: E402
from obs_parse import parse_entries  # noqa: E402
from repo_kontext import current_session  # noqa: E402

# obs-drain.py trägt einen Bindestrich (CLI-Name) und ist deshalb nicht direkt importierbar.
# Der Trigger lebt trotzdem dort, nicht hier: Wer den Drain-Satz berechnet, entscheidet auch,
# ob er eine Session beansprucht – zwei Stimmen dazu wären eine Quelle für stille Divergenz.
_drain_spec = importlib.util.spec_from_file_location(
    "obs_drain", os.path.join(os.path.dirname(os.path.abspath(__file__)), "obs-drain.py"))
_drain = importlib.util.module_from_spec(_drain_spec)
_drain_spec.loader.exec_module(_drain)

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent

# Modul-Arten. RAHMEN und ZUSTAND werden immer gerendert, aber an verschiedenen Stellen:
# RAHMEN als eigener Block VOR der Agenda, ZUSTAND als Kopf INNERHALB der Agenda.
RAHMEN, ZUSTAND, AUFGABE, STUB = "rahmen", "zustand", "aufgabe", "stub"


@dataclass
class Block:
    """Ergebnis eines Moduls. `stub` ist die Einzeiler-Fassung, `inhalt` die volle."""
    stub: str
    inhalt: str = ""
    beansprucht: bool = False   # beansprucht den Aufgaben-Slot?


def _lies(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8") if pfad.is_file() else ""


def _laufe(*befehl: str) -> str:
    """Externes Script ausführen; stdout zurück. Fehler wirft – der Rahmen fängt ihn je Modul."""
    ergebnis = subprocess.run(befehl, capture_output=True, text=True, cwd=ROOT)
    if ergebnis.returncode != 0:
        raise RuntimeError(f"{' '.join(befehl)} → Exit {ergebnis.returncode}: "
                           f"{ergebnis.stderr.strip()[:200]}")
    return ergebnis.stdout.rstrip("\n")


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


def modul_principles() -> Block:
    text = _lies(ROOT / "docs" / "kaizen" / "principles.md")
    if not text:
        raise FileNotFoundError("docs/kaizen/principles.md fehlt")
    return Block(stub="principles.md", inhalt=ohne_kommentare(text))


def modul_bash_allowlist() -> Block:
    text = _laufe("python3", str(ROOT / ".claude" / "hooks" / "check-bash-permission.py"), "--list")
    return Block(stub="Bash-Allow-Liste", inhalt=text)


# --- Zustand (Kopf der Agenda) -----------------------------------------------

def modul_memory_state() -> Block:
    """Phase, Story und nächster Lauf – winzig und immer relevant.

    Trägt bewusst KEINEN Stub: Der Block wird ungekürzt gerendert, eine Kurzfassung
    daneben wäre dieselbe Information zweimal.
    """
    text = _laufe("python3", str(SCRIPTS / "next_run.py"), "--render",
                  str(ROOT / "docs" / "AGENT_MEMORY.md"))
    zeilen = [z for z in text.splitlines()
              if z.startswith(("**Phase:", "**Aktuelle Story:", "**Nächster Lauf:"))]
    return Block(stub="", inhalt="\n".join(zeilen) or "(kein Zustand lesbar)")


# --- Aufgaben-Kandidaten (in Rangfolge) --------------------------------------
# `inhalt` ist hier zugleich die Ausgabe von `--only <name>` UND der Aufgabentext der
# Agenda. Er muss deshalb ohne jede Rahmenzeile sagen, worum es geht und was zu tun ist.

def modul_retro() -> Block:
    text = _laufe("python3", str(SCRIPTS / "jenga_score.py"))
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
    text = _laufe("python3", str(SCRIPTS / "obs-drain.py"))
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
    text = _laufe("python3", str(SCRIPTS / "next_run.py"), "--render",
                  str(ROOT / "docs" / "AGENT_MEMORY.md"))
    # TD-Punkte stehen in AGENT_MEMORY nur als Platzhalter (ID + Done); Titel und Fälligkeit
    # werden hier aus tech-debt.md aufgelöst, damit sie nur an einer Stelle leben und nicht
    # driften können (OBS-S118-1). Fällt das Auflösen aus, bleibt der Platzhalter stehen –
    # sichtbar, statt den Punkt zu verschlucken.
    try:
        import td_entry
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
    import next_run
    story = next_run.extract_story(_lies(ROOT / "docs" / "AGENT_MEMORY.md"))
    if story is None:
        return Block(stub="Nächster Lauf: keine aktuelle Story")
    text = _laufe("python3", str(SCRIPTS / "next_run.py"), "--open", "--story", story)
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


def ungeplante_szenarien(dateien: list[tuple[str, str]],
                         implementiert: set[str]) -> tuple[int, list[str]]:
    """(Anzahl, Befundzeilen) für Szenarien ohne Weg in die Implementierung.

    Rein textbasiert, damit die Erkennung ohne Repo-Fixture testbar bleibt.
    """
    from _feature import parse_feature

    befunde: list[str] = []
    anzahl = 0
    for name, text in dateien:
        ftags, _, szenarien = parse_feature(text)
        story_gebunden = any(t.startswith("@US-") for t in ftags)
        offen = [s for s in szenarien if s["title"] not in implementiert
                 and (not story_gebunden or s["run"] is None)]
        if not offen:
            continue
        anzahl += len(offen)
        grund = ("Datei trägt keinen `@US-`Tag – die Lauf-Auflösung läuft über die aktuelle "
                 "Story und erreicht sie nie") if not story_gebunden else \
                "kein `# @run-N` – nie geclustert"
        befunde.append(f"  {name} ({grund}):")
        befunde += [f"    - „{s['title']}\"" for s in offen]
    return anzahl, befunde


def modul_ungeplante_szenarien() -> Block:
    """Geschriebene, nicht implementierte Szenarien, die kein Mechanismus je vorlegt.

    Zwei Wege, auf denen ein Szenario aus jedem Plan fällt:
      (a) seine Feature-Datei trägt keinen `@US-`Tag (querschnittliche Dateien nach ADR-S103-1) –
          `next_run.py` löst über die aktuelle Story auf und erreicht sie strukturell nie;
      (b) es trägt keinen `# @run-N`-Kommentar – also nie geclustert worden.

    Bewusst als eigenes Modul und nicht in `next-run` versteckt: Die Aufgabe darf nur die
    Läufe DER AKTUELLEN STORY beanspruchen (sonst behauptet er Arbeit, die die Feature-Datei
    ausdrücklich zurückstellt) – aber die Szenarien dann stillschweigend zu unterschlagen, wäre
    die falsche Hälfte der Korrektur. Der Status ist **ungeklärt**, nicht „fällig": Sie können
    bewusst zurückgestellt sein. Genau das soll die Zeile sagen.
    """
    import next_run
    dateien = [(p.name, _lies(p)) for p in sorted((ROOT / "features").glob("**/*.feature"))]
    anzahl, befunde = ungeplante_szenarien(dateien, next_run._gather_implemented())
    if not anzahl:
        return Block(stub="")
    return Block(
        stub=f"Ungeplante Szenarien: {anzahl} geschrieben, keinem Lauf zugeordnet – Einplanung ungeklärt",
        inhalt=("Geschriebene Szenarien, die kein Mechanismus als „nächsten Lauf\" vorlegt.\n"
                "Das heißt NICHT, dass sie fällig sind – sie können bewusst zurückgestellt sein\n"
                "(Feature-Dateien tragen den Scope oft als Kommentar). Ungeklärt ist, WANN sie\n"
                "eingeplant werden; solange das offen ist, brauchen TD-Einträge, die auf sie\n"
                "ankern, einen Backstop-Anker.\n" + "\n".join(befunde)),
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
                + "\n  Vollbild: python3 .claude/scripts/anchors.py check"),
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
                + "\n  Vollbild: python3 .claude/scripts/ordinale.py"),
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
    ("ungeplante-szenarien", STUB, modul_ungeplante_szenarien),
    # STUB, nicht AUFGABE: ein defekter Verweis ist ein Befund, kein Arbeitsauftrag für die
    # Session. Er meldet sich nur, wenn wirklich etwas kaputt ist.
    ("anker-defekt", STUB, modul_anker_defekt),
    ("ordinale", STUB, modul_ordinale),
    ("commit-hook", STUB, modul_commit_hook),
]

ABRUF = "python3 .claude/scripts/session-agenda.py --only <name>"

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
    aufgabe = waehle_aufgabe(bloecke)
    teile: list[str] = []

    # Rahmen zuerst – über Sessions unverändert, beim Lesen überspringbar.
    for name, art, _ in MODULE:
        if art == RAHMEN and (block := bloecke.get(name)):
            teile += [f"=== {block.stub} ===", block.inhalt, "=" * (len(block.stub) + 8)]

    # Agenda zuletzt – das einzig session-spezifische Stück, direkt vor der ersten
    #    Nachricht des Users. Zustand, Aufgabe und Einzeiler stehen zusammenhängend.
    teile.append("=== Session-Agenda ===")
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
    teile.append("======================")
    return "\n".join(teile)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    gruppe = ap.add_mutually_exclusive_group()
    gruppe.add_argument("--only", metavar="ID", help="ein Modul in voller Tiefe ausgeben")
    gruppe.add_argument("--list", action="store_true", help="Modulnamen listen")
    args = ap.parse_args()

    if args.list:
        for name, art, _ in MODULE:
            print(f"{name:16} {art}")
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

    print(rendere(*sammle()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
