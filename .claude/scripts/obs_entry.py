"""Lesen und Schreiben einzelner OBS-Einträge in `docs/kaizen/observations.md`.

Zwei Gründe für diesen Zugriffsweg statt Read/Edit auf der ganzen Datei:

**Lesen.** Wer einen Eintrag ändert, muss die Datei vorher lesen – der Harness verlangt das.
Gemessen ist rund die Hälfte des Lesens auf `docs/kaizen` genau dieser erzwungene Vor-Edit-Read,
und nur ein Viertel davon ist gezielt. Für die Änderung eines Eintrags wird also meist die
gesamte Datei gelesen.

**Form.** Die Erfassungsregeln (abschließende Feldliste, Pflichtfelder, `Entscheidung/Maßnahme`
bei Erfassung nur mit dem Kanon-Wert) werden bisher **nachträglich** von
`.claude/hooks/check-obs-capture.py` erzwungen – ein Eintrag entsteht, ist falsch, wird geblockt.
Über `add()` kann er gar nicht erst falsch entstehen: Die Felder werden aus geprüften Argumenten
zusammengesetzt, und das Entscheidungsfeld ist nicht setzbar.

Format-Kopplung: Eintrags-Heading und Feld-Präfixe sind im Header von `observations.md`
kanonisch festgelegt – dieselbe Kopplung wie `obs_parse.py` und `check-obs-capture.py`.
"""
import re
from pathlib import Path

from obs_parse import OBS_FILE, repo_root, running_session

IMPACT_WERTE = ("KRITISCH", "HOCH", "MITTEL", "GERING")
HAEUFIGKEIT_WERTE = ("gelegentlich", "häufig", "dauerhaft")
KATEGORIE_WERTE = ("PROZESS", "AGENT", "QUALITÄT", "TOOLING")

# Genau der Wert, den check-obs-capture.py bei der Erfassung zulässt.
KANON_OFFEN = "offen - beim Drain Kandidaten erstellen und bewerten"

_HEADING = re.compile(r"^## (OBS-S\d+-\d+)", re.M)


def obs_path(root: Path | None = None) -> Path:
    return (root or repo_root()) / OBS_FILE


def entry_spans(text: str) -> dict[str, tuple[int, int]]:
    """OBS-ID → (Start, Ende) als Zeichen-Offsets im Text; Ende = vor der nächsten Überschrift."""
    treffer = list(_HEADING.finditer(text))
    spans = {}
    for i, match in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        spans[match.group(1)] = (match.start(), ende)
    return spans


VORPRAEGUNG_FELD = "Vorprägung"
_VORPRAEGUNG_RE = re.compile(rf"^- {VORPRAEGUNG_FELD}:.*$", re.M)


def get(text: str, oid: str, mit_vorpraegung: bool = False) -> str | None:
    """Vollständiger Text eines Eintrags (None, wenn es ihn nicht gibt).

    Das Feld `Vorprägung` wird standardmäßig **nicht** ausgegeben, sondern durch einen Hinweis
    ersetzt (OBS-S112-8). Grund: Es enthält Lösungsideen, Ursachenvermutungen oder
    Analogieschlüsse, die die Kandidatenbildung im Drain prägen. Eine Regel „erst eigene
    Kandidaten, dann bewerten" käme zu spät – wer den Volltext gelesen hat, ist geprägt.
    Der Hinweis ist Pflicht und kein Schmuck: Ein stumm verborgenes Feld wäre so verloren wie
    ein getilgtes, nur unauffälliger.
    """
    span = entry_spans(text).get(oid)
    if not span:
        return None
    block = text[span[0]:span[1]].rstrip()
    if not (mit_vorpraegung or not _VORPRAEGUNG_RE.search(block)):
        hinweis = (
            f"- ⚠ {VORPRAEGUNG_FELD} vorhanden (Lösungsideen/Ursachenvermutungen) – erst eigene "
            f"Kandidaten bilden und dem User vorlegen, dann abrufen:\n"
            f"    python3 .claude/scripts/obs.py get {oid} --vorprägung"
        )
        block = _VORPRAEGUNG_RE.sub(lambda _: hinweis, block, count=1)

    # Eingehende Kanten anzeigen, statt sie zu spiegeln: Die Kante steht nur einmal (beim
    # nennenden Eintrag) und kann darum nicht auseinanderlaufen – wer diesen Eintrag liest,
    # sieht trotzdem, dass er Teil einer Einheit ist.
    eingehend = eingehende_kanten(text, oid)
    if eingehend:
        block += f"\n- {EINGEHEND_MARKER} {', '.join(eingehend)}"
    return block


