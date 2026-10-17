#!/usr/bin/env python3
"""PreToolUse-Hook: Dependency-Dateien vor unkontrollierten Änderungen schützen.

Blockiert Edit/Write auf:
- jedes package.json
- jede *.csproj
- Directory.Packages.props (zentrale NuGet-Paketversionen)
- jedes dependencies.md

Directory.Build.props/.targets bleiben editierbar, weil sie Build-Einstellungen tragen –
blockiert wird dort nur neuer Text, der ein Paket einbindet oder versioniert. Sonst ließe sich
die Freigabe über diese Dateien umgehen, die MSBuild in jedes Projekt importiert.

Bewusst nicht geschützt: .config/dotnet-tools.json (lokale .NET-Werkzeuge). Ein dort neu
eingetragenes Werkzeug bliebe wirkungslos, weil die Bash-Allow-Liste sein Ausführen blockiert
(erlaubt sind nur `dotnet tool restore|list` und `dotnet ef` für Migrationen).

Grund: Externe Abhängigkeiten erfordern explizite Freigabe durch den User.
Prozess: docs/reference/dependencies.md (Sektion "Prozess: Neues Paket hinzufügen")
"""
import re


PROTECTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r'(^|[/\\])package\.json$'), 'package.json'),
    (re.compile(r'\.csproj$'), '.csproj'),
    (re.compile(r'(^|[/\\])Directory\.Packages\.props$'), 'Directory.Packages.props'),
    (re.compile(r'(^|[/\\])dependencies\.md$'), 'dependencies.md'),
]

DIRECTORY_BUILD = re.compile(r'(^|[/\\])Directory\.Build\.(props|targets)$')

# Ein Element, das ein Paket einbindet oder versioniert. Ohne Include/Update bleibt erlaubt:
# <PackageReference> in einer ItemDefinitionGroup setzt nur Standard-Metadaten.
PAKET_ELEMENT = re.compile(r'<(PackageReference|PackageVersion|GlobalPackageReference)\s[^>]*\b(Include|Update)=')

DENY_MESSAGE = """\
Dependency-Datei ({filename}) darf nicht direkt vom Agenten bearbeitet werden.

Prozess (docs/reference/dependencies.md):
1. Agent bereitet 5-Punkte-Anfrage vor
2. User gibt explizit frei
3. User trägt das Paket manuell in docs/reference/dependencies.md ein
4. User installiert das Paket: NuGet-Paket mit Version in Directory.Packages.props,
   in der .csproj nur <PackageReference Include="…" /> ohne Version"""

DENY_MESSAGE_DIRECTORY_BUILD = """\
Paketreferenz in Directory.Build.props/.targets blockiert: Diese Dateien wirken auf jedes Projekt,
ein Paket darüber umginge die Freigabe.

Pakete für alle Projekte gehören als <GlobalPackageReference> nach Directory.Packages.props,
Pakete einzelner Projekte in deren .csproj – beides über den Prozess in
docs/reference/dependencies.md (der User trägt ein)."""


def get_denial_reason(file_path: str, new_text: str = "") -> str | None:
    """Gibt die Deny-Meldung zurück, wenn die Änderung geschützt ist, sonst None.

    new_text ist der neu geschriebene Text (Edit: new_string, Write: content).
    """
    for pattern, filename in PROTECTED_PATTERNS:
        if pattern.search(file_path):
            return DENY_MESSAGE.format(filename=filename)
    if DIRECTORY_BUILD.search(file_path) and PAKET_ELEMENT.search(new_text):
        return DENY_MESSAGE_DIRECTORY_BUILD
    return None


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    if data.get("tool_name") not in ("Edit", "Write"):
        return None

    # Absolute Pfade brauchen keinen Abzug des Projektordners: Jedes Muster verankert am
    # Anfang oder an einem Pfadtrenner.
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not file_path:
        return None

    new_text = tool_input.get("new_string") or tool_input.get("content") or ""
    return get_denial_reason(file_path, new_text)
