"""Throw-Check: throw-Statements im Produktionscode."""
import re
from .common import HookInput

CS_THROW = re.compile(r'\bthrow\s+new\s+(\w+)')
CS_ALLOWED = {'InvalidOperationException'}
TS_THROW = re.compile(r'\bthrow\b')


def check(inp: HookInput) -> list[str]:
    warnings = []

    if inp.is_cs and not inp.is_test:
        violations = {
            f"`throw new {m}`"
            for m in CS_THROW.findall(inp.new_content)
            if m not in CS_ALLOWED
        }
        if violations:
            found = ", ".join(violations)
            warnings.append(
                f"⛔ Throw-Verletzung (C#, blockierend): {found} im Produktionscode erkannt.\n"
                "`throw` ist eine Ausnahme, keine Regel:\n"
                "  ✅ Erlaubt: `throw new InvalidOperationException` in Value-Object-Guards\n"
                "  ❌ Domänen-/Validierungsfehler → `OneOf<T, Error<string>>` zurückgeben\n"
                "Jedes `throw` muss mit einem Kommentar begründet werden.\n"
                "Siehe CODING_GUIDELINE_CSHARP.md (Abschnitt 4 – ROP)."
            )

    if inp.is_ts and not inp.is_test:
        count = len(TS_THROW.findall(inp.new_content))
        if count:
            warnings.append(
                f"⛔ Throw-Verletzung (TypeScript, blockierend): {count}× `throw` im Produktionscode erkannt.\n"
                "`throw` ist eine Ausnahme, keine Regel:\n"
                "  ✅ Erlaubt: echte technische Ausnahmezustände (5xx, unerwarteter Server-Fehler)\n"
                "  ❌ Domänen-/Validierungsfehler → `neverthrow` `err(...)` zurückgeben\n"
                "Siehe CODING_GUIDELINE_TYPESCRIPT.md (Abschnitt 4 – ROP)."
            )

    return warnings
