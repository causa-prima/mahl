#!/usr/bin/env python3
"""Gemeinsame Basis der Abschnitts-Tracker – Parsing, ID-Vergabe, Ändern, Löschen.

Warum (OBS-S120-2): Fünf Dokumente tragen strukturierte Einträge mit Pflichtfeldern und IDs,
und die Pflege war je Datei anders gelöst – `obs.py` konnte get/add/set, `lessons.py` nur
get/add, `decisions.py` war trotz 463 Zeilen reines Lesen, für `tech-debt.md` gab es gar
nichts und `open-questions.md` hatte nicht einmal eine CLI. Wer eine Datei ergänzte,
duplizierte Parsing, ID-Vergabe und Feld-Ersetzung ein weiteres Mal.

**Reichweite – bewusst nicht alle fünf.** Hier liegt, was `open-questions.md` und
`tech-debt.md` teilen: H2-Kopfzeile `## <ID> — <Titel>`, `**Feld:**`-Zeilen, `---` als
Trenner, dieselbe Fälligkeits-Grammatik. `observations.md` und `lessons_learned.md` haben ein
anderes Eintragsformat (`- Feld:` bzw. eine Bullet-Kopfzeile mit Tag-Tripel) und bleiben
eigenständig; sie hier einzupassen hieße, die Basis um Sonderfälle zu erweitern, bis sie
nichts mehr vereinfacht. Was sie dennoch teilen – die Struktur-Nachprüfung und die
Darstellung im Freigabedialog – liegt bei ihnen bzw. in `tracker_preview.py`.

Die tracker-spezifische Prüfung (Anker-Grammatik, Kopplung an AGENT_MEMORY) gehört NICHT
hierher, sondern kommt als `pruefer`-Callback aus dem jeweiligen Modul: Sonst müsste diese
Datei jeden Sonderfall kennen und wäre wieder die Sammelstelle, die sie ersetzt.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TrackerSpec:
    """Beschreibt einen Tracker mit H2-Einträgen und `**Feld:**`-Zeilen."""
    datei: str
    praefix: str                      # "OQ", "TD" – der ID-Vorspann
    felder: tuple[str, ...]           # Pflichtfelder, in Reihenfolge der Ausgabe
    trenner: str = "\n\n---\n\n"

    @property
    def kopf(self) -> re.Pattern[str]:
        return re.compile(
            rf"^## ({self.praefix}-S(\d{{3}})-(\d+))\s+[—–-]\s+(.+)$", re.M)

    def feldzeile(self, feld: str) -> re.Pattern[str]:
        return re.compile(rf"^\*\*{re.escape(feld)}:\*\*.*$", re.M)


def entry_spans(spec: TrackerSpec, text: str) -> dict[str, tuple[int, int]]:
    """ID → (Start, Ende). Ein Eintrag endet vor der nächsten Kopfzeile."""
    treffer = list(spec.kopf.finditer(text))
    return {
        m.group(1): (m.start(),
                     treffer[i + 1].start() if i + 1 < len(treffer) else len(text))
        for i, m in enumerate(treffer)
    }


def get(spec: TrackerSpec, text: str, eid: str) -> str | None:
    """Der Eintrag im Volltext – ohne die nachfolgende Dokument-Trennlinie, die keinem
    Eintrag gehört und im Volltext nur nach abgeschnittenem Inhalt aussieht."""
    span = entry_spans(spec, text).get(eid)
    if not span:
        return None
    return re.sub(r"\n\s*---\s*$", "", text[span[0]:span[1]].strip())


def titel(spec: TrackerSpec, text: str, eid: str) -> str | None:
    for m in spec.kopf.finditer(text):
        if m.group(1) == eid:
            return m.group(4).strip()
    return None


def next_id(spec: TrackerSpec, text: str, session: int) -> str:
    """Nächste freie Nummer INNERHALB der übergebenen Session.

    Die Session wird übergeben statt aus der höchsten bestehenden Serie abgeleitet: Sonst
    setzt ein Aufrufer mitten in der Session die jüngste fremde Serie fort und nummeriert
    falsch – die Klasse aus OBS-S107-1, dort mit ~7 nachzuziehenden Referenzen.
    """
    benutzt = [int(m.group(3)) for m in spec.kopf.finditer(text)
               if int(m.group(2)) == session]
    return f"{spec.praefix}-S{session:03d}-{max(benutzt, default=0) + 1}"


def pruefe_wohlgeformt(spec: TrackerSpec, eid: str, block: str) -> None:
    """Jedes vorkommende Feld steht genau einmal am Zeilenanfang – sonst Abbruch.

    Bewusst KEINE Vollständigkeitsprüfung: Einträge aus der Zeit vor einem später
    eingeführten Pflichtfeld führen es legitim nicht, und ein Vollständigkeits-Check machte
    sie unänderbar. Unterschieden wird „fehlt" (kommt gar nicht vor – in Ordnung) von
    „verrutscht" (kommt vor, aber nicht am Zeilenanfang – Strukturbruch).

    Läuft vor UND nach jedem Umbau: vorher, weil ein verrutschtes Feld jeden weiteren
    Schreibzugriff zum Strukturbruch macht; nachher, weil ein Wert, der wie eine Feldzeile
    aussieht, die Struktur sonst kapert. Der Ausfall war bisher still – nichts schlug fehl,
    der zerstörte OBS-S111-4 fiel erst zehn Sessions später auf (LL-S121-1, OBS-S121-1).
    """
    for feld in spec.felder:
        marke = f"**{feld}:**"
        am_zeilenanfang = len(re.findall(rf"^{re.escape(marke)}", block, re.M))
        if am_zeilenanfang > 1:
            raise ValueError(
                f"{eid}: Feld `{feld}` steht {am_zeilenanfang}× am Zeilenanfang – "
                f"jedes Feld darf nur einmal vorkommen.")
        if block.count(marke) != am_zeilenanfang:
            raise ValueError(
                f"{eid}: Feld `{feld}` steht nicht am Zeilenanfang (Strukturbruch). "
                f"Der Eintrag muss von Hand repariert werden, bevor er änderbar ist.")


def format_entry(spec: TrackerSpec, eid: str, kurztitel: str, werte: dict[str, str]) -> str:
    if not kurztitel.strip():
        raise ValueError("Der Titel darf nicht leer sein.")
    fehlend = [f for f in spec.felder if not (werte.get(f) or "").strip()]
    if fehlend:
        raise ValueError(f"{eid}: Pflichtfeld(er) fehlen oder sind leer: {', '.join(fehlend)}")
    zeilen = [f"## {eid} — {kurztitel.strip()}"]
    zeilen += [f"**{f}:** {werte[f].strip()}" for f in spec.felder]
    return "\n".join(zeilen) + "\n"


def add(spec: TrackerSpec, text: str, session: int, kurztitel: str,
        werte: dict[str, str]) -> tuple[str, str]:
    """Hängt einen Eintrag unten an – beide Dateien schreiben Sortierung nach ID aufsteigend
    vor. Liefert (neuer Dateiinhalt, vergebene ID)."""
    eid = next_id(spec, text, session)
    eintrag = format_entry(spec, eid, kurztitel, werte)
    pruefe_wohlgeformt(spec, eid, eintrag)
    trenner = spec.trenner if entry_spans(spec, text) else "\n\n"
    return text.rstrip("\n") + trenner + eintrag, eid


def set_fields(spec: TrackerSpec, text: str, eid: str, werte: dict[str, str],
               titel: str | None = None) -> str:
    """Ersetzt Feldwerte und/oder den Titel.

    `titel` ändert die Überschrift, nicht die ID: Der Titel ist zugleich der Kurztitel, unter
    dem der Eintrag im Gespräch geführt wird. Trägt er den Punkt nicht mehr, wird er korrigiert
    – ein zweites Namensfeld daneben würde still veralten und dann Falsches behaupten.
    """
    span = entry_spans(spec, text).get(eid)
    if not span:
        raise ValueError(f"{eid} existiert nicht in {spec.datei}.")
    unbekannt = [f for f in werte if f not in spec.felder]
    if unbekannt:
        raise ValueError(
            f"{eid}: unbekannte(s) Feld(er) {', '.join(unbekannt)}. "
            f"Erlaubt: {', '.join(spec.felder)}.")

    block = text[span[0]:span[1]]
    pruefe_wohlgeformt(spec, eid, block)
    if titel is not None:
        if not titel.strip():
            raise ValueError(f"{eid}: leerer Titel.")
        kopf = re.compile(rf"^## {re.escape(eid)} .*$", re.M)
        neue_zeile = f"## {eid} — {titel.strip()}"
        block = kopf.sub(lambda _: neue_zeile, block, count=1)
    for feld, wert in werte.items():
        if wert is None:
            continue
        muster = spec.feldzeile(feld)
        if not muster.search(block):
            raise ValueError(f"{eid} hat kein Feld `**{feld}:**` – Datei von Hand prüfen.")
        # Ersetzung als Funktion, nicht als String: Ein String wäre ein Regex-Template, in
        # dem `\s` mit „bad escape" abbräche und `\1` still durch eine Gruppe ersetzt würde.
        # Einträge zitieren regelmäßig Muster und Pfade – der Wert muss literal bleiben.
        neuer_wert = f"**{feld}:** {wert.strip()}"
        # noqa B023: wie in `obs_entry.set_feld` – `sub` ruft das Lambda sofort in derselben
        # Iteration auf, die Closure überlebt sie nicht. Geprüft in S128.
        block = muster.sub(lambda _: neuer_wert, block, count=1)  # noqa: B023

    pruefe_wohlgeformt(spec, eid, block)
    return text[:span[0]] + block + text[span[1]:]


def remove(spec: TrackerSpec, text: str, eid: str) -> str:
    """Entfernt einen Eintrag samt genau EINER angrenzenden Trennlinie.

    Ohne diese Behandlung bliebe je nach Position ein `---` ohne Eintrag stehen oder zwei
    fielen aufeinander – die Datei wäre nach jedem Löschen von Hand nachzuputzen, also genau
    der Aufwand, den das Werkzeug abschafft (OBS-S120-1).
    """
    span = entry_spans(spec, text).get(eid)
    if not span:
        vorhanden = ", ".join(entry_spans(spec, text)) or "(keine)"
        raise ValueError(f"{eid} existiert nicht in {spec.datei}. Vorhandene: {vorhanden}.")

    vorher, nachher = text[:span[0]], text[span[1]:]
    if re.search(r"\n---\s*\n\s*$", vorher) and nachher.strip():
        vorher = re.sub(r"\n---\s*\n\s*$", "\n", vorher)
    elif re.match(r"^\s*---\s*\n", nachher):
        nachher = re.sub(r"^\s*---\s*\n", "", nachher)

    zusammen = vorher.rstrip("\n") + ("\n\n" + nachher.lstrip("\n") if nachher.strip() else "\n")
    return re.sub(r"\n{3,}", "\n\n", zusammen)
