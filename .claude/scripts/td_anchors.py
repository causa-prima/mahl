#!/usr/bin/env python3
"""Anker-Grammatik für Fälligkeiten (`**Fällig:**`) – geteilt von Schreib- und Startzeit.

Ein Fälligkeits-Feld hat die Form

    **Fällig:** <Anker>[, <Anker>…] – <Freitext-Erläuterung>

Der **Kopf** vor dem Gedankenstrich ist maschinenlesbar, der Rest bleibt Prosa und trägt
weiter die Nuance („(c) und (d) je mit ihrem Gherkin-Szenario"). Vorher war das ganze Feld
Prosa; `Fällig:`-Regel 3 („so konkret wie möglich, ggf. mit Fallback") war damit eine
Ermessensfrage, die niemand prüfen konnte.

Anker-Vokabular:

    jetzt              sofort (zusätzlich: TD-ID muss in AGENT_MEMORY stehen)
    Phase:MVP          Phasenwechsel – tritt ein, wenn AGENT_MEMORY `**Phase:**` sie erreicht
    S123               Spätestens-Termin – tritt ein, wenn die laufende Session sie erreicht
    Szenario:„Titel"   ein Gherkin-Szenario – tritt ein, wenn sein Lauf drankommt
    US-602             eine Story – nur gültig, SOLANGE die Story keine Szenarien hat
    TD-S089-1          ein anderer Eintrag – tritt ein, wenn jener behoben (= entfernt) ist

**Die tragende Regel: jeder Eintrag braucht mindestens einen *terminierten* Anker.**
Terminiert sind `jetzt`, `Phase:`, `S<NNN>` und `Szenario:` mit Lauf-Zuordnung. NICHT
terminiert sind `US-NNN` (die Story kann beliebig lange ungeplant bleiben) und `Szenario:`
ohne `# @run-N`-Zuordnung; ein `TD-`-Anker erbt die Terminierung aus der Kette, die dafür
zyklenfrei sein muss. Grund: Ein Anker, der nur eintreten *kann*, lässt den Eintrag
lautlos verwaisen – genau der Fall, den OBS-S099-1 beschreibt (Schuld in Bereichen, zu denen
nie ein Lauf kommt).

Warum `US-NNN` mit dem Workshop ungültig wird: Vor dem Workshop ist die Story die feinste
verfügbare Granularität. Danach steht fest, zu welchem Szenario die Schuld gehört – oder die
ehrliche Antwort ist `jetzt` (vor Implementierungsbeginn zu erledigen). Ein Story-Anker, der
den Workshop überlebt, behauptet eine Ungenauigkeit, die es nicht mehr gibt.

Konsumenten: `check-td-capture.py` (Schreibzeit: existiert das Referenzierte, ist es
terminiert?) und das `td-due`-Modul von `session-agenda.py` (Startzeit: ist es eingetreten?).
Ein Code-Pfad, zwei Aufrufstellen – sonst driften die beiden Sichten auseinander.
"""
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _feature import parse_feature  # noqa: E402

# Trennt den maschinenlesbaren Kopf von der Prosa. Erstes Vorkommen zählt: die Prosa selbst
# enthält regelmäßig weitere Gedankenstriche.
_KOPF_TRENNER_RE = re.compile(r"\s+[–—]\s+")

# Ein Token je Alternative. Bewusst tokenisierend statt an Kommata splittend: Szenario-Titel
# enthalten Kommata, ein Split zerschnitte sie mitten im Titel.
# Reihenfolge ist bedeutsam – `TD-S089-1` muss vor `S089` greifen, sonst matcht der
# Session-Anker den Teilstring innerhalb der TD-ID.
_ANKER_RE = re.compile(
    r"""
      (?P<td>TD-S\d{3}-\d+)
    | (?P<jetzt>\bjetzt\b)
    | Phase:(?P<phase>[A-Za-z0-9_]+)
    | Szenario:(?:„(?P<sz_de>[^"„]+)"|"(?P<sz_gerade>[^"]+)")
    | (?P<story>US-\d+)
    | (?P<session>\bS\d{3}\b)
    """,
    re.X,
)

JETZT, PHASE, SESSION, SZENARIO, STORY, TD = "jetzt", "phase", "session", "szenario", "story", "td"


@dataclass(frozen=True)
class Anker:
    art: str
    wert: str = ""


