#!/usr/bin/env python3
"""
decisions.py – CLI-Tool zur Verwaltung von Architecture Decision Records in docs/history/adr.md
"""

import argparse
import re
import sys
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def find_repo_root() -> Path:
    """Find the repository root by looking for CLAUDE.md or .git."""
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / "CLAUDE.md").exists():
            return parent
    # Fallback to cwd
    return Path.cwd()


REPO_ROOT = find_repo_root()
ADR_FILE = REPO_ROOT / "docs" / "history" / "adr.md"

CODE_DIRS = [
    REPO_ROOT / "Server",
    REPO_ROOT / "Client" / "src",
]
CODE_EXTENSIONS = {".cs", ".ts", ".tsx"}

# Regex to match ADR reference comments in code: // ADR-SXXX-N or // ADR-SXXX-N-DEP etc.
CODE_REF_RE = re.compile(r"//\s*(ADR-S\d{3}-\d+(?:-(?:DEP|SUP))?)")

# Regex to parse ADR entry headers
ENTRY_HEADER_RE = re.compile(r"^### (ADR-S\d{3}-\d+(?:-(?:DEP|SUP))?): (.+)$")
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(.+)$")
TAGS_RE = re.compile(r"^\*\*Tags:\*\*\s*(.+)$")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def load_adr_file() -> str:
    if not ADR_FILE.exists():
        print(f"Fehler: {ADR_FILE} nicht gefunden.", file=sys.stderr)
        sys.exit(1)
    return ADR_FILE.read_text(encoding="utf-8")


def parse_entries(text: str) -> list[dict]:
    """Parse all ADR entries from the markdown text.

    Returns a list of dicts with keys:
      id, title, status, tags (list[str]), body (full markdown block)
    """
    entries = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = ENTRY_HEADER_RE.match(lines[i])
        if m:
            adr_id = m.group(1)
            title = m.group(2)
            status = None
            tags = []
            body_lines = [lines[i]]
            i += 1
            # Read until next ### heading or end-of-file separator "---" followed by empty
            while i < len(lines):
                line = lines[i]
                # Check for new entry header (stop)
                if ENTRY_HEADER_RE.match(line):
                    break
                body_lines.append(line)
                sm = STATUS_RE.match(line)
                if sm:
                    status = sm.group(1).strip()
                tm = TAGS_RE.match(line)
                if tm:
                    raw_tags = tm.group(1).strip()
                    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
                i += 1
            # Trim trailing blank lines / separators from body
            while body_lines and body_lines[-1].strip() in ("", "---"):
                body_lines.pop()
            entries.append({
                "id": adr_id,
                "title": title,
                "status": status or "Unknown",
                "tags": tags,
                "body": "\n".join(body_lines),
            })
        else:
            i += 1
    return entries


def base_id(adr_id: str) -> str:
    """Return the base ID without -DEP/-SUP suffix."""
    return re.sub(r"-(?:DEP|SUP)$", "", adr_id)


def normalize_id(raw: str) -> str:
    """Accept S041-1 or ADR-S041-1 (case-insensitive prefix)."""
    raw = raw.strip()
    if not raw.upper().startswith("ADR-"):
        raw = "ADR-" + raw
    return raw.upper()


def find_entry(entries: list[dict], query_id: str) -> dict | None:
    """Find entry by base ID (with or without -DEP/-SUP suffix)."""
    norm = normalize_id(query_id)
    norm_base = base_id(norm)
    # Exact match first
    for e in entries:
        if e["id"].upper() == norm or e["id"].upper() == norm_base:
            return e
    # Suffix variants
    for e in entries:
        if base_id(e["id"].upper()) == norm_base:
            return e
    return None


# ---------------------------------------------------------------------------
# Tag filtering helpers
# ---------------------------------------------------------------------------

def tag_matches(tag: str, filter_tag: str) -> bool:
    """
    filter_tag can be:
      - "scope:cross-cutting" → exact match
      - "http:"               → category prefix match (ends with ":")
    """
    if filter_tag.endswith(":"):
        # Category prefix match
        category = filter_tag[:-1]
        return tag.startswith(category + ":")
    return tag == filter_tag