def eingehende_kanten(text: str, oid: str) -> list[str]:
    """IDs, die `oid` in ihrem `Zusammen-erledigen`-Feld nennen."""
    treffer = []
    for andere, span in entry_spans(text).items():
        if andere == oid:
            continue
        feld = re.search(rf"^- {re.escape(ZUSAMMEN_FELD)}:\s*(.+)$",
                         text[span[0]:span[1]], flags=re.M)
        if feld and oid in re.findall(r"OBS-S\d{3}-\d+", feld.group(1)):
            treffer.append(andere)
    return sorted(treffer)


def next_id(text: str, session: int) -> str:
    """Nächste freie ID für diese Session (`OBS-S<NNN>-<n>`)."""
    belegt = [
        int(m.group(1))
        for oid in entry_spans(text)
        if (m := re.fullmatch(rf"OBS-S0*{session}-(\d+)", oid))
    ]
    return f"OBS-S{session:03d}-{max(belegt, default=0) + 1}"


def _pruefe(name: str, wert: str, erlaubt: tuple[str, ...]) -> None:
    if wert not in erlaubt:
        raise ValueError(f"{name}: '{wert}' ist nicht zulässig. Erlaubt: {', '.join(erlaubt)}")


ZUSAMMEN_FELD = "Zusammen-erledigen"
ZUSAMMEN_KEINER = "keiner"
_OBS_ID_RE = re.compile(r"^OBS-S\d{3}-\d+$")


EINGEHEND_MARKER = "⇦ von hier aus zusammen erledigbar (eingehende Kante, steht im anderen Eintrag):"


def _pruefe_ziele(oid: str, ziele: list[str], text: str) -> None:
    """Referenzielle Integrität der Kanten – zur Schreibzeit, nicht als späterer Audit.

    Bewusst KEINE Spiegelung A<->B: `obs-drain.cluster()` macht die Kante beim Lesen ohnehin
    ungerichtet, eine zweite Kopie könnte nur auseinanderlaufen. Was der Mechanismus dagegen
    nicht selbst merkt, ist ein Ziel, das es gar nicht gibt – unbekannte IDs verwirft er
    stillschweigend, die Kante fällt also lautlos aus. Genau das wird hier verhindert.
    """
    bekannt = set(entry_spans(text))
    if oid in ziele:
        raise ValueError(f"{ZUSAMMEN_FELD}: {oid} kann nicht auf sich selbst zeigen.")
    unbekannt = [z for z in ziele if z not in bekannt]
    if unbekannt:
        raise ValueError(
            f"{ZUSAMMEN_FELD}: {', '.join(unbekannt)} existiert nicht in {OBS_FILE}. "
            f"Offene Einträge zeigt `obs.py list-offen` (Vertipper? falsche Session-Nummer?).")


