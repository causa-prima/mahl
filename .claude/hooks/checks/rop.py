"""
ROP-Check (blockierend): .IsT0/.AsT0 (C#) und .isOk()/.isErr() (TypeScript) im Produktionscode.
Falls die Änderung nach den Guidelines korrekt sein sollte, bitte Rücksprache mit dem Aufrufer halten.
"""
import re
from .common import HookInput

CS_FORBIDDEN = re.compile(r'\.(IsT\d|AsT\d)\b')
TS_FORBIDDEN = re.compile(r'\.(isOk|isErr|_unsafeUnwrap)\s*\(')


def check(inp: HookInput) -> list[str]:
    warnings = []

    if inp.is_cs and not inp.is_test:
        matches = CS_FORBIDDEN.findall(inp.new_content)
        if matches:
            found = ", ".join(f"`.{m}`" for m in set(matches))
            warnings.append(
                f"⛔ ROP-Verletzung (C#, blockierend): {found} erkannt.\n"
                "Verwende stattdessen `.Match(ok => ..., err => ...)` oder `.MatchAsync(...)`.\n"
                "Gilt global für allen Produktionscode – nicht nur in Endpoints.\n"
                "Siehe CODING_GUIDELINE_CSHARP.md (ROP-Abschnitt)."
            )

    if inp.is_ts and not inp.is_test:
        matches = TS_FORBIDDEN.findall(inp.new_content)
        if matches:
            found = ", ".join(f"`.{m}()`" for m in set(matches))
            warnings.append(
                f"⛔ ROP-Verletzung (TypeScript, blockierend): {found} erkannt.\n"
                "Verwende stattdessen `.match(ok => ..., err => ...)` (neverthrow).\n"
                "`_unsafeUnwrap()` ist nur in Tests erlaubt.\n"
                "Siehe CODING_GUIDELINE_TYPESCRIPT.md (ROP-Abschnitt)."
            )

    return warnings
