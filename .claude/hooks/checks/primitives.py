"""
Primitive-Obsession-Check: Nackte Built-in-Typen in Domain-Code.

check_blocking: Properties mit nackten Primitives – blockierend (fast immer falsch).
check_nonblocking: Parameter mit nackten Primitives – Hinweis (Factory-Methods dürfen Primitives nehmen).
"""
import re
from .common import HookInput

PRIMITIVE_TYPES = r'(?:string|int|long|double|float|decimal|bool|Guid|uint|short|byte)'
PROPERTY_PATTERN = re.compile(rf'\bpublic\s+{PRIMITIVE_TYPES}\??\s+\w+\s*\{{\s*get\s*[;{{]')
PARAM_PATTERN = re.compile(rf'(?:[\(,]\s*){PRIMITIVE_TYPES}\??\s+\w+')

# Zeilen mit Endpoint-Mapping-Methoden enthalten primitive Typen als Route-Parameter (Pflicht)
ENDPOINT_MAPPING_LINE = re.compile(r'\.Map(?:Get|Post|Put|Delete|Patch|Methods)\b')

# Zeilen mit Error<string> als Rückgabetyp (Factory-Methods dürfen string-Parameter haben)
ERROR_STRING_LINE = re.compile(r'Error<string>')

# Explizite Test-Projekt-Pfade (zusätzlich zu is_test aus common.py)
TEST_PROJECT_PATHS = re.compile(
    r'[/\\](?:mahl\.Server\.Tests|mahl\.Shared\.Test|mahl\.Tests\.Shared)[/\\]'
)


def _filter_lines(content: str, line_filter: re.Pattern) -> str:
    return "\n".join(line for line in content.splitlines() if not line_filter.search(line))


def _is_excluded(inp: HookInput) -> bool:
    return not inp.is_cs or inp.is_domain_excluded or inp.is_test or bool(TEST_PROJECT_PATHS.search(inp.file_path))


def check_blocking(inp: HookInput) -> list[str]:
    """Properties mit nackten Primitives – blockierend."""
    if _is_excluded(inp):
        return []

    content = _filter_lines(inp.new_content, ENDPOINT_MAPPING_LINE)
    content = _filter_lines(content, ERROR_STRING_LINE)

    if not PROPERTY_PATTERN.findall(content):
        return []

    return [
        "⛔ Primitive-Obsession-Verletzung (blockierend): Nackte Built-in-Typen als Property in Domain-Code erkannt.\n"
        "Kapsle sie in Value Objects (z.B. `RecipeName`, `IngredientId`).\n"
        "Ausnahmen: DTOs (`Shared/Dtos/`), EF-Entities (`DatabaseTypes/`), Tests.\n"
        "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 2)."
    ]


def check_nonblocking(inp: HookInput) -> list[str]:
    """Parameter mit nackten Primitives – Hinweis (Factory-Methods dürfen Primitives nehmen)."""
    if _is_excluded(inp):
        return []

    content = _filter_lines(inp.new_content, ENDPOINT_MAPPING_LINE)
    content = _filter_lines(content, ERROR_STRING_LINE)

    if not PARAM_PATTERN.findall(content):
        return []

    return [
        "⚠ Primitive-Obsession-Hinweis: Nackte Built-in-Typen als Parameter in Domain-Code erkannt.\n"
        "Prüfe ob Value Objects (z.B. `RecipeName`, `IngredientId`) passender wären.\n"
        "Ausnahme: Factory-Methods und Value Objects nehmen bewusst Primitives als Input.\n"
        "Ausnahmen: DTOs (`Shared/Dtos/`), EF-Entities (`DatabaseTypes/`), Tests.\n"
        "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 2)."
    ]
