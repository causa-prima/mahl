#!/usr/bin/env python3
"""obs_parse.py – geteiltes Parsing für das OBS-Backlog (docs/kaizen/observations.md).

Konsument: obs-drain.py (Session-Start-Drain). Eigenes Modul, damit das Format-Parsing
unabhängig vom Drain-Algorithmus testbar bleibt und ein zweiter Konsument es ohne
Copy-Paste nutzen könnte.

Eintrags-Format (kanonisch im Header von observations.md): `## OBS-S<NNN>-<n> – Titel`,
dann die Feld-Zeilen `- Status:` / `- Impact: … Häufigkeit: …` / `- Bezug:` … Geparkte
Items tragen ihr Ablauf-Datum in der Status-Zeile: `IN BEOBACHTUNG bis S<NNN>`.
"""
import re
import sys
from pathlib import Path

OBS_FILE = "docs/kaizen/observations.md"
SESSIONS_DIR = "docs/history/sessions"

IMPACT = {"KRITISCH": 4, "HOCH": 3, "MITTEL": 2, "GERING": 1}
FREQ = {"dauerhaft": 3, "häufig": 2, "gelegentlich": 1}


def repo_root() -> Path:
    # Script liegt in .claude/scripts/ -> zwei Ebenen hoch ist der Repo-Root.
    return Path(__file__).resolve().parents[2]


def current_session(root: Path):
    """Höchste session_NNN.md = letzte abgeschlossene; die laufende ist +1.
    None, wenn kein Sessions-Verzeichnis/keine Datei existiert (Alter unbestimmbar)."""
    nums = []
    d = root / SESSIONS_DIR
    if d.is_dir():
        for f in d.glob("session_*.md"):
            m = re.search(r"session_0*(\d+)", f.name)
            if m:
                nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else None


def score_from_keywords(text: str, table: dict, field: str = "Wert") -> float:
    """Mittel der gefundenen Schlüsselwörter (vor einer Klammer); Ranges werden so gemittelt.
    Unbekannter/fehlender Wert → 1.0 (niedrigste Stufe) + Warnung, statt still falsch zu priorisieren."""
    head = text.split("(")[0]
    found = [v for k, v in table.items() if k in head]
    if found:
        return sum(found) / len(found)
    print(f"WARNUNG: unbekannter {field}-Wert '{head.strip()[:40]}' → als 1.0 gewertet.", file=sys.stderr)
    return 1.0


def parse_entries(text: str):
    parts = re.split(r"^## (OBS-S\d+-\d+)", text, flags=re.M)
    entries = []
    for i in range(1, len(parts), 2):
        oid, body = parts[i], parts[i + 1]
        m_sess = re.match(r"OBS-S0*(\d+)-(\d+)", oid)
        session, sub = int(m_sess.group(1)), int(m_sess.group(2))

        def field(name):
            mm = re.search(rf"^- {name}:\s*(.+)", body, flags=re.M)
            return mm.group(1).strip() if mm else ""

        status = field("Status")
        impact = field("Impact").split("Häufigkeit")[0]
        freq_m = re.search(r"Häufigkeit:\s*(.+)", field("Impact"))
        freq = freq_m.group(1) if freq_m else ""
        bezug = field("Bezug")
        title = body.splitlines()[0].lstrip("– ").strip()

        # Wiedervorlage: bei geparkten Items 'IN BEOBACHTUNG bis S<NNN>' das Ablauf-Datum.
        # Erster Treffer (Status-Prosa darf davor stehen). None, wenn nicht angegeben.
        wv_m = re.search(r"\bbis\s+S0*(\d+)", status, flags=re.I)
        wiedervorlage = int(wv_m.group(1)) if wv_m else None

        # Datei-Token für Kolokation: Backtick-Tokens, die wie Dateinamen/Pfade aussehen.
        files = set()
        for tok in re.findall(r"`([^`]+)`", body):
            for word in re.split(r"[\s,()]+", tok):
                if re.search(r"\.(py|md|cs|ts|tsx|json|sh|js|yml|yaml|editorconfig)$", word) or "/" in word:
                    files.add(word.strip(".,"))

        entries.append({
            "id": oid, "session": session, "sub": sub, "status": status,
            "title": title, "bezug": bezug, "files": files,
            "wiedervorlage": wiedervorlage,
            "impact": score_from_keywords(impact, IMPACT, "Impact"),
            "freq": score_from_keywords(freq, FREQ, "Häufigkeit"),
            "impact_raw": impact.split("(")[0].strip(), "freq_raw": freq.split("(")[0].strip(),
        })
    return entries


def is_parked(status: str) -> bool:
    return status.upper().startswith("IN BEOBACHTUNG")


def is_resolved(status: str) -> bool:
    s = status.upper()
    return s.startswith("UMGESETZT") or s.startswith("VERWORFEN")


def is_due_parked(entry: dict, cur) -> bool:
    """Geparktes Item, dessen Wiedervorlage erreicht ist → zurück in den Drain.
    Ohne 'bis S<NNN>' (wiedervorlage None) sofort fällig + Warnung, damit ein
    geparktes Item nie still liegenbleibt. cur None (Alter unbestimmbar) → datierte
    bleiben geparkt, undatierte werden fällig."""
    if not is_parked(entry["status"]):
        return False
    wv = entry.get("wiedervorlage")
    if wv is None:
        print(f"WARNUNG: {entry['id']} ist IN BEOBACHTUNG ohne 'bis S<NNN>' "
              f"→ sofort fällig (Wiedervorlage nachtragen).", file=sys.stderr)
        return True
    return cur is not None and cur >= wv
