# Session 019 – 2026-03-06: PreToolUse-Hook für Bash-Permissions

## Kontext

Fortsetzung von Session 18. Das Permission-System wurde als unzuverlässig identifiziert:
`permissions.allow`-Glob-Patterns matchten Compound-Commands nicht (Sicherheitsdesign), und
`fall-through` (exit 0, kein JSON) führte zu ungeplanten Auto-Approvals durch den Session-State.

---

## Implementiertes

### `check-bash-permission.py` (neu)

PreToolUse-Hook für alle Bash-Befehle. Entscheidungskette:

1. **Priority-Allow** (vor Deny): Stryker NUR mit Python-Summary-Script (`cmd.exe ... && dotnet stryker... | tail -60 && python3 .claude/scripts/stryker-summary.py`)
2. **Deny** auf vollständigem Befehl: stryker ohne Script, Pipe in cmd.exe, `find -delete`, `find -exec rm`, `rm -r/-rf/-R/-fR/-Rf`, `git push --force`, `git reset --hard`, `git clean -f`, `git checkout .`, `git restore .`, `git add -f/--force`
3. **Compound-Command-Splitting**: Befehl an `|`, `||`, `&&`, `;` aufteilen (quote-aware), jedes Segment einzeln prüfen
4. **Allow**: ~25 Patterns (dotnet build/test, npm, docker, Lese-/Analyse-Befehle, mkdir/touch/jq/chmod +x, python3 nur .claude/, git read-only, git add/stash safe writes)
5. **Explizites `ask`**: Für alles andere – erzwingt immer einen Prompt

Output-Redirect-Erkennung: unquoted `>` / `>>` werden erkannt; nur `.claude/tmp/`, `/dev/null`, `/dev/stderr`, `/dev/stdout` sind sichere Ziele. `>&N` (File-Descriptor) immer erlaubt.

### `test-bash-permission.py` (neu, 96 Tests)

Vollständige Test-Suite für den Hook. Alle 96 Tests grün.

### `settings.json` (angepasst)

- `permissions.allow: []` – Hook ist alleinige Autorität
- PreToolUse-Hook für alle Bash-Befehle ergänzt

### `.claude/tmp/.gitkeep` (neu)

Sicheres Zielverzeichnis für Output-Redirects.

### `check-pre-commit.sh` (gelöscht)

Toter Hook: `Bash(git commit*)` Matcher feuert nie (matcht auf Tool-Namen, nicht Kommando-Inhalt). Script und Settings.json-Eintrag entfernt.

---

## Probleme und Lösungen

| Problem | Ursache | Lösung |
|---------|---------|--------|
| `fall-through` → kein Prompt | Claude Code Session-State kann auto-approven | Explizites `permissionDecision: "ask"` statt fall-through |
| `Bash(git commit*)` feuert nie | Matcher matcht Tool-Namen `"Bash"`, nicht Kommando | Hook-internen Kommando-Parse-Ansatz verwenden |
| `rm -fR` nicht gematcht | Deny-Pattern war case-sensitive (nur `r`) | `[rR]` im Pattern |

---

## Ergebnisse

- Permission-System ist jetzt vollständig durch den Python-Hook kontrolliert
- 96 Tests sichern das Verhalten ab
- `permissions.allow: []` verhindert unerwartete Auto-Approvals

---

## Offene Punkte

- **`Quantity`-TDD abschließen**: `Create(decimal)`, `> 0`-Validierung, `SpecifiedCase`
- **Stryker-Findings (Mittel-Priorität)**: AND→OR in Ingredients/Recipes, OrderBy in Recipes, WeeklyPool 7 Survivors
- **Frontend-Neuimplementierung** (4 Seiten)
