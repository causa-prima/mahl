#!/usr/bin/env python3
"""Fällige offene Fragen aus `docs/open-questions.md`.

Bis S116 hing diese Logik in `obs-drain.py` – angehängt, weil dort der einzige
Session-Start-Vorlage-Mechanismus lag. Mit `session-agenda.py` gibt es einen Träger, dem
offene Fragen als eigenes Modul gehören: Sie sind ein anderer Tracker mit anderem Ausgang
(mit dem User klären, nicht im Drain entscheiden) und haben in einem OBS-Script nichts zu
suchen.

Warum es den Mechanismus überhaupt braucht (S115): `open-questions.md` hatte als einziger
Tracker keinen Lese-Trigger – sämtliche Verweise darauf waren Schreib-Verweise („dort
eintragen"), kein Prozessschritt legte Fragen vor. Folge im Bestand: vier Fragen lagen
14–25 Sessions unbeantwortet, und eine davon (Taxonomie ADR vs. Tech-Debt) wurde mehrfach
ad hoc neu verhandelt, ohne dass die offene Frage konsultiert wurde.

**Anker-Grammatik (S119, Beschluss E4 aus S118).** `**Fällig:**` liest sich hier nach
derselben Grammatik wie bei Tech-Debt – `td_anchors.py` wird **wiederverwendet, nicht
kopiert**. Vorher kannte dieses Modul nur `S<NNN>`: Ein Anker wie `Phase:V1` oder
`Szenario:„…"` fiel still auf die Alters-Regel zurück, und ein Vertipper blieb unbemerkt.
Genau das war im Bestand aufgetreten (OQ-S094-1 trug einen Ereignis-Trigger, den das Feld
nicht ausdrücken konnte).

Zwei bewusste Abweichungen von der TD-Auswertung:

1. **`jetzt` erzeugt hier einen Grund.** Bei Tech-Debt tut es das nicht, weil solche Einträge
   ohnehin in `AGENT_MEMORY.md` stehen und von dort vorgelegt werden (OBS-S116-2). Für offene
   Fragen gibt es diesen zweiten Kanal nicht – eine Frage mit `Fällig: jetzt` würde sonst
   nirgends auftauchen.
2. **Ohne `Fällig`-Feld greift die Alters-Regel.** Bei TD ist das Feld Pflicht; hier ist es
   ausdrücklich optional, und eine Frage ohne Termin soll nach ~`STALE` Sessions trotzdem
   hochkommen. Ein *gesetzter* Anker unterdrückt die Alters-Regel weiterhin – sonst wäre eine
   bewusst weit geparkte Frage sofort wieder fällig und der Termin wirkungslos.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import td_anchors  # noqa: E402

OQ_FILE = "docs/open-questions.md"
STALE = 10   # ohne Termin gilt eine Frage ab diesem Alter als überaltert → vorlegen
MAX = 3      # Deckel: der Session-Start-Block soll nicht von Fragen überschwemmt werden

_HEADER_RE = re.compile(r"^## (OQ-S(\d{3})-\d+)\s+[—–-]\s+(.+)$", re.M)
_FAELLIG_RE = re.compile(r"^\*\*Fällig:\*\*(.*)$", re.M)
_FRAGE_RE = re.compile(r"^\*\*Frage:\*\*(.*)$", re.M)


def parse(text: str) -> list[dict]:
    """Einträge als (id, session, title, faellig, frage, body).

    `faellig` ist der **rohe** Feldwert (Kopf + Prosa) oder None – ausgewertet wird er erst
    in `due()` gegen den Anker-Kontext.
    """
    treffer = list(_HEADER_RE.finditer(text))
    fragen = []
    for i, m in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        body = text[m.end():ende]
        termin = _FAELLIG_RE.search(body)
        frage = _FRAGE_RE.search(body)
        fragen.append({
            "id": m.group(1),
            "session": int(m.group(2)),
            "title": m.group(3).strip(),
            "faellig": termin.group(1).strip() if termin else None,
            "frage": frage.group(1).strip() if frage else "",
            "body": body.strip(),
        })
    return fragen


def gruende(eintrag: dict, ktx: td_anchors.Kontext, cur: int | None) -> list[str]:
    """Warum diese Frage jetzt vorzulegen ist (leer = noch nicht fällig).

    Ein Syntaxfehler im Kopf wird als Grund gemeldet, nicht verschluckt: Sonst verschwände die
    Frage lautlos aus der Vorlage – der Fehlermodus, den die Anker-Grammatik gerade behebt.
    """
    roh = eintrag["faellig"]
    if roh is None:
        if cur is not None and cur - eintrag["session"] >= STALE:
            return [f"seit {cur - eintrag['session']} Sessions ohne Termin offen"]
        return []

    anker, fehler = td_anchors.parse(roh)
    if fehler:
        return [f"`Fällig:` nicht auswertbar: {fehler[0]}"]

    treffer = td_anchors.faellig_gruende(eintrag["id"], roh, ktx)
    # Siehe Modul-Docstring, Abweichung 1: `jetzt` hat bei OQ keinen zweiten Kanal.
    if any(a.art == td_anchors.JETZT for a in anker):
        treffer.append("als `jetzt` terminiert")
    return treffer


def due(fragen: list[dict], ktx: td_anchors.Kontext, cur: int | None) -> list[dict]:
    """Vorzulegende Fragen, älteste zuerst, auf `MAX` gedeckelt.

    Jeder Treffer trägt seine Gründe unter `"gruende"` – die Vorlage nennt sie, damit
    erkennbar ist, WARUM die Frage jetzt kommt.
    """
    faellig = []
    for eintrag in fragen:
        if g := gruende(eintrag, ktx, cur):
            faellig.append({**eintrag, "gruende": g})
    return sorted(faellig, key=lambda f: f["session"])[:MAX]
