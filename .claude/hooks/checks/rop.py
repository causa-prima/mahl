"""
ROP-Check (blockierend): .IsT0/.AsT0 (C#) im Produktionscode.
TypeScript: isOk()/isErr()/_unsafeUnwrap() werden durch ESLint no-restricted-syntax abgedeckt.
"""
import re
from .common import HookInput

CS_FORBIDDEN = re.compile(r'\.(IsT\d|AsT\d)\b')


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs or inp.is_test:
        return []

    matches = CS_FORBIDDEN.findall(inp.new_content)
    if not matches:
        return []

    found = ", ".join(f"`.{m}`" for m in set(matches))
    return [
        f"⛔ ROP-Verletzung (C#, blockierend): {found} erkannt.\n"
        "Verwende stattdessen `.Match(ok => ..., err => ...)` oder `.MatchAsync(...)`.\n"
        "Gilt global für allen Produktionscode – nicht nur in Endpoints.\n"
        "Siehe CODING_GUIDELINE_CSHARP.md (ROP-Abschnitt)."
    ]
