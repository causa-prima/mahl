"""Berechnet den Jenga-Score aus docs/kaizen/lessons_learned.md.

Aufruf: python .claude/scripts/jenga_score.py [--file <pfad>]
Output: Jenga-Score + Zähltabelle (Schwere × Kategorie × Kontext)

Formel (Start 100):
  -5  pro Session
  -25 pro KRITISCH-Finding
  -10 pro HOCH-Finding
  -3  pro MITTEL-Finding
  -1  pro GERING-Finding
"""

import argparse
import os
import re
import sys
from collections import defaultdict

REPO_ROOT = os.environ.get("CLAUDE_PROJECT_DIR", "/mnt/c/Users/kieritz/source/repos/mahl")
DEFAULT_FILE = os.path.join(REPO_ROOT, "docs", "kaizen", "lessons_learned.md")

DEDUCTIONS = {"KRITISCH": 25, "HOCH": 10, "MITTEL": 3, "GERING": 1}
SESSION_DEDUCTION = 5
START_SCORE = 100

# Passt auf: - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
FINDING_RE = re.compile(
    r"^\s*-\s+\*\*\[(?P<schwere>KRITISCH|HOCH|MITTEL|GERING)\]\s*"
    r"\[(?P<kategorie>\w+(?:-\w+)*)\]\s*"
    r"\[(?P<kontext>\w+(?:-\w+)*)\]"
)
SESSION_RE = re.compile(r"^##\s+Session\s+\d+")


def parse(path: str) -> tuple[int, list[dict]]:
    """Gibt (session_count, findings) zurück."""
    sessions = 0
    findings: list[dict] = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            if SESSION_RE.match(line):
                sessions += 1
                continue
            m = FINDING_RE.match(line)
            if m:
                findings.append({
                    "schwere": m.group("schwere"),
                    "kategorie": m.group("kategorie"),
                    "kontext": m.group("kontext"),
                })

    return sessions, findings


def compute_score(sessions: int, findings: list[dict]) -> int:
    score = START_SCORE
    score -= sessions * SESSION_DEDUCTION
    for f in findings:
        score -= DEDUCTIONS[f["schwere"]]
    return score


def render_table(findings: list[dict]) -> str:
    """Zähltabelle: Schwere × Kategorie × Kontext."""
    if not findings:
        return "  (keine Findings)\n"

    # Zählen
    by_schwere: dict[str, int] = defaultdict(int)
    by_kategorie: dict[str, int] = defaultdict(int)
    by_kontext: dict[str, int] = defaultdict(int)
    cross: dict[tuple, int] = defaultdict(int)  # (schwere, kontext)

    for f in findings:
        by_schwere[f["schwere"]] += 1
        by_kategorie[f["kategorie"]] += 1
        by_kontext[f["kontext"]] += 1
        cross[(f["schwere"], f["kontext"])] += 1

    lines = []

    # Zeile 1: Schwere-Zusammenfassung
    schwere_order = ["KRITISCH", "HOCH", "MITTEL", "GERING"]
    parts = [f"{s}: {by_schwere[s]}" for s in schwere_order if by_schwere[s]]
    lines.append("  Schwere:   " + "  |  ".join(parts))

    # Zeile 2: Kategorie-Zusammenfassung
    kat_parts = sorted(by_kategorie.items(), key=lambda x: -x[1])
    lines.append("  Kategorie: " + "  |  ".join(f"{k}: {v}" for k, v in kat_parts))

    # Zeile 3: Kontext-Zusammenfassung
    ctx_parts = sorted(by_kontext.items(), key=lambda x: -x[1])
    lines.append("  Kontext:   " + "  |  ".join(f"{k}: {v}" for k, v in ctx_parts))

    # Kreuz-Tabelle wenn > 1 Schwere-Stufe vorhanden
    active_schwere = [s for s in schwere_order if by_schwere[s]]
    active_kontext = sorted(by_kontext.keys())
    if len(active_schwere) > 1 and len(active_kontext) > 1:
        lines.append("")
        col_w = max(len(k) for k in active_kontext) + 2
        header = "  " + " " * 10 + "".join(k.ljust(col_w) for k in active_kontext)
        lines.append(header)
        for s in active_schwere:
            row = f"  {s:<10}" + "".join(
                str(cross.get((s, k), 0)).ljust(col_w) for k in active_kontext
            )
            lines.append(row)

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Berechnet den Jenga-Score.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="Pfad zur lessons_learned.md")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Fehler: Datei nicht gefunden: {args.file}", file=sys.stderr)
        return 1

    sessions, findings = parse(args.file)
    score = compute_score(sessions, findings)

    # Ausgabe
    status = "RETRO FÄLLIG" if score <= 0 else "OK"
    print(f"\nJenga-Score: {score} / {START_SCORE}  [{status}]")
    print(f"  Sessions: {sessions} × -{SESSION_DEDUCTION} = -{sessions * SESSION_DEDUCTION}")
    print(f"  Findings: {len(findings)} gesamt")
    print()
    print("Zähltabelle:")
    print(render_table(findings))

    return 0 if score > 0 else 2  # exit 2 = Retro fällig


if __name__ == "__main__":
    sys.exit(main())