def _pruefe_zusammen(wert: str) -> str:
    """Pflichtangabe: OBS-IDs oder `keiner`.

    Pflicht statt optional, weil ein fehlendes Feld von „geprüft, es gibt keine" nicht zu
    unterscheiden wäre. Keine Freitexte, weil ein unlesbarer Wert im Drain still auf „keine
    Kante" zurückfiele – und damit wieder wie eine echte Negativ-Angabe aussähe.
    """
    wert = (wert or "").strip()
    if not wert:
        raise ValueError(
            f"{ZUSAMMEN_FELD} ist Pflicht: OBS-IDs, die *eine* Lösung mit erledigen würde, "
            f"sonst '{ZUSAMMEN_KEINER}'. Offene Titel zeigt `obs.py list-offen`.")
    if wert.lower() == ZUSAMMEN_KEINER:
        return ZUSAMMEN_KEINER
    teile = [t.strip() for t in wert.split(",") if t.strip()]
    ungueltig = [t for t in teile if not _OBS_ID_RE.match(t)]
    if ungueltig:
        raise ValueError(
            f"{ZUSAMMEN_FELD}: '{', '.join(ungueltig)}' ist keine OBS-ID. Erlaubt sind "
            f"OBS-S<NNN>-<n> (komma-getrennt) oder '{ZUSAMMEN_KEINER}'.")
    return ", ".join(teile)


def format_entry(oid: str, titel: str, quelle: str, impact: str, haeufigkeit: str,
                 kategorie: str, kontext: str, beobachtung: str, bezug: str | None,
                 zusammen: str = "", vorpraegung: str | None = None) -> str:
    """Baut einen formatgetreuen Eintrag. `Entscheidung/Maßnahme` ist bewusst nicht setzbar.

    `vorpraegung` nimmt auf, was die Kandidatenbildung prägen würde – genannte Lösungen,
    vermutete Ursachen, Analogieschlüsse. Es ersetzt den früheren Ausnahme-Marker: Die
    Information geht nicht verloren, wird beim Standardzugriff aber nicht mitgelesen (s. `get`).
    """
    _pruefe("Impact", impact, IMPACT_WERTE)
    _pruefe("Häufigkeit", haeufigkeit, HAEUFIGKEIT_WERTE)
    _pruefe("Kategorie", kategorie, KATEGORIE_WERTE)
    zusammen_wert = _pruefe_zusammen(zusammen)
    if not titel.strip() or not beobachtung.strip():
        raise ValueError("Titel und Beobachtung dürfen nicht leer sein.")

    zeilen = [
        f"## {oid} – {titel.strip()}",
        f"- Quelle: {quelle.strip()}",
        "- Status: NEU",
        f"- Impact: {impact}    Häufigkeit: {haeufigkeit}",
        f"- Kategorie: {kategorie}    Kontext: {kontext.strip()}",
        f"- Beobachtung: {beobachtung.strip()}",
    ]
    # Zwischen Beobachtung und Entscheidung: Beim Lesen der Datei ist damit sichtbar, wo die
    # neutrale Schilderung endet und das Vorgeprägte beginnt.
    if vorpraegung and vorpraegung.strip():
        zeilen.append(f"- {VORPRAEGUNG_FELD}: {vorpraegung.strip()}")
    zeilen += [
        f"- {ZUSAMMEN_FELD}: {zusammen_wert}",
        f"- Entscheidung/Maßnahme: {KANON_OFFEN}",
    ]
    if bezug and bezug.strip():
        zeilen.append(f"- Bezug: {bezug.strip()}")
    return "\n".join(zeilen) + "\n"


def add(text: str, session: int, **felder) -> tuple[str, str]:
    """Hängt einen neuen Eintrag an. Liefert (neuer Dateiinhalt, vergebene ID)."""
    oid = next_id(text, session)
    _pruefe_ziele(oid, re.findall(r"OBS-S\d{3}-\d+", felder.get("zusammen") or ""), text)
    eintrag = format_entry(oid, **felder)
    return text.rstrip("\n") + "\n\n" + eintrag, oid


