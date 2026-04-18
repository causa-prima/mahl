"""Immutability-Check (blockierend): Mutable Collections in Domain-Code.

Ergänzt Meziantou MA0016 (erzwingt Interface-Typen): dieser Check erzwingt zusätzlich
die stärkere Anforderung von ImmutableList<T>/IImmutableSet<T> statt nur IList<T>.
"""
import re
from .common import HookInput, IMMUTABILITY_EXCLUDED

MUTABLE_COLLECTION = re.compile(
    r'\b(?:List|Dictionary|HashSet|Queue|Stack|SortedSet|SortedDictionary|Collection|ObservableCollection)\s*<'
)
LOCAL_NEW = re.compile(
    r'\bnew\s+(?:List|Dictionary|HashSet|Queue|Stack|SortedSet|SortedDictionary|Collection|ObservableCollection)\s*[<(]'
)


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs:
        return []
    if IMMUTABILITY_EXCLUDED.search(inp.file_path):
        return []

    mutable_lines = [
        line.strip() for line in inp.new_content.splitlines()
        if MUTABLE_COLLECTION.search(line) and not LOCAL_NEW.search(line)
    ]
    if not mutable_lines:
        return []

    examples = "\n    ".join(mutable_lines[:3])
    return [
        "⛔ Immutability-Verletzung (blockierend): Mutable Collection-Typ in Property/Parameter erkannt:\n"
        f"    {examples}\n"
        "  Verwende unveränderliche Strukturen:\n"
        "    List<T>         → ImmutableList<T> oder IEnumerable<T>\n"
        "    Dictionary<K,V> → ImmutableDictionary<K,V>\n"
        "    HashSet<T>      → ImmutableHashSet<T>\n"
        "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 1)."
    ]
