"""
Primitive-Obsession-Check: Nackte Built-in-Typen in Domain-Code.

check_blocking: Properties mit nackten Primitives – blockierend (fast immer falsch).
             Dazu Parameter mit nackten Primitives, aber **nur in Entities** (s.u.).
check_nonblocking: Parameter mit nackten Primitives außerhalb von Entities – Hinweis.

Warum die Unterscheidung (Drei-Ebenen-Regel, `coding-guideline-csharp.md` §2): In
`Server/Domain/` liegen zwei Ebenen mit gegensätzlicher Regel.

  - **Constraint-/Domänentyp** (`NonEmptyTrimmedString`, `IngredientName`): `Create()` nimmt
    Primitives – das *ist* die Validierungsebene. Ein Blocken wäre hier schlicht falsch.
  - **Entity** (`Ingredient`): `Create()` nimmt ausschließlich Domänentypen. Ein rohes
    `Guid`/`string` ist die Verletzung, die dieser Check fangen soll.

Mechanisch getrennt an der `Value`-Property: Ein Typ, der seinen gekapselten Wert über
`public <primitive> Value` freigibt, ist die Kapselung selbst und darf Primitives annehmen.
Fehlt sie, ist der Typ ein Aggregat aus anderen Typen – dort ist ein Primitive ein Leck.
Der Bestand belegt die Trennschärfe: `NonEmptyTrimmedString` hat `Value`, `Ingredient` nicht.
"""
import re
from pathlib import Path

from .common import HookInput

PRIMITIVE_TYPES = r'(?:string|int|long|double|float|decimal|bool|Guid|uint|short|byte)'
# Beide Property-Formen: `{ get; … }` und expression-bodied `=>`. Die zweite fehlte bis S119 –
# Domain-Typen nutzen durchweg `=>`, der Check lief dort faktisch ins Leere.
PROPERTY_PATTERN = re.compile(
    rf'\bpublic\s+{PRIMITIVE_TYPES}\??\s+\w+\s*(?:\{{\s*get\s*[;{{]|=>)')
PARAM_PATTERN = re.compile(rf'(?:[\(,]\s*){PRIMITIVE_TYPES}\??\s+\w+')

# Ein Typ mit dieser Property kapselt einen Primitive und darf ihn deshalb annehmen.
VALUE_PROPERTY = re.compile(rf'\bpublic\s+{PRIMITIVE_TYPES}\??\s+Value\s*(?:\{{\s*get\s*[;{{]|=>)')

# Sum-Types (ADR-S018-1) sind eine dritte Kategorie, die die Drei-Ebenen-Regel nicht abbildet:
# weder Aggregat noch Wert-Kapselung. Ihre Value-Träger-Subtypen führen den Payload bewusst als
# Primitive (`NameDuplicateCase(string EnteredName)`), und die `Match<T>`-Signatur nimmt ihn als
# Callback-Parameter entgegen. Ohne diese Ausnahme sperrt der Check `IngredientValidationError.cs`
# vollständig – verifiziert, nicht vermutet.
SUM_TYPE = re.compile(r'\babstract\s+record\b|\bpublic\s+T\s+Match<T>')

# In `Server/Domain/` liegen Entities und Domänentypen; `Server/Types/` nur Constraint-Typen.
ENTITY_PATH = re.compile(r'[/\\]Domain[/\\]')

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


def _relevant_content(inp: HookInput) -> str:
    content = _filter_lines(inp.new_content, ENDPOINT_MAPPING_LINE)
    return _filter_lines(content, ERROR_STRING_LINE)


def _file_text(file_path: str) -> str:
    """Bestehender Datei-Inhalt; "" wenn die Datei (noch) nicht existiert oder unlesbar ist."""
    try:
        path = Path(file_path)
        return path.read_text(encoding="utf-8") if path.is_file() else ""
    except OSError:
        return ""


def _in_fragment_or_file(pattern: re.Pattern, content: str, file_path: str) -> bool:
    """Trifft das Muster im Edit-Fragment **oder** in der Gesamtdatei?

    Bei `Edit` enthält `new_content` nur den geänderten Ausschnitt. Wer in `IngredientName.cs`
    allein die `Create`-Zeile anfasst, hätte die `Value`-Property sonst nicht im Blickfeld – und
    der Typ würde fälschlich als Entity behandelt. Das Fragment zählt mit, damit auch der Fall
    trägt, in dem das Merkmal gerade erst hinzugefügt wird.
    """
    return bool(pattern.search(content) or pattern.search(_file_text(file_path)))


