#!/usr/bin/env python3
"""obs-archive.py – verschiebt aufgelöste OBS (UMGESETZT/VERWORFEN) aus observations.md ins Archiv.

Rein mechanisch: schneidet die Blöcke aufgelöster Einträge aus der Live-Datei und hängt sie ans
Archiv an – spart dem Agenten das fehleranfällige Hand-Cut/Paste (Token-Ersparnis). Aufruf EXPLIZIT
durch das Skill `draining-observations` (Hygiene-Schritt) oder von Hand; NICHT vom Session-Start-Hook
(der bleibt read-only/advisory – obs-drain.py erinnert nur per Hygiene-Reminder).
Mechanismus & Begründung: docs/kaizen/process.md, Abschnitt "Backlog-Abbau".
"""
import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs_parse import OBS_FILE, repo_root, parse_entries, is_resolved  # noqa: E402

ARCHIVE_FILE = "docs/kaizen/archive/observations_archive.md"


def split_blocks(text: str):
    """(preamble, [(oid, raw_block), ...]). Invariante: preamble + ''.join(raw_blocks) == text
    (verlustfreie Rekonstruktion – nichts wird beim Verschieben umformatiert)."""
    parts = re.split(r"^## (OBS-S\d+-\d+)", text, flags=re.M)
    preamble = parts[0]
    blocks = [(parts[i], f"## {parts[i]}{parts[i + 1]}") for i in range(1, len(parts), 2)]
    return preamble, blocks


def archive_resolved(obs_text: str, archive_text: str):
    """Verschiebt aufgelöste Einträge (UMGESETZT/VERWORFEN) aus obs_text ins Archiv.
    Gibt (neue_obs, neues_archiv, [verschobene_ids]) zurück. Ohne Treffer unverändert."""
    preamble, blocks = split_blocks(obs_text)
    status = {e["id"]: e["status"] for e in parse_entries(obs_text)}
    kept, moved = [], []
    for oid, block in blocks:
        (moved if is_resolved(status.get(oid, "")) else kept).append((oid, block))
    new_obs = preamble + "".join(b for _, b in kept)
    if not moved:
        return new_obs, archive_text, []
    # Genau eine Leerzeile zwischen Archiv-Bestand und neuen Blöcken (kein Verkleben, keine HRs).
    if archive_text.endswith("\n\n"):
        sep = ""
    elif archive_text.endswith("\n"):
        sep = "\n"
    else:
        sep = "\n\n"
    new_archive = archive_text + sep + "".join(b for _, b in moved)
    return new_obs, new_archive, [oid for oid, _ in moved]


def main():
    ap = argparse.ArgumentParser(description="Verschiebt aufgelöste OBS mechanisch ins Archiv.")
    ap.add_argument("--file", help="Pfad zu observations.md (Default: Repo-Standard)")
    ap.add_argument("--archive", help="Pfad zum Archiv (Default: Repo-Standard)")
    ap.add_argument("--dry-run", action="store_true", help="nur anzeigen, was verschoben würde")
    args = ap.parse_args()
    root = repo_root()
    obs = Path(args.file) if args.file else root / OBS_FILE
    arch = Path(args.archive) if args.archive else root / ARCHIVE_FILE
    if not obs.is_file() or not arch.is_file():
        print(f"FEHLER: {obs} oder {arch} nicht gefunden.", file=sys.stderr)
        return 1
    new_obs, new_archive, moved = archive_resolved(
        obs.read_text(encoding="utf-8"), arch.read_text(encoding="utf-8"))
    if not moved:
        print("Nichts zu archivieren (keine aufgelösten Einträge in der Live-Datei).")
        return 0
    if args.dry_run:
        print("Würde verschieben: " + ", ".join(moved))
        return 0
    obs.write_text(new_obs, encoding="utf-8")
    arch.write_text(new_archive, encoding="utf-8")
    print(f"Ins Archiv verschoben ({len(moved)}): " + ", ".join(moved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