@dataclass(frozen=True)
class Kontext:
    """Alles, wogegen Anker aufgelöst werden. Fehlende Angaben = unbestimmbar, nie „eingetreten"."""
    phase: str | None = None
    story: str | None = None
    session: int | None = None
    # Szenario-Titel → {"lauf": int|None, "lauf_offen": bool, "implementiert": bool}
    szenarien: dict[str, dict] = field(default_factory=dict)
    # Storys, für die bereits Szenarien existieren (z.B. {"US-904"}) → Story-Anker ungültig
    storys_mit_szenarien: frozenset[str] = frozenset()
    # TD-ID → roher `Fällig:`-Wert, für die Kettenauflösung
    td_faelligkeiten: dict[str, str] = field(default_factory=dict)


def kopf_und_prosa(faellig: str) -> tuple[str, str]:
    """Zerlegt den Feldwert in maschinenlesbaren Kopf und Prosa-Rest."""
    teile = _KOPF_TRENNER_RE.split(faellig.strip(), maxsplit=1)
    return (teile[0].strip(), teile[1].strip() if len(teile) > 1 else "")


def parse(faellig: str) -> tuple[list[Anker], list[str]]:
    """(Anker, Syntaxfehler) für einen `**Fällig:**`-Wert.

    Syntaxfehler entstehen, wenn im Kopf etwas steht, das kein bekannter Anker ist – sonst
    würde ein Vertipper (`Phase-MVP` statt `Phase:MVP`) still als „kein Anker" durchgehen und
    der Eintrag wäre unbemerkt ohne Fälligkeit.
    """
    kopf, _ = kopf_und_prosa(faellig)
    if not kopf:
        return [], ["`**Fällig:**` ist leer"]

    anker: list[Anker] = []
    rest = kopf
    for treffer in _ANKER_RE.finditer(kopf):
        gruppen = treffer.groupdict()
        if gruppen["td"]:
            anker.append(Anker(TD, gruppen["td"]))
        elif gruppen["jetzt"]:
            anker.append(Anker(JETZT))
        elif gruppen["phase"]:
            anker.append(Anker(PHASE, gruppen["phase"]))
        elif gruppen["sz_de"] or gruppen["sz_gerade"]:
            anker.append(Anker(SZENARIO, gruppen["sz_de"] or gruppen["sz_gerade"]))
        elif gruppen["story"]:
            anker.append(Anker(STORY, gruppen["story"]))
        elif gruppen["session"]:
            anker.append(Anker(SESSION, gruppen["session"]))
        rest = rest.replace(treffer.group(0), "", 1)

    unbekannt = rest.replace(",", " ").strip()
    fehler = []
    if unbekannt:
        fehler.append(
            f"unbekannter Anker im Kopf: {unbekannt!r} – zulässig sind `jetzt`, `Phase:<NAME>`, "
            "`S<NNN>`, `Szenario:„<Titel>\"`, `US-<NNN>`, `TD-S<NNN>-<n>`; alles Erklärende "
            "gehört hinter den Gedankenstrich"
        )
    if not anker:
        fehler.append("kein Anker im Kopf gefunden")
    return anker, fehler


def _szenario_terminiert(anker: Anker, ktx: Kontext) -> bool:
    """Ein Szenario-Anker ist nur terminiert, wenn das Szenario einem OFFENEN Lauf zugehört.

    Ohne `# @run-N` ist das Szenario zwar geschrieben, aber von keinem Plan eingeplant – der
    Anker könnte beliebig lange nicht eintreten. Real vorgekommen: die drei Szenarien in
    `features/interaction.feature` („Implementierungs-Scope: nach MVP") tragen keinen Run-Tag.
    """
    eintrag = ktx.szenarien.get(anker.wert)
    return bool(eintrag and eintrag["lauf"] is not None and eintrag["lauf_offen"])


def ist_terminiert(anker: Anker, ktx: Kontext, _kette: frozenset[str] = frozenset()) -> bool:
    """Terminiert ein einzelner Anker den Eintrag?"""
    if anker.art in (JETZT, PHASE, SESSION):
        return True
    if anker.art == SZENARIO:
        return _szenario_terminiert(anker, ktx)
    if anker.art == TD:
        return _kette_terminiert(anker.wert, ktx, _kette)
    return False  # STORY: die Story kann beliebig lange ungeplant bleiben


