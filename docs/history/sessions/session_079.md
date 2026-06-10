# Session 079 – Bash-Permission-Friktion ausgewertet & behoben

**Datum:** 2026-06-10
**Phase:** SKELETON (Tooling/Prozess)
**Schwerpunkt:** Offene Maßnahme aus S078 (CM): bash-permission-Friktion auswerten, Hook + Guidance verbessern.

## Ausgangslage

Offenes CM (S078): Häufige Befehls-Denies → Zeit/Token-Verlust, Ursachen ungeklärt. Auftrag: Deny-Log kategorisieren, dann entscheiden (Hook lockern / Allow-Patterns / Guidance / Deny-Hint-UX).

## Analyse

Deny-Log (`.claude/tmp/denied-commands.log`, 198 Events) per Wegwerf-Script kategorisiert, **differenziert nach Hook-Ära** (S70-Umbau am 2026-06-04, commit `bd1b8d9`):

- 71 `ONE_TIME` (bewusste `# --allow-once`, kein Problem) → **127 echte Denies**.
- PRE-S70: 69, POST-S70: 58. S70-Umbau senkte Friktion kaum.
- Re-Run aller Denies gegen den damaligen Hook: ~alle würden weiterhin denied → strukturell, kein Alt-Artefakt.
- Ursachen zu ⅔ **nicht** fehlende Patterns, sondern: (a) Bash statt Read/Grep/Glob für Read-only-Inspektion (`find|xargs grep`, `sed -n`, `cat`, `python3 -c`, `for`-Loops); (b) `cd`-Prefix + mehrzeilige/Assignment-Skripte killen den Compound; (c) **Wrapper-Scripts in `--list` unsichtbar**.

**Meta-Befund:** Der Hook denyte während der Analyse 4× meine eigenen legitimen Befehle (mehrzeilig, `python3 -c`, Heredoc, `>=` als Redirect geparst, `bash`) — zugleich Beleg fürs Problem.

## Umgesetzt (TDD, alle Tests in `test-bash-permission.py` grün)

**Hook gelockert (sicher verifiziert):**
- ALLOW `cd` (Navigation; gefährliche Kombis `cd + dotnet run`/`npx` bleiben via WRONG_APPROACH gedeckt, da das auf dem Gesamtbefehl **vor** dem Split läuft).
- ALLOW `sed` read-only (ohne `-i`/`--in-place`; In-Place bleibt Edit-Tool).
- ALLOW `xargs <safe-readonly>` (grep/cat/wc/head/tail/file/stat/sort/uniq/cut/ls — eng begrenzt, da xargs beliebige Befehle ausführt).
- ALLOW `git -C <pfad> <readonly>` (`-C` brach vorher den Anker).

**Guidance/UX:**
- Smart-Hints für `python3 -c` und `for`/`while` (Obs: Denies ohne Hint).
- `_NO_HINT_MESSAGE` zeigt auf `--list` statt irreführender CLAUDE.md-Navigationstabelle (die mappt Aufgabe→Doku, nicht Befehl→Alternative).
- `--list`-Ausgabe erweitert: Bash-Tool-Framing + Deny-Mechanik („nicht gelistet = hart geblockt") + Tool-Vorrang (Read/Edit/Grep/Glob) + **Projekt-Task→Wrapper-Block** (Backend-/Frontend-Tests, E2E, Mutation, Lint, jscpd).
- `--list` im SessionStart-Hook (`session-start.sh`) injiziert → Allow-Liste ab Zeile 1 im Kontext.

**Bewusst NICHT** (Sicherheit/Aufwand): Newline-Split (würde Heredocs brechen) und VAR_ASSIGN (`X=$(rm -rf …)` umginge die DESTRUCTIVE-Prüfung).

## Verifikation (2 Subagent-Evals)

Frischer general-purpose-Agent führt nur `--list` aus, löst eine Problemliste (Mix aus trivial-allow, combo-allow, tool-besser, allow-once-nötig, wrapper-script, deny-user-action), Vorschläge gegen den Hook geprüft:
- **Runde 1** (vor Wrapper-Block): ~11/15 korrekt; deckte die Lücke auf — `dotnet test`/`npm test` für falsch-erlaubt/unsicher gehalten, weil Wrapper-Scripts unsichtbar → unnötiger Deny.
- **Runde 2** (nach Wrapper-Block): alle Tests/Lint/Mutation-Tasks **proaktiv korrekt**; Framing (Bash-Bezug / Deny-Mechanik / Wrapper / Tool-Vorrang) als klar bestätigt. Restliche Edge-Cases (`dotnet format`, `curl`→WebFetch, `git commit`) trotzdem korrekt gelöst.

Re-Run der Alt-Denies gegen den gepatchten Hook: 35/130 gingen jetzt durch, Rest großteils *korrekte* Denies — nun mit Hints.

## Geänderte Dateien

`check-bash-permission.py`, `test-bash-permission.py`, `session-start.sh`, `docs/process/dev-workflow.md`, `docs/kaizen/countermeasures.md`, `docs/AGENT_MEMORY.md`.

## Ergebnis

CM (S078, bash-permission-Friktion) → **AKTIV**. Ziel (Agenten arbeiten autonom korrekt ohne unnötige Denies/allow-once) für die Standard-Tasks empirisch erreicht.

## Offene Punkte

- CM **HOCH→CM-Härtung prüfen** (closing-session-Prüfung weich) bleibt OFFEN.
- US-904 weiter (nächstes Szenario aus `features/ingredients.feature`).
