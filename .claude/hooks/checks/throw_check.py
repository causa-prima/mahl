"""
Throw-Check: throw-Statements im C#-Produktionscode.
TypeScript: throw wird durch functional/no-throw-statements (ESLint) und Review-Checkliste abgedeckt.
"""
import re
from .common import HookInput

CS_THROW = re.compile(r'\bthrow\s+new\s+(\w+)')
CS_ALLOWED = {'InvalidOperationException'}


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs or inp.is_test:
        return []

    violations = {
        f"`throw new {m}`"
        for m in CS_THROW.findall(inp.new_content)
        if m not in CS_ALLOWED
    }
    if not violations:
        return []

    found = ", ".join(violations)
    return [
        f"⛔ Throw-Verletzung (C#, blockierend): {found} im Produktionscode erkannt.\n"
        "`throw` ist eine Ausnahme, keine Regel:\n"
        "  ✅ Erlaubt: `throw new InvalidOperationException` in Value-Object-Guards\n"
        "  ❌ Domänen-/Validierungsfehler → `OneOf<T, Error<string>>` zurückgeben\n"
        "Jedes `throw` muss mit einem Kommentar begründet werden.\n"
        "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 4 – ROP)."
    ]