def is_value_wrapper(content: str, file_path: str = "") -> bool:
    """True für Constraint-/Domänentypen – sie kapseln einen Primitive und dürfen ihn annehmen."""
    return _in_fragment_or_file(VALUE_PROPERTY, content, file_path)


def is_sum_type(content: str, file_path: str = "") -> bool:
    """True für Sum-Types nach ADR-S018-1 – ihre Payload-Subtypen tragen Primitives bewusst."""
    return _in_fragment_or_file(SUM_TYPE, content, file_path)


def is_entity(inp: HookInput, content: str) -> bool:
    """True für Aggregate in `Server/Domain/` – weder Wert-Kapselung noch Sum-Type (§2)."""
    if not ENTITY_PATH.search(inp.file_path):
        return False
    return not is_value_wrapper(content, inp.file_path) and not is_sum_type(content, inp.file_path)


def check_blocking(inp: HookInput) -> list[str]:
    """Nackte Primitives als Property – und als Parameter, sofern der Typ eine Entity ist."""
    if _is_excluded(inp):
        return []

    content = _relevant_content(inp)
    reasons = []

    # Die `Value`-Property eines Constraint-/Domänentyps IST der gekapselte Primitive –
    # sie ist die Schnittstelle nach außen, nicht das Leck. Sum-Types ebenso (ADR-S018-1).
    # Beide Prüfungen sehen Fragment UND Datei; die Rolle des Typs steht nicht im Ausschnitt.
    if (PROPERTY_PATTERN.findall(content)
            and not is_value_wrapper(content, inp.file_path)
            and not is_sum_type(content, inp.file_path)):
        reasons.append(
            "⛔ Primitive-Obsession-Verletzung (blockierend): Nackte Built-in-Typen als Property in Domain-Code erkannt.\n"
            "Kapsle sie in Domänentypen (z.B. `RecipeName`, `IngredientId`).\n"
            "Ausnahme: die `Value`-Property eines Constraint-/Domänentyps – sie gibt den gekapselten Wert frei.\n"
            "Ausnahmen: DTOs (`Shared/Dtos/`), EF-Entities (`DatabaseTypes/`), Tests.\n"
            "Siehe docs/guidelines/coding-guideline-csharp.md §2 (Drei-Ebenen-Regel)."
        )

    if PARAM_PATTERN.findall(content) and is_entity(inp, content):
        reasons.append(
            "⛔ Primitive-Obsession-Verletzung (blockierend): Nacktes Built-in als Parameter in einer Entity.\n"
            "Eine Entity nimmt ausschließlich Domänentypen – `Create(Guid id, …)` ist die Verletzung,\n"
            "`Create(IngredientId id, IngredientName name, …)` die Sollform.\n"
            "Constraint-/Domänentypen (erkennbar an `public <primitive> Value`) dürfen Primitives nehmen –\n"
            "sie SIND die Validierungsebene.\n"
            "Siehe docs/guidelines/coding-guideline-csharp.md §2 (Drei-Ebenen-Regel)."
        )

    return reasons


def check_nonblocking(inp: HookInput) -> list[str]:
    """Parameter mit nackten Primitives außerhalb von Entities – Hinweis."""
    if _is_excluded(inp):
        return []

    content = _relevant_content(inp)
    if not PARAM_PATTERN.findall(content):
        return []
    # In einer Entity ist das blockierend (s.o.) – sonst doppelte Meldung für denselben Fund.
    if is_entity(inp, content):
        return []
    # Ein Constraint-/Domänentyp und ein Sum-Type nehmen Primitives per Konstruktion entgegen.
    # Ohne diese Ausnahme feuerte der Hinweis bei JEDEM guideline-konformen `Create(string)` –
    # ein Signal, das bei korrektem Code immer anspringt, wird gelesen wie keines.
    if is_value_wrapper(content, inp.file_path) or is_sum_type(content, inp.file_path):
        return []

    return [
        "⚠ Primitive-Obsession-Hinweis: Nackte Built-in-Typen als Parameter in Domain-Code erkannt.\n"
        "Prüfe ob Domänentypen (z.B. `RecipeName`, `IngredientId`) passender wären.\n"
        "Ausnahme: Constraint-/Domänentypen nehmen bewusst Primitives als Input – sie validieren sie.\n"
        "Ausnahmen: DTOs (`Shared/Dtos/`), EF-Entities (`DatabaseTypes/`), Tests.\n"
        "Siehe docs/guidelines/coding-guideline-csharp.md §2 (Drei-Ebenen-Regel)."
    ]
