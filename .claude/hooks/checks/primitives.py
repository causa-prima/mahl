"""Primitive-Obsession-Check: Nackte Built-in-Typen in Domain-Code."""
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
    """Entfernt alle Zeilen, auf die der Filter zutrifft."""
    return "\n".join(line for line in content.splitlines() if not line_filter.search(line))


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs:
        return []
    if inp.is_domain_excluded or inp.is_test:
        return []
    if TEST_PROJECT_PATHS.search(inp.file_path):
        return []

    new = _filter_lines(inp.new_content, ENDPOINT_MAPPING_LINE)
    new = _filter_lines(new, ERROR_STRING_LINE)
    prop_matches = PROPERTY_PATTERN.findall(new)
    param_matches = PARAM_PATTERN.findall(new)

    hits = []
    if prop_matches:
        hits.append(f"  Properties: {len(prop_matches)} Treffer")
    if param_matches:
        hits.append(f"  Parameter:  {len(param_matches)} Treffer")

    if hits:
        return [
            "Primitive-Obsession-Hinweis: Nackte Built-in-Typen in Domain-Code erkannt.\n"
            + "\n".join(hits) + "\n"
            "Kapsle sie in Value Objects (z.B. `RecipeName`, `IngredientId`).\n"
            "Ausnahmen: DTOs (`Shared/Dtos/`), EF-Entities (`DatabaseTypes/`), Tests.\n"
            "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 2)."
        ]
    return []