def entry_matches_tags(entry: dict, filter_tags: list[str]) -> bool:
    for ft in filter_tags:
        if not any(tag_matches(t, ft) for t in entry["tags"]):
            return False
    return True


# ---------------------------------------------------------------------------
# Subcommand: list
# ---------------------------------------------------------------------------

def cmd_list(args):
    text = load_adr_file()
    entries = parse_entries(text)

    # Status filter
    if args.status == "all":
        filtered = entries
    else:
        filtered = [e for e in entries if e["status"] == "Accepted"]

    # Tag filters
    if args.tag:
        filtered = [e for e in filtered if entry_matches_tags(e, args.tag)]

    if not filtered:
        print("Keine Einträge gefunden.")
        return

    if args.full:
        for e in filtered:
            print(e["body"])
            print("\n---\n")
        return

    # Compact format
    for e in filtered:
        status_label = e["status"]
        # Build short category list from tags
        categories = sorted({t.split(":")[0] for t in e["tags"] if ":" in t})
        cat_str = ", ".join(categories) if categories else ""
        print(f"[{status_label}][{cat_str}] {e['id']}  {e['title']}")
        if e["tags"]:
            print(f"{'':27}tags: {', '.join(e['tags'])}")


# ---------------------------------------------------------------------------
# Subcommand: get
# ---------------------------------------------------------------------------

def cmd_get(args):
    text = load_adr_file()
    entries = parse_entries(text)

    exit_code = 0
    for raw_id in args.ids:
        entry = find_entry(entries, raw_id)
        if entry is None:
            print(f"Fehler: ADR '{raw_id}' nicht gefunden.", file=sys.stderr)
            exit_code = 1
            continue
        if entry["status"] != "Accepted":
            print(f"⚠ {base_id(entry['id'])} ist {entry['status']} – prüfen ob diese Entscheidung noch gilt.")
        print(entry["body"])
        print()

    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Subcommand: check
# ---------------------------------------------------------------------------

def find_code_refs() -> list[tuple[str, int, str]]:
    """Return list of (filepath, lineno, adr_id) for all ADR refs in code."""
    refs = []
    for code_dir in CODE_DIRS:
        if not code_dir.exists():
            continue
        for path in code_dir.rglob("*"):
            if path.suffix not in CODE_EXTENSIONS:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(content.splitlines(), 1):
                for m in CODE_REF_RE.finditer(line):
                    refs.append((str(path.relative_to(REPO_ROOT)), lineno, m.group(1)))
    return refs


def cmd_check(args):
    text = load_adr_file()
    entries = parse_entries(text)

    refs = find_code_refs()

    if not refs:
        print("Keine ADR-Referenzen im Code gefunden.")
        sys.exit(0)

    exit_code = 0
    col_width = max(len(f"{r[0]}:{r[1]}") for r in refs) + 2

    for filepath, lineno, adr_id in refs:
        loc = f"{filepath}:{lineno}"
        entry = find_entry(entries, adr_id)
        if entry is None:
            print(f"{loc:<{col_width}} {adr_id:<15} ✗ nicht gefunden")
            exit_code = 1
        elif entry["status"] == "Accepted":
            print(f"{loc:<{col_width}} {adr_id:<15} ✓ Accepted")
        else:
            print(f"{loc:<{col_width}} {adr_id:<15} ⚠ {entry['status']}")

    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Subcommand: tags
# ---------------------------------------------------------------------------

def cmd_tags(args):
    text = load_adr_file()
    entries = parse_entries(text)

    # Build: { category: { tag_value: count } }
    from collections import defaultdict
    categories: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for e in entries:
        for tag in e["tags"]:
            if ":" in tag:
                cat, val = tag.split(":", 1)
                categories[cat][val] += 1
            else:
                categories["(other)"][tag] += 1

    target_cats = sorted(categories.keys())
    if args.category:
        if args.category not in categories:
            print(f"Kategorie '{args.category}' nicht gefunden.")
            sys.exit(0)
        target_cats = [args.category]

    for cat in target_cats:
        tag_dict = categories[cat]
        n_tags = len(tag_dict)
        print(f"{cat}: ({n_tags} Tag{'s' if n_tags != 1 else ''})")
        for val, count in sorted(tag_dict.items()):
            adr_word = "ADRs" if count != 1 else "ADR"
            print(f"  {val:<30} {count} {adr_word}")
        print()