def set_fields(text: str, oid: str, status: str | None = None,
               entscheidung: str | None = None, zusammen: str | None = None) -> str:
    """Ersetzt Status, Entscheidung und/oder die `Zusammen-erledigen`-Kanten eines Eintrags.

    `zusammen` wird **eingefügt**, wenn das Feld fehlt – Einträge aus der Zeit vor der
    Pflichtangabe haben es nicht, und der Drain muss Kanten beidseitig korrigieren können.
    """
    span = entry_spans(text).get(oid)
    if not span:
        raise ValueError(f"{oid} existiert nicht in {OBS_FILE}.")

    block = text[span[0]:span[1]]
    if zusammen is not None:
        _pruefe_ziele(oid, re.findall(r"OBS-S\d{3}-\d+", zusammen), text)
        zeile = f"- {ZUSAMMEN_FELD}: {_pruefe_zusammen(zusammen)}"
        vorhanden = re.compile(rf"^- {re.escape(ZUSAMMEN_FELD)}:.*$", re.M)
        if vorhanden.search(block):
            block = vorhanden.sub(lambda _: zeile, block, count=1)
        else:
            # Dieselbe Position wie bei neuen Einträgen: hinter der Beobachtung (bzw. der
            # Vorprägung, die zwischen beiden steht), vor der Entscheidung.
            anker = re.compile(r"^- Entscheidung/Maßnahme:", re.M)
            if not anker.search(block):
                raise ValueError(f"{oid} hat kein Feld `- Entscheidung/Maßnahme:` – "
                                 f"Datei von Hand prüfen.")
            block = anker.sub(lambda m: zeile + "\n" + m.group(0), block, count=1)

    for feld, wert in (("Status", status), ("Entscheidung/Maßnahme", entscheidung)):
        if wert is None:
            continue
        muster = re.compile(rf"^- {re.escape(feld)}:.*$", re.M)
        if not muster.search(block):
            raise ValueError(f"{oid} hat kein Feld `- {feld}:` – Datei von Hand prüfen.")
        # Ersetzung als Funktion, nicht als String: Ein String-Argument wäre ein
        # Regex-Ersetzungs-Template, in dem `\s` mit „bad escape“ abbricht und `\1`
        # still durch eine Regex-Gruppe ersetzt würde. Entscheidungstexte zitieren
        # regelmäßig Muster und Pfade – der Wert muss literal bleiben.
        neuer_wert = f"- {feld}: {wert}"
        block = muster.sub(lambda _: neuer_wert, block, count=1)

    return text[:span[0]] + block + text[span[1]:]


def append_beobachtung(text: str, oid: str, zusatz: str) -> str:
    """Hängt `zusatz` an die Beobachtung eines bestehenden Eintrags an.

    Für die Konsolidierung aus dem Drain-Skill: Tritt dasselbe Problem an anderer Stelle
    erneut auf, wird der tragende Eintrag erweitert statt ein zweiter angelegt. Ohne diesen
    Weg bliebe dafür nur der Hand-Edit der ganzen Datei – also genau der Pfad, den die
    Script-Pflicht vermeidet.

    Die Beobachtung ist EIN Feld auf EINER Zeile; der Zusatz wird deshalb mit Leerzeichen
    angefügt, nicht mit Zeilenumbruch.
    """
    span = entry_spans(text).get(oid)
    if not span:
        raise ValueError(f"{oid} existiert nicht in {OBS_FILE}.")

    block = text[span[0]:span[1]]
    muster = re.compile(r"^- Beobachtung:.*$", re.M)
    treffer = muster.search(block)
    if not treffer:
        raise ValueError(f"{oid} hat kein Feld `- Beobachtung:` – Datei von Hand prüfen.")

    # Ersetzung als Funktion: der Text bleibt literal (kein Regex-Template, s. set_fields).
    erweitert = f"{treffer.group(0).rstrip()} {zusatz.strip()}"
    block = muster.sub(lambda _: erweitert, block, count=1)
    return text[:span[0]] + block + text[span[1]:]


def laufende_session(root: Path | None = None) -> int:
    """Nummer der laufenden Session (Mechanik: `obs_parse.running_session`)."""
    session = running_session(root or repo_root())
    if session is None:
        raise ValueError("Session-Nummer nicht bestimmbar – docs/history/sessions/ fehlt.")
    return session
