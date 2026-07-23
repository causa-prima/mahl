#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): keine Lösungskandidaten bei der OBS-Erfassung.

Ein **neu** in `docs/kaizen/observations.md` erfasster Eintrag darf im Feld
`- Entscheidung/Maßnahme:` genau einen von zwei Werten tragen: `offen` oder
`offen - beim Drain Kandidaten erstellen und bewerten`. Freie Prosa ist bewusst NICHT erlaubt –
auch nicht hinter dem Token: sonst wandert der Lösungskandidat einfach dorthin („offen – Richtung: …"),
und genau so ist die Regel bisher unterlaufen worden. Ebenso wenig gehören offene *Fragen* in
dieses Feld. Was beobachtet wurde, gehört ins Feld `- Beobachtung:`; die Entscheidung trifft
der Drain. Ein hier notierter Kandidat ankert den bewusst frischen Drain-Agenten
(Anchoring-Bias) und untergräbt dessen Debiasing-Zweck. Die Regel steht im Header von
`observations.md` und in `closing-session` Schritt 2, wurde aber wiederholt verletzt –
Lese-Disziplin reicht nicht, deshalb dieser syntaktische Guard.

Scope:
- **Nur** `docs/kaizen/observations.md`; jede andere Datei passiert ungeprüft.
- Geprüft werden **nur neu hinzukommende** OBS-IDs (im Post-Inhalt, nicht im Pre-Inhalt).
  Bestehende Einträge sind frei änderbar – genau das tut der Drain, wenn er entscheidet.
- **Zeilen-Ausnahme:** ein `obs-ok`-Marker in der Entscheidungs-Zeile hebt die Prüfung auf
  (bewusste Einzelfälle, z.B. ein umnummerierter Bestands-Eintrag).

Format-Kopplung: Eintrags-Heading `## OBS-S<NNN>-<n>` und Feld-Präfix `- Entscheidung/Maßnahme:`
sind im Header von `observations.md` kanonisch festgelegt (dieselbe Kopplung wie `obs_parse.py`).

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import re
import sys
from pathlib import Path

OBS_FILE = "docs/kaizen/observations.md"

_ENTRY_SPLIT_RE = re.compile(r"^## (OBS-S\d+-\d+)", re.M)
_DECISION_RE = re.compile(r"^- Entscheidung/Maßnahme:\s*(.*)$", re.M)
_OBS_OK = "obs-ok"

# Feld-Zeile = uneingerückt, benannt, mit Doppelpunkt. Eingerückte Bullets sind Prosa.
_FIELD_RE = re.compile(r"^- ([^:\n]{1,40}?):", re.M)
ALLOWED_FIELDS = ("Quelle", "Status", "Impact", "Kategorie", "Beobachtung", "Entscheidung/Maßnahme", "Bezug")
REQUIRED_FIELDS = tuple(f for f in ALLOWED_FIELDS if f != "Bezug")  # Bezug ist laut Header optional

# Explizite Vorschlags-Ansagen. Bewusst NICHT enthalten: modale Wendungen (sollte/müsste/könnte) –
# die beschreiben am Bestand überwiegend ein Risiko, nicht einen Vorschlag (zu viele Fehlalarme).
_PROPOSAL_RE = re.compile(r"Lösungs(?:vorschlag|richtung|idee|ansatz|kandidat)|\b(?:Kandidat|Vorschlag|Idee|Abhilfe|Fix)\s*:", re.I)

# Abschließende Liste der bei der Erfassung zulässigen Werte (normalisiert).
CANONICAL_OPEN_VALUES = ("offen", "offen - beim Drain Kandidaten erstellen und bewerten")

_DASHES = str.maketrans({"–": "-", "—": "-"})
_WHITESPACE_RE = re.compile(r"\s+")


def is_obs_file(file_path: str) -> bool:
    """True nur für das OBS-Backlog selbst (absolut wie repo-relativ angegeben)."""
    return Path(file_path).as_posix().endswith(OBS_FILE)


def parse_obs_entries(content: str) -> dict[str, str]:
    """OBS-ID → Eintrags-Rumpf (alles zwischen dieser und der nächsten Eintrags-Überschrift)."""
    parts = _ENTRY_SPLIT_RE.split(content)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def parse_obs_decisions(content: str) -> dict[str, str | None]:
    """OBS-ID → Wert des Feldes `- Entscheidung/Maßnahme:` (None, wenn das Feld fehlt)."""
    return {oid: decision_of(body) for oid, body in parse_obs_entries(content).items()}


def decision_of(body: str) -> str | None:
    match = _DECISION_RE.search(body)
    return match.group(1).strip() if match else None


def field_names(body: str) -> list[str]:
    """Namen der Feld-Zeilen eines Eintrags, in Vorkommens-Reihenfolge."""
    return [name.strip() for name in _FIELD_RE.findall(body)]


def _normalize(value: str) -> str:
    """Blendet aus, was keine Bedeutung trägt: Gedankenstrich-Variante, Groß-/Kleinschreibung,
    Mehrfach-/Rand-Leerzeichen."""
    return _WHITESPACE_RE.sub(" ", value.translate(_DASHES).strip()).lower()


_CANONICAL_NORMALIZED = frozenset(_normalize(v) for v in CANONICAL_OPEN_VALUES)


def is_canonical_open(value: str | None) -> bool:
    """True nur für die zulässigen Erfassungs-Werte; alles andere ist inhaltliche Vorwegnahme."""
    return bool(value) and _normalize(value) in _CANONICAL_NORMALIZED


def check_entry(body: str) -> list[str]:
    """Begründungen, warum dieser neu erfasste Eintrag die Erfassungs-Regeln verletzt."""
    reasons = []

    decision = decision_of(body)
    if not is_canonical_open(decision):
        shown = "(Feld fehlt)" if decision is None else f"„{decision[:70]}“"
        reasons.append(f"`- Entscheidung/Maßnahme:` = {shown}")

    names = field_names(body)
    reasons += [f"unbekanntes Feld `- {n}:`" for n in names if n not in ALLOWED_FIELDS]
    reasons += [f"Pflichtfeld `- {n}:` fehlt" for n in REQUIRED_FIELDS if n not in names]

    proposal = _PROPOSAL_RE.search(body)
    if proposal:
        reasons.append(f"Lösungs-Ansage „{proposal.group(0)}“ im Eintrags-Text")

    return reasons


def find_violations(pre: str, post: str) -> list[tuple[str, str]]:
    """(OBS-ID, Begründung) für jeden neu erfassten Eintrag, der die Regeln verletzt."""
    known = parse_obs_entries(pre).keys()
    return [
        (oid, " · ".join(reasons))
        for oid, body in parse_obs_entries(post).items()
        if oid not in known and _OBS_OK not in body and (reasons := check_entry(body))
    ]


def read_file_text(file_path: str) -> str:
    """Aktueller Datei-Inhalt; "" wenn die Datei (noch) nicht existiert."""
    path = Path(file_path)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def compute_post_content(tool: str, tool_input: dict, pre: str) -> str | None:
    """Simuliert den Datei-Inhalt nach Anwendung des Edits/Writes."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if old and old in pre:
            count = -1 if tool_input.get("replace_all") else 1
            return pre.replace(old, new, count)
        return pre  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    try:
        tool = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if tool not in ("Edit", "Write") or not file_path or not is_obs_file(file_path):
            sys.exit(0)

        pre = read_file_text(file_path)
        post = compute_post_content(tool, tool_input, pre)
        if post is None:
            sys.exit(0)

        violations = find_violations(pre, post)
        if violations:
            print("❌ OBS-Erfassung (Poka-Yoke): neu erfasster Eintrag verletzt die Erfassungs-Regeln:", file=sys.stderr)
            for oid, reason in violations:
                print(f"  - {oid}: {reason}", file=sys.stderr)
            allowed = "\n".join(f"    - Entscheidung/Maßnahme: {v}" for v in CANONICAL_OPEN_VALUES)
            print(
                "  Ein neu erfasster OBS beschreibt NUR, was beobachtet wurde – die Entscheidung trifft "
                "der Drain mit frischem Blick, und jeder hier notierte Kandidat ankert ihn.\n"
                "  1. `- Entscheidung/Maßnahme:` trägt GENAU einen dieser zwei Werte – nichts davor, "
                f"nichts dahinter:\n{allowed}\n"
                f"  2. Nur diese Felder sind zulässig: {', '.join(f'`- {f}:`' for f in ALLOWED_FIELDS)} "
                "(`- Bezug:` optional, der Rest Pflicht). Ein eigenes Feld für Kandidaten/Lösungsideen "
                "ist genau die Umgehung, die hier verhindert wird.\n"
                "  3. Keine Lösungs-Ansage im Eintrags-Text (`Lösungsvorschlag:`, `Idee:`, `Kandidat:` …). "
                "Ein Risiko zu beschreiben (`X könnte passieren`) ist ausdrücklich erlaubt – gemeint ist "
                "nur die vorweggenommene Abhilfe.\n"
                "  Was dir aufgefallen ist, gehört in `- Beobachtung:` – dort darf es beliebig ausführlich "
                "stehen, inklusive der Frage, die sich dir stellt und der Kosten, die es verursacht hat. "
                "Bewusster Einzelfall (z.B. Umnummerierung eines Bestands-Eintrags) → `obs-ok`-Marker "
                "irgendwo in den Eintrag.",
                file=sys.stderr,
            )
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-obs-capture: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
