"""Constructor-Check: Nicht-private Konstruktoren in Domain-Code."""
import re
from .common import HookInput

NON_PRIVATE_CTOR = re.compile(r'\b(?:public|internal|protected)\s+\w+\s*\(')
CLASS_DECL = re.compile(
    r'\b(?:public|internal|protected)\s+(?:abstract\s+|sealed\s+|static\s+)?'
    r'(?:class|record|struct|interface|enum)\s+\w+'
)
# Einzeiliges Pflicht-Muster für readonly record struct:
# public TypeName() => throw new InvalidOperationException(...)
_THROWING_PARAMETERLESS_SINGLE = re.compile(
    r'\b(?:public|internal|protected)\s+\w+\s*\(\s*\)\s*=>\s*throw\s+new\s+InvalidOperationException'
)
# Erster Teil des zweigelierten Musters: public TypeName() ohne Body
_PARAMETERLESS_CTOR_ONLY = re.compile(r'\b(?:public|internal|protected)\s+\w+\s*\(\s*\)')
# Zweite Zeile des zweigelierten Musters: => throw new InvalidOperationException
_THROW_CONTINUATION = re.compile(r'^\s*=>\s*throw\s+new\s+InvalidOperationException')


def _is_allowed_ctor(lines: list[str], idx: int) -> bool:
    """Prüft ob Zeile idx (und ggf. Folgezeile) das erlaubte Wurf-Muster ist."""
    line = lines[idx]
    if _THROWING_PARAMETERLESS_SINGLE.search(line):
        return True
    if _PARAMETERLESS_CTOR_ONLY.search(line):
        if idx + 1 < len(lines) and _THROW_CONTINUATION.search(lines[idx + 1]):
            return True
    return False


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs:
        return []
    if inp.is_domain_excluded or inp.is_test:
        return []

    lines = inp.new_content.splitlines()
    suspicious_lines = []
    for idx, line in enumerate(lines):
        if CLASS_DECL.search(line):
            continue
        if not NON_PRIVATE_CTOR.search(line):
            continue
        if _is_allowed_ctor(lines, idx):
            continue
        suspicious_lines.append(line.strip())

    if suspicious_lines:
        examples = "\n  ".join(suspicious_lines[:3])
        return [
            "⛔ Constructor-Verletzung (blockierend): Nicht-privater Konstruktor in Domain-Code erkannt.\n"
            f"  {examples}\n"
            "Domänen-Objekte müssen private Konstruktoren haben.\n"
            "Instanziierung nur über statische Factory-Methoden: `Create(...)`, `New(...)`.\n"
            "Ausnahmen:\n"
            "  - DTOs, EF-Entities (`DatabaseTypes/`), Tests\n"
            "  - `public TypeName() => throw new InvalidOperationException(...)` für readonly record struct\n"
            "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 3)."
        ]
    return []
