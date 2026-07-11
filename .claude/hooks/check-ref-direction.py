#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): Referenz-Richtung volatil → stabil (OBS-S095-3).

Setzt das principles.md-Prinzip „Referenzen laufen von volatil → stabil, nie umgekehrt"
syntaktisch durch: Eine **stabile** Datei darf kein **volatiles** ID-Schema
(`OBS-`/`OQ-`/`LL-`/`TD-S…`) referenzieren – solche IDs verschwinden beim Erledigen/Archivieren
und lassen den Verweis dangeln. `ADR-S…` ist stabil und daher erlaubt.

Datei-Scope (default-protected + explizite Ausnahmen, robust gegen neue Dateien):
- **Geschützt:** alles unter `docs/`, `.claude/skills/`, `.claude/agents/` + Root-`CLAUDE.md`.
- **Ausgenommen** (selbst volatil oder verwalten das ID-System): die kaizen-Bookkeeping-Dateien
  (`observations`/`countermeasures`/`lessons_learned`/`process`.md), `docs/kaizen/archive/**`,
  die volatilen Tracker (`tech-debt`/`open-questions`/`AGENT_MEMORY`.md),
  `docs/history/sessions/**` (read-only Logs) und `.claude/skills/kaizen/**`.
- **Zeilen-Ausnahme:** eine Zeile mit `ref-ok`-Marker wird ignoriert (bewusste Einzelfälle).

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Geschützte Wurzeln (relativer POSIX-Pfad-Präfix) + einzelne geschützte Dateien.
_PROTECTED_ROOTS = ("docs/", ".claude/skills/", ".claude/agents/")
_PROTECTED_FILES = ("CLAUDE.md",)

# Ausnahmen: ganze Dateien bzw. Präfixe, die volatile IDs tragen dürfen.
_EXEMPT_FILES = frozenset({
    "docs/kaizen/observations.md",
    "docs/kaizen/countermeasures.md",
    "docs/kaizen/lessons_learned.md",
    "docs/kaizen/process.md",
    "docs/tech-debt.md",
    "docs/open-questions.md",
    "docs/AGENT_MEMORY.md",
})
_EXEMPT_PREFIXES = ("docs/kaizen/archive/", "docs/history/sessions/", ".claude/skills/kaizen/")

# Volatiles ID-Schema: OBS-/OQ-/LL-/TD- gefolgt von S<Session>[-<n>]. ADR- ist bewusst NICHT dabei (stabil).
_VOLATILE_RE = re.compile(r"\b(?:OBS|OQ|LL|TD)-S\d{2,3}(?:-\d+)?\b")
_REF_OK = "ref-ok"


def _rel_path(file_path: str) -> str | None:
    """Repo-relativer POSIX-Pfad; None wenn außerhalb des Repos (oder unauflösbar)."""
    try:
        return Path(file_path).resolve().relative_to(_REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return None


def is_protected(file_path: str) -> bool:
    """True, wenn die Datei stabil ist (geschützt) und nicht explizit ausgenommen."""
    rel = _rel_path(file_path) if (file_path.startswith("/") or "\\" in file_path) else file_path
    if rel is None:
        return False
    rel = rel.replace("\\", "/")
    if rel in _EXEMPT_FILES or rel.startswith(_EXEMPT_PREFIXES):
        return False
    if rel in _PROTECTED_FILES:
        return True
    return rel.startswith(_PROTECTED_ROOTS)


def find_volatile_refs(content: str) -> list[tuple[int, str]]:
    """(Zeilennummer, ID)-Paare für volatile Referenzen; Zeilen mit `ref-ok` bleiben außen vor."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        if _REF_OK in line:
            continue
        for match in _VOLATILE_RE.finditer(line):
            hits.append((lineno, match.group(0)))
    return hits


def compute_post_content(tool: str, file_path: str, tool_input: dict) -> str | None:
    """Simuliert den Datei-Inhalt nach Anwendung des Edits/Writes."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        path = Path(file_path)
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if old and old in current:
            if tool_input.get("replace_all"):
                return current.replace(old, new)
            return current.replace(old, new, 1)
        return current  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
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
        if tool not in ("Edit", "Write") or not file_path:
            sys.exit(0)
        if not is_protected(file_path):
            sys.exit(0)

        post = compute_post_content(tool, file_path, tool_input)
        if post is None:
            sys.exit(0)

        refs = find_volatile_refs(post)
        if refs:
            print("❌ Referenz-Richtung (Poka-Yoke): stabile Datei referenziert volatile ID(s):", file=sys.stderr)
            for lineno, ident in refs:
                print(f"  - Zeile {lineno}: {ident}", file=sys.stderr)
            print(
                "  Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt“ (principles.md): volatile IDs "
                "(OBS-/OQ-/LL-/TD-) verschwinden beim Erledigen/Archivieren → der Verweis dangelt. "
                "Nötige Info hier inlinen oder nur auf stabile Artefakte (ADR/Guideline) verweisen. "
                "Bewusster Einzelfall → `ref-ok`-Marker in die Zeile.",
                file=sys.stderr,
            )
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-ref-direction: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
