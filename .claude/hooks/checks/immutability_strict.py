"""Immutability-Strict-Check (blockierend): class ohne record, public set;"""
import re
from .common import HookInput, IMMUTABILITY_EXCLUDED

CLASS_WITHOUT_RECORD = re.compile(r'(?<!\brecord\s)\bclass\s+\w+')
# `static class` sind keine Domain-Entities (z.B. Endpoint-Registrierungs-Klassen in Server/Endpoints/)
STATIC_CLASS_LINE = re.compile(r'\bstatic\s+class\b')
# Matcht `set;` das NICHT durch private/protected/internal eingeschränkt ist.
# In C# schreibt man { get; set; } ohne explizites `public` – trotzdem öffentlich.
# Erlaubt: private set; | protected set; | internal set; | protected internal set;
_RESTRICTED_SETTER = re.compile(r'\b(?:private|protected|internal)\s+(?:set|init)\s*;')
PUBLIC_SETTER = re.compile(r'\bset\s*;')

def check(inp: HookInput) -> list[str]:
    if not inp.is_cs:
        return []
    if IMMUTABILITY_EXCLUDED.search(inp.file_path):
        return []

    violations = []

    content_without_static_classes = "\n".join(
        line for line in inp.new_content.splitlines()
        if not STATIC_CLASS_LINE.search(line)
    )
    if CLASS_WITHOUT_RECORD.search(content_without_static_classes):
        violations.append(
            "⛔ `class` ohne `record` in Domain-Code erkannt.\n"
            "  EF-Entities → `class` nur in `Server/Data/DatabaseTypes/`.\n"
            "  DTOs        → `record` mit `init;`.\n"
            "  Value Objects → `readonly record struct`."
        )

    # Zeilen mit eingeschränktem Setter (private/protected/internal) ignorieren
    lines_without_restricted = "\n".join(
        line for line in inp.new_content.splitlines()
        if not _RESTRICTED_SETTER.search(line)
    )
    if PUBLIC_SETTER.search(lines_without_restricted):
        violations.append(
            "⛔ `public set;` in Domain-Code erkannt.\n"
            "  Verwende `init;` (DTOs/records) oder `get;` mit Konstruktor-Zuweisung (Value Objects).\n"
            "  `private set;` ist nur in EF-Entities (`DatabaseTypes/`) erlaubt."
        )

    if violations:
        return [
            "Immutability-Verletzung (blockierend):\n"
            + "\n".join(violations)
            + "\nSiehe CODING_GUIDELINE_CSHARP.md (Abschnitt 1)."
        ]
    return []
