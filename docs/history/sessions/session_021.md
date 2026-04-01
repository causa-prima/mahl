# Session 21 – 2026-03-09: Hook-Architektur-Fixes

## Kontext
Wartungs-Session: Zwei bekannte Hook-Probleme behoben + Infrastruktur stabilisiert. Kein Produktionscode geändert.

---

## Implementiertes

### 1. Blocking-Hook → PreToolUse
`check-code-quality-blocking.py` war fälschlicherweise in `PostToolUse` (konnte nicht blockieren, weil das Tool bereits ausgeführt war). → Verschoben nach `PreToolUse`. Jetzt blockiert es Write/Edit tatsächlich vor der Ausführung.

`check-code-quality-nonblocking.py` bleibt in `PostToolUse` (advisory, nach dem Schreiben).

### 2. $PWD → $CLAUDE_PROJECT_DIR
Alle Hook-Commands in `.claude/settings.json` nutzen jetzt `$CLAUDE_PROJECT_DIR` statt `$PWD`. `$PWD` ist fragil: wenn `cd` in einem Bash-Tool-Call ausgeführt wird, persistiert der neue CWD und bricht alle Hook-Pfade.

### 3. `bash -c "..."` Wrapper entfernt
Die Code-Quality-Hooks wurden mit `bash -c "python3 ..."` aufgerufen – unnötige Komplexität. Direkt `python3 $CLAUDE_PROJECT_DIR/...` wie beim Bash-Permission-Hook. Mit Test verifiziert.

### 4. `Error<string>` Filter in primitives.py
`PARAM_PATTERN` triggerte fälschlicherweise bei `public static OneOf<T, Error<string>> Create(string name) =>` – der `(string name)`-Parameter wurde als Primitive Obsession gewertet. Fix: Zeilen mit `Error<string>` werden vor dem Check ausgefiltert (analog `ENDPOINT_MAPPING_LINE`). Generics generell auszufiltern wurde diskutiert und verworfen (würde echte Violations wie `List<string>` als Property maskieren).

### 5. Neue Hook-Tests (primitives.py)
- `test_error_string_factory_method_not_blocked`: Factory-Method-Signatur mit `Error<string>` wird nicht geblockt
- `test_string_param_without_error_string_still_blocked`: String-Parameter ohne `Error<string>` wird weiterhin erkannt

---

## Probleme

### $PWD-CWD-Bruch
Nach `cd .claude/hooks` im Bash-Tool: Hook-Chain komplett gebrochen → Session-Neustart nötig. Nicht alle Tests konnten in der Session durchgeführt werden.

### Schlechte Testwahl (DENY-Hook)
`git push --force` als DENY-Test gewählt – wenn der Hook ausgefallen wäre, hätte der Befehl ausgeführt werden können. Hätte `dotnet stryker` (DENY + harmlos) sein sollen.

---

## Ergebnisse
- Alle 4 Hook-Typen nach Neustart verifiziert: ✅ Bash-allow, ✅ Bash-deny, ✅ Blocking-PreToolUse, ✅ Nonblocking-PostToolUse
- 54 Hook-Tests (war 52, +2 neue für `Error<string>`)
- Keine Produktions-Codeänderungen

## Offene Punkte
- Stryker-Findings (Mittel-Priorität) unverändert offen → nächste Priorität
- Frontend-Neuimplementierung ausstehend
- DEV_WORKFLOW.md: Hinweis auf `$CLAUDE_PROJECT_DIR` + CWD-Gefahr pending (User-Approval noch offen)