# ---------------------------------------------------------------------------
# Subcommand: refs
# ---------------------------------------------------------------------------

def cmd_refs(args):
    text = load_adr_file()
    entries = parse_entries(text)

    all_refs = find_code_refs()

    # Filter by requested IDs
    if args.ids:
        normalized_ids = {base_id(normalize_id(i)) for i in args.ids}
        filtered_refs = [
            (fp, ln, aid) for fp, ln, aid in all_refs
            if base_id(normalize_id(aid)) in normalized_ids
        ]
        # Also show entries with no refs when specific IDs are requested
        ref_ids = {base_id(normalize_id(aid)) for _, _, aid in filtered_refs}
        missing = normalized_ids - ref_ids
    else:
        filtered_refs = all_refs
        missing = set()

    # Group by ADR ID (base form)
    from collections import defaultdict
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for fp, ln, aid in filtered_refs:
        grouped[base_id(normalize_id(aid))].append((fp, ln))

    # Add missing (no refs found) requested IDs
    for mid in missing:
        if mid not in grouped:
            grouped[mid] = []

    if not grouped and not missing:
        print("Keine ADR-Referenzen gefunden.")
        return

    for adr_id in sorted(grouped.keys()):
        entry = find_entry(entries, adr_id)
        title = entry["title"] if entry else "unbekannt"
        print(f"{adr_id} ({title}):")
        locs = grouped[adr_id]
        if locs:
            for fp, ln in sorted(locs, key=lambda x: (x[0], x[1])):
                print(f"  {fp}:{ln}")
        else:
            print("  (keine Referenzen)")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="decisions.py",
        description="CLI-Tool zur Verwaltung von Architecture Decision Records (docs/history/adr.md)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- list ---
    p_list = subparsers.add_parser(
        "list",
        help="Listet ADR-Entries (Standard: aktive Entries, kompakt)",
    )
    p_list.add_argument(
        "--tag",
        action="append",
        metavar="TAG",
        help='Filtert nach Tag. Exakt ("scope:cross-cutting") oder Kategorie ("http:"). Mehrfach verwendbar.',
    )
    p_list.add_argument(
        "--status",
        default="active",
        choices=["active", "all"],
        help='"active" (Standard): nur Accepted. "all": auch Deprecated/Superseded.',
    )
    p_list.add_argument(
        "--full",
        action="store_true",
        help="Vollständigen Markdown-Text aller gefundenen Entries ausgeben.",
    )
    p_list.set_defaults(func=cmd_list)

    # --- get ---
    p_get = subparsers.add_parser(
        "get",
        help="Gibt den vollständigen Text eines oder mehrerer Entries aus.",
    )
    p_get.add_argument(
        "ids",
        nargs="+",
        metavar="ID",
        help="ADR-ID(s), z.B. S041-1 oder ADR-S041-1.",
    )
    p_get.set_defaults(func=cmd_get)

    # --- check ---
    p_check = subparsers.add_parser(
        "check",
        help="Prüft alle ADR-Referenzkommentare im Code gegen adr.md.",
    )
    p_check.set_defaults(func=cmd_check)

    # --- tags ---
    p_tags = subparsers.add_parser(
        "tags",
        help="Listet alle verwendeten Tags, gruppiert nach Kategorie.",
    )
    p_tags.add_argument(
        "--category",
        metavar="CATEGORY",
        help="Nur diese Kategorie anzeigen.",
    )
    p_tags.set_defaults(func=cmd_tags)

    # --- refs ---
    p_refs = subparsers.add_parser(
        "refs",
        help="Sucht Code-Referenzen für ADR-IDs.",
    )
    p_refs.add_argument(
        "ids",
        nargs="*",
        metavar="ID",
        help="ADR-ID(s). Ohne Angabe: alle Referenzen.",
    )
    p_refs.set_defaults(func=cmd_refs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