def _kette_terminiert(td_id: str, ktx: Kontext, kette: frozenset[str]) -> bool:
    """Erbt ein `TD-`-Anker eine Terminierung? Zyklen brechen die Kette ab (nicht terminiert).

    Ein Zyklus ist kein theoretischer Fall: TD-S090-2 und TD-S101-1 verwiesen wechselseitig
    aufeinander, während beide real an MVP hingen.
    """
    if td_id in kette or td_id not in ktx.td_faelligkeiten:
        return False
    anker, _ = parse(ktx.td_faelligkeiten[td_id])
    weiter = kette | {td_id}
    return any(ist_terminiert(a, ktx, weiter) for a in anker)


def validiere(td_id: str, faellig: str, ktx: Kontext) -> list[str]:
    """Schreibzeit-Prüfung: Verstöße gegen die Anker-Grammatik (leer = in Ordnung)."""
    anker, fehler = parse(faellig)
    if fehler:
        return fehler

    for a in anker:
        if a.art == SZENARIO and a.wert not in ktx.szenarien:
            fehler.append(
                f"`Szenario:„{a.wert}\"` matcht kein Szenario in `features/` – Titel exakt "
                "übernehmen (oder das Szenario zuerst schreiben)"
            )
        elif a.art == STORY and a.wert in ktx.storys_mit_szenarien:
            fehler.append(
                f"`{a.wert}` hat bereits Szenarien – ein Story-Anker ist nur gültig, solange "
                "die Story keine hat. Häng den Eintrag auf `Szenario:„…\"` um, oder auf "
                "`jetzt`, wenn er der Implementierung vorausgehen muss"
            )
        elif a.art == TD:
            if a.wert not in ktx.td_faelligkeiten:
                fehler.append(f"`{a.wert}` existiert nicht (mehr) in `tech-debt.md`")
            elif a.wert == td_id:
                fehler.append(f"`{a.wert}` verweist auf sich selbst")

    if not fehler and not any(ist_terminiert(a, ktx, frozenset({td_id})) for a in anker):
        fehler.append(
            "kein terminierter Anker – `US-NNN`, ein `Szenario:` ohne `# @run-N`-Zuordnung und "
            "eine nicht terminierende `TD-`-Kette sagen alle nicht, WANN etwas passiert. "
            "Ergänze einen Backstop (`Phase:MVP`, `S<NNN>` oder `jetzt`)"
        )
    return fehler


def faellig_gruende(td_id: str, faellig: str, ktx: Kontext) -> list[str]:
    """Startzeit-Prüfung: warum dieser Eintrag jetzt vorzulegen ist (leer = noch nicht fällig).

    `jetzt` erzeugt bewusst KEINEN Grund: solche Einträge stehen bereits in AGENT_MEMORY und
    werden von dort vorgelegt – hier nochmals zu melden wäre die Doppelung, die OBS-S116-2
    beanstandet.
    """
    anker, fehler = parse(faellig)
    if fehler:
        return [f"Fälligkeit nicht auswertbar: {fehler[0]}"]

    gruende: list[str] = []
    for a in anker:
        if a.art == PHASE and ktx.phase and a.wert.upper() == ktx.phase.upper():
            gruende.append(f"Phase {a.wert} ist erreicht")
        elif a.art == SESSION and ktx.session is not None and int(a.wert[1:]) <= ktx.session:
            gruende.append(f"Spätestens-Termin {a.wert} ist erreicht")
        elif a.art == STORY:
            if a.wert in ktx.storys_mit_szenarien:
                gruende.append(f"{a.wert} hat inzwischen Szenarien – Anker umhängen")
            elif ktx.story and a.wert == ktx.story:
                gruende.append(f"{a.wert} ist die aktuelle Story")
        elif a.art == SZENARIO:
            gruende += _szenario_gruende(a, ktx)
        elif a.art == TD and a.wert not in ktx.td_faelligkeiten:
            gruende.append(f"{a.wert} ist behoben – dieser Eintrag hing daran")
    return gruende


def _szenario_gruende(anker: Anker, ktx: Kontext) -> list[str]:
    eintrag = ktx.szenarien.get(anker.wert)
    if eintrag is None:
        return [f"Szenario „{anker.wert}\" existiert nicht (mehr) – Titel gedriftet?"]
    if eintrag["implementiert"]:
        # Der wertvollste Check des Moduls: der Lauf ist durch, die Schuld wurde nicht
        # mitgenommen. Genau so vorgekommen – ein Lauf veränderte den Toast-Bereich, während
        # der zugehörige TD-Eintrag unbemerkt liegen blieb.
        return [f"Szenario „{anker.wert}\" ist implementiert – beim Lauf nicht mitgenommen"]
    # „Keinem Lauf zugeordnet" ist bewusst KEIN Fälligkeitsgrund: Der Zustand ist statisch und
    # zur Schreibzeit bereits behandelt (er erzwingt dort den Backstop-Anker). Als Startzeit-
    # Grund gemeldet, stünde er in jeder Session erneut da, ohne dass sich etwas geändert hätte –
    # eine Lane, die unveränderte Zustände wiederholt, wird überlesen.
    return []


