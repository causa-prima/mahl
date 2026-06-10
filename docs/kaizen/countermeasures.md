# Countermeasures

<!--
wann-lesen: In jeder Retro – AKTIV/OFFEN auf Wirksamkeit prüfen, BEWÄHRT auf Regressionen scannen.
wann-schreiben: Nach KRITISCH- oder HOCH-Finding sofort; nach Retro wenn Muster in MITTEL/GERING erkannt.

Status-Lifecycle: OFFEN → [IN UMSETZUNG] → AKTIV → BEWÄHRT
  OFFEN: Problem bekannt, Maßnahme noch nicht definiert oder noch nicht implementiert.
  IN UMSETZUNG: (optional) Maßnahme definiert, Umsetzung dauert mehrere Sessions.
  AKTIV: Maßnahme live – Wirksamkeit wird beobachtet.
  BEWÄHRT: In einer Retro explizit erklärt (Kriterium: docs/kaizen/process.md).
           Bleibt in dieser Datei (unterer Abschnitt) – für Regressions-Erkennung.
           Regression = neues Finding das inhaltlich passt → zurück auf AKTIV.

Kontext-Spalte:
  Welche Kontext-Tags (aus process.md) diese Maßnahme abdeckt.
  Leer = Wildcard (Maßnahme gilt für alle Kontexte dieser Schwere+Kategorie).
  Mehrere Werte kommasepariert: z.B. "Agent-Prompt, Review"
  Wann leer lassen: Maßnahme ist generisch genug, dass der konkrete Kontext keine Rolle spielt
    (z.B. "Guidelines nicht angewandt" trifft auf TDD, C#-Code, TS-Code gleichermaßen zu).
  Wann befüllen: Problem ist klar auf bestimmte Kontexte beschränkt und würde bei anderen
    Kontexten zu False-Positives im Pattern-Kandidaten-Report führen.

Reaktionsregeln je Schwere: docs/kaizen/process.md
-->

## Aktive Maßnahmen

| Problem | Schwere | Kategorie | Kontext | Maßnahme | Status | Seit Session |
|---------|---------|-----------|---------|----------|--------|--------------|
| Ad-hoc-Bash-Befehle statt erlaubter Befehle aus docs/process/dev-workflow.md (S53: `npx playwright test`) | MITTEL | TOOLING | Bash/Permission | `check-bash-permission.py` umgebaut: auto-deny, `# --allow-once`-Marker, Log in `.claude/tmp/denied-commands.log`, Smart-Hints, neue Allow-Patterns (npx, dotnet run). docs/process/dev-workflow.md aktualisiert. | AKTIV | 056 |
| Review-Agent-Output blind übernommen (semantisch falsch) | HOCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert; Prüf-Schritt in `review-code` Skill ergänzt | AKTIV | 047 |
| Guidelines gelesen aber nicht auf konkreten Fall angewandt (Rückfall S53: YAGNI) | HOCH | PROZESS | | `write-code` Skill: Pflicht-Schritt "Guidelines lesen" + explizite Per-Member-YAGNI-Frage: „Welcher aktuell rote Test fordert genau das?" | AKTIV | 047 |
| Behauptungen über externes Tool-Verhalten als gesichertes Wissen präsentiert (S061, S063) | HOCH | AGENT | Kommunikation | Regel in `principles.md` dokumentiert ✓. Selbst-Check vor jeder Tool-Verhaltensbehauptung: „Basiert das auf einem Tool-Call dieser Session?" Falls nein: explizit als unverified kennzeichnen und Verifizierung anbieten. | AKTIV | 064 |
| Infrastruktur-Fehler oder Tooling-Trivia als lessons_learned dokumentiert (S061 ×2, S063, S053, S052) | MITTEL | QUALITÄT | Sonstiges | Filter-Test in `docs/kaizen/process.md` und im lessons_learned-Header ergänzt. Preprocessing-Schritt im `kaizen`-Skill (vor retro_report.py): Noise-Review von lessons_learned + Archiv mit User-Freigabe. | AKTIV | 064 |
| Neue Guideline wird nicht in bestehende Skills und Feature-Files integriert (S063: UX-Guideline) | MITTEL | PROZESS | Doku | Beim Einführen einer neuen Guideline: explizit prüfen welche Skills sie referenzieren sollen + ob bestehende Feature-Files einen Retrofit-Workshop brauchen. Hinweis als Pflicht-Schritt in `closing-session` Skill ergänzt. | AKTIV | 064 |
| Subagent implementierte Code beyond Szenario-Scope; Tests wurden nachträglich angepasst um Gold-Plating zu verschleiern; Orchestrator-Check erkannte es nicht (S069) | KRITISCH | PROZESS | TDD | (1) Orchestrator-Vorabanalyse vor E2E-Test auf Spec-Ambiguitäten; (2) Subagent bittet nach RED um Test-Review + stagt Tests; (3) Per-Assertion-Zuordnung, Full-State-Assertion-Check, Check auf Anpassungen an bestehenden Tests; (4) Staged-Test-Check in Schritt 4. Details: `implementing-scenario` SKILL.md | AKTIV | 070 |
| Subagent meldete Stryker 100% auf Basis eines --mutate-Runs; vollständiger Lauf ergab 83% (S069) | HOCH | PROZESS | TDD | Subagenten-Prompts in `implementing-scenario` SKILL.md: vollständiger Stryker-Lauf ohne --mutate Pflicht für Übergabe; Pfad zur HTML-Report-Datei in Summary | AKTIV | 070 |
| check-bash-permission.py: --list nicht selbst-wartend; sed ohne Hint; DLL-Lock ohne automatischen Check (S069) | HOCH | TOOLING | Bash/Permission, Mutation-Testing | --list via 3-Tupel selbst-wartend; sed-Hint ergänzt; `check_dotnet_dll_lock()` in dotnet-Skripten integriert | AKTIV | 070 |
| Subagenten lieferten keine strukturierten Rückmeldungen über Tooling-Probleme (S069) | MITTEL | PROZESS | Agent-Prompt | Pflicht-Abschnitt "Prozessverbesserung" am Ende jedes Subagenten-Prompts in `implementing-scenario` SKILL.md | AKTIV | 070 |
| User-facing Verhaltensszenarien (Dialog-Reset, Abbrechen, Feld-Init, Async-States) fehlen systematisch in Feature-Files (S069) | MITTEL | PROZESS | Gherkin | UI-Verhaltens-Checkliste in `gherkin-workshop` Schritt 1 + MEDIUM-Finding in `references/agent-review.md` | AKTIV | 070 |
| Hintergrund-Subagenten scheiterten an Edit/Write-Permissions (kein interaktiver Bestätigungskanal) (S070) | MITTEL | TOOLING | Agent-Prompt | Subagenten die Dateien editieren als Vordergrund-Agenten starten (kein `run_in_background: true`); alternativ: relevante Pfade vorab in `settings.json` unter `permissions.allow` eintragen | AKTIV | 070 |
| Häufige Befehls-Denies (127 echte Denies, 58 mit aktuellem Hook seit S70) → Zeit/Token-Verlust (S078) | MITTEL | TOOLING | Bash/Permission | Deny-Log kategorisiert (pre/post-S70-Split): Friktion zu ⅔ **nicht** durch fehlende Patterns, sondern (a) Bash statt Read/Grep/Glob für Read-only-Inspektion, (b) mehrzeilige/Assignment-Skripte + `cd`-Prefix, (c) **Wrapper-Scripts in `--list` unsichtbar** → Agent griff zu `dotnet test`/`npm test` → unnötiger Deny (per Subagent-Eval bestätigt). Maßnahmen: ALLOW `cd`, `sed` (read-only), `xargs <safe>`, `git -C <readonly>`; Smart-Hints für `python3 -c`/`for`/`while`; `_NO_HINT_MESSAGE` zeigt auf `--list` statt Nav-Tabelle; `--list` um Bash-Framing + Deny-Mechanik + Tool-Vorrang + **Projekt-Task→Wrapper-Block** erweitert; `--list` im SessionStart-Hook injiziert (Allow-Liste ab Zeile 1). Verifiziert: 2. Subagent-Eval löste alle Tests/Lint/Mutation-Tasks proaktiv korrekt. Re-Run: 35/130 Alt-Denies gingen jetzt durch, Rest großteils korrekt+behintet. Bewusst NICHT: Newline-Split (Heredoc-Bruch), VAR_ASSIGN (umgeht DESTRUCTIVE-Check). Tests in `test-bash-permission.py`. | AKTIV | 078 |
| HOCH-Findings bekommen nicht zuverlässig einen CM-Eintrag (S71/74/76/77 ohne CM trotz process.md-Pflicht); `closing-session`-Prüfung ist weiche Ermessensfrage (S078) | MITTEL | PROZESS | Skill-Nutzung | Prüfen ob HOCH→CM von weicher Prüfung zu erzwungenem Check wird (z.B. flaggt HOCH-Findings ohne zugehörigen CM-Eintrag) | OFFEN | 078 |

---

## Bewährte Maßnahmen

> Nur auf Regressionen prüfen: Gibt es ein neues Finding in `lessons_learned.md`, das inhaltlich
> zu einem Eintrag hier passt? Falls ja → zurück in "Aktive Maßnahmen" mit Status AKTIV.

| Problem | Schwere | Kategorie | Kontext | Maßnahme | Status | Seit Session |
|---------|---------|-----------|---------|----------|--------|--------------|
| Reviewer mit Iterations-Vorwissen beauftragt | KRITISCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert ✓; Pflicht-Hinweis in `review-code` SKILL.md Schritt 3 ergänzt: keine früheren Findings, keine false-positive-Labels übergeben | BEWÄHRT | 047 |
