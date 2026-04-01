"""
Prüft ob Typ-Deklarationen in mahl.Server public statt internal sind.
Hexagonal Architecture: alle Typ-Deklarationen in Server/ müssen internal sein.
Ausnahme: Infrastructure/-Typen (MahlDbContext, *DbType) sind public.
"""
import re
from .common import HookInput

# Dateipfade im Server-Projekt (Domain, Endpoints, Dtos, Types, Helpers)
# aber explizit NICHT Infrastructure/
SERVER_PATH = re.compile(r'(?:^|[/\\])Server[/\\](?!.*Infrastructure).*\.cs$')

# public Typ-Deklarationen (class, record, struct, interface, enum)
# Ignoriert: Kommentare, file-scoped (implizit internal), abstract/sealed/readonly modifier
PUBLIC_TYPE = re.compile(
    r'^[ \t]*public\s+(?:(?:static|abstract|sealed|readonly|partial)\s+)*'
    r'(?:class|record|struct|interface|enum)\b',
    re.MULTILINE
)

# Ausnahmen: Infrastructure-Pfade sind explizit public
INFRASTRUCTURE_PATH = re.compile(r'[/\\]Infrastructure[/\\]')


def check(inp: HookInput) -> list[str]:
    if not inp.is_cs:
        return []
    if inp.is_test:
        return []
    if not SERVER_PATH.search(inp.file_path):
        return []
    if INFRASTRUCTURE_PATH.search(inp.file_path):
        return []

    violations = []
    for match in PUBLIC_TYPE.finditer(inp.new_content):
        line_num = inp.new_content[:match.start()].count('\n') + 1
        snippet = match.group().strip()[:80]
        violations.append(
            f"❌ DOMAIN VISIBILITY: `public` Typ-Deklaration in Server/ (Zeile {line_num}):\n"
            f"   {snippet}\n"
            f"   → Alle Typ-Deklarationen in Server/ müssen `internal` sein (Hexagonal Architecture).\n"
            f"   → `internal` betrifft die Typdeklaration – Member bleiben `private`/`protected`.\n"
            f"   → Ausnahme: Infrastructure/-Typen (MahlDbContext, *DbType) sind `public`.\n"
            f"   → Begründung: docs/ARCHITECTURE.md Sektion 0c"
        )

    return violations