# ---------------------------------------------------------------------------
# Textbasierte Extraktion (ohne Dateisystem – damit testbar ohne Repo-Fixture)
# ---------------------------------------------------------------------------

TD_HEADING_RE = re.compile(r"^## (TD-S\d{3}-\d+)", re.M)
_FAELLIG_RE = re.compile(r"^\*\*Fällig:\*\*(.*)$", re.M)
_PHASE_RE = re.compile(r"^\*\*Phase:\*\*\s*(\S+)", re.M)


def td_faelligkeiten(text: str) -> dict[str, str]:
    """TD-ID → `**Fällig:**`-Wert. Einträge ohne das Feld fehlen (der Hook fängt sie separat)."""
    teile = TD_HEADING_RE.split(text)
    ergebnis = {}
    for i in range(1, len(teile), 2):
        treffer = _FAELLIG_RE.search(teile[i + 1])
        if treffer:
            ergebnis[teile[i]] = treffer.group(1).strip()
    return ergebnis


def phase_aus_memory(memory_text: str) -> str | None:
    treffer = _PHASE_RE.search(memory_text)
    return treffer.group(1) if treffer else None


def szenario_index(feature_texte: list[str], implementiert: set[str]) -> tuple[dict, frozenset[str]]:
    """(Szenario-Index, Storys mit Szenarien) über alle Feature-Dateien.

    Ein Lauf gilt als offen, sobald eines seiner Szenarien nicht implementiert ist – dieselbe
    Definition wie in `next_run.py`, damit Anker und Lauf-Resolver nicht auseinanderlaufen.
    """
    index: dict[str, dict] = {}
    storys: set[str] = set()
    for text in feature_texte:
        ftags, _, szenarien = parse_feature(text)
        if szenarien:
            storys |= {tag.lstrip("@") for tag in ftags if tag.startswith("@US-")}
        offen_je_lauf: dict[int, bool] = {}
        for s in szenarien:
            nummer = s["run"]["number"] if s["run"] else None
            if nummer is not None and s["title"] not in implementiert:
                offen_je_lauf[nummer] = True
        for s in szenarien:
            nummer = s["run"]["number"] if s["run"] else None
            index[s["title"]] = {
                "lauf": nummer,
                "lauf_offen": offen_je_lauf.get(nummer, False),
                "implementiert": s["title"] in implementiert,
            }
    return index, frozenset(storys)


# ---------------------------------------------------------------------------
# Dateisystem-Anbindung
# ---------------------------------------------------------------------------

def lade_kontext(root: Path) -> Kontext:
    """Baut den Auflöse-Kontext aus dem Repo. Fehlende Quellen ⇒ leere Teil-Angaben (fail-open:
    ein unvollständiger Kontext darf nie einen Edit blocken, er meldet dann nur weniger)."""
    import next_run  # lokal: zieht beim reinen Parsen keine Feature-Dateien nach
    from obs_parse import current_session

    def lies(pfad: Path) -> str:
        return pfad.read_text(encoding="utf-8") if pfad.is_file() else ""

    memory = lies(root / "docs" / "AGENT_MEMORY.md")
    feature_texte = [lies(p) for p in sorted((root / "features").glob("**/*.feature"))]
    spec_dir = root / "Client" / "e2e"
    implementiert: set[str] = set()
    for spec in sorted(spec_dir.glob("**/*.spec.ts")) if spec_dir.is_dir() else []:
        implementiert |= next_run.implemented_titles_from_text(lies(spec))

    szenarien, storys = szenario_index(feature_texte, implementiert)
    return Kontext(
        phase=phase_aus_memory(memory),
        story=next_run.extract_story(memory),
        session=current_session(root),
        szenarien=szenarien,
        storys_mit_szenarien=storys,
        td_faelligkeiten=td_faelligkeiten(lies(root / "docs" / "tech-debt.md")),
    )
