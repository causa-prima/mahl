#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): Referenz-Richtung volatil → stabil (OBS-S095-3).

Setzt das principles.md-Prinzip „Referenzen laufen von volatil → stabil, nie umgekehrt"
syntaktisch durch: Eine **stabile** Datei darf kein **volatiles** ID-Schema
(`OBS-`/`OQ-`/`LL-`/`TD-S…`) referenzieren – solche IDs verschwinden beim Erledigen/Archivieren
und lassen den Verweis dangeln. `ADR-S…` ist stabil und daher erlaubt.

Datei-Scope (default-protected + explizite Ausnahmen, robust gegen neue Dateien):
- **Geschützt:** alles unter `docs/`, `.claude/skills/`, `.claude/agents/` + Root-`AGENTS.md`.
- **Ausgenommen** (selbst volatil oder verwalten das ID-System): die kaizen-Bookkeeping-Dateien
  (`observations`/`countermeasures`/`lessons_learned`/`process`.md), `docs/kaizen/archive/**`,
  die volatilen Tracker (`tech-debt`/`open-questions`/`AGENT_MEMORY`.md)
  und `.claude/skills/kaizen/**`.
- **Zeilen-Ausnahme:** eine Zeile mit `ref-ok`-Marker wird ignoriert (bewusste Einzelfälle).

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import re
from pathlib import Path

from ._hook_io import edit_zustand

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Geschützte Wurzeln (relativer POSIX-Pfad-Präfix) + einzelne geschützte Dateien.
_PROTECTED_ROOTS = ("docs/", ".claude/skills/", ".claude/agents/")
_PROTECTED_FILES = ("AGENTS.md",)

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
_EXEMPT_PREFIXES = ("docs/kaizen/archive/", ".claude/skills/kaizen/")

# Volatiles ID-Schema: OBS-/OQ-/LL-/TD- gefolgt von S<Session>[-<n>]. ADR- ist bewusst NICHT dabei (stabil).
_VOLATILE_RE = re.compile(r"\b(?:OBS|OQ|LL|TD)-S\d{2,3}(?:-\d+)?\b")
_REF_OK = "ref-ok"

_KOPF = "❌ Referenz-Richtung (Poka-Yoke): stabile Datei referenziert volatile ID(s):\n"
_HINWEIS = (
    "  Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt“ (principles.md): volatile IDs "
    "(OBS-/OQ-/LL-/TD-) verschwinden beim Erledigen/Archivieren → der Verweis dangelt. "
    "Nötige Info hier inlinen oder nur auf stabile Artefakte (ADR/Guideline) verweisen. "
    "Bewusster Einzelfall → `ref-ok`-Marker in die Zeile."
)


def _rel_path(file_path: str) -> str | None:
    """Repo-relativer POSIX-Pfad; None wenn außerhalb des Repos (oder unauflösbar)."""
    try:
        return Path(file_path).resolve().relative_to(_REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return None


def is_protected(file_path: str) -> bool:
    """True, wenn die Datei stabil ist (geschützt) und nicht explizit ausgenommen."""
    # Relative Pfade (auch mit `\`) bleiben wie sie sind; das Auflösen ergäbe dasselbe.
    rel = _rel_path(file_path) if file_path.startswith("/") else file_path
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


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    zustand = edit_zustand(data, is_protected)
    if zustand is None:
        return None
    _file_path, _pre, post = zustand

    refs = find_volatile_refs(post)
    if not refs:
        return None

    lines = "\n".join(f"  - Zeile {lineno}: {ident}" for lineno, ident in refs)
    return f"{_KOPF}{lines}\n{_HINWEIS}"
