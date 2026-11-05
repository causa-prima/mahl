# Anknüpfung an Claude Code

<!--
wann-lesen: In der monatlichen Abhängigkeits-Durchsicht (Claude-Code-Abgleich) und bevor ein Hook, Wrapper oder Skill auf ein Verhalten von Claude Code gebaut wird
kritische-regeln: Jede neue Anknüpfung kommt in die Tabelle; „Abgeglichen bis" schreibt nur die Durchsicht fort
-->

Vieles im Prozess tun wir **so**, weil Claude Code an einer Stelle so funktioniert – ein Hook
fängt einen Aufruf ab, ein Wrapper kürzt eine Ausgabe, ein Script schreibt statt `Edit`. Ändert
sich das Verhalten, kann das Gebaute still falsch werden oder überflüssig. Diese Liste ist die
Bewertungsbasis dafür: Sie nennt je Anknüpfung, was wir darauf bauen und welche Annahme dahinter
steht.

**Abgeglichen bis:** Claude Code 2.1.318 (2026-11-05)

<a id="CCA-abgleich"></a>
## Abgleich in der Durchsicht

Die [Abhängigkeits-Durchsicht](dev-workflow.md#DEV-abhaengigkeiten-durchsicht) liest den
[Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) ab der Version
oben und geht die Tabelle Zeile für Zeile durch:

- **Berührt ein Eintrag die Zeile** – gründlich neu bewerten: Stimmt die Annahme noch (an der
  Doku oder am echten Verhalten geprüft, nicht vermutet)? Ist unser Weg noch der beste, oder
  bietet Claude Code jetzt einen, der ihn ersetzt?
- **Sonst oberflächlich:** Macht eine neue Funktion die Zeile überflüssig oder einfacher, auch
  wenn sie die Annahme nicht bricht?

Befunde werden behoben oder dem User vorgelegt wie jedes Update. Danach „Abgeglichen bis" auf
die laufende Version setzen. Sie steht im Session-Log (`"version"` in der jsonl unter
`~/.claude/projects/<repo>/`). Neue Anknüpfungen, die beim Abgleich auffallen, kommen in die
Tabelle.

<a id="CCA-liste"></a>
## Anknüpfungen

| Anknüpfung | Worauf wir bauen (wo) | Annahme über Claude Code |
|---|---|---|
| PreToolUse als Gate | Bash-Allow-Liste, Edit/Write-Prüfungen, Agent-Start (`.claude/settings.json` → `prozesscode/hooks/`) | Exit 2 bzw. `permissionDecision: deny` blockt; `ask` erzwingt den Prompt **auch im Auto-Modus** (seit 2.1.283 Startmodus im Terminal). Ein Hook, der abstürzt, Exit ≠ 0/2 liefert oder ins Timeout läuft, lässt den Aufruf durch – im Auto-Modus entscheidet dann der Klassifizierer. Ausnahme: Der Bash-Guard trägt `onFailure: "block"`, sein Fehlschlag blockt wie Exit 2. Ein installierter Mod mit `tool.check` kann einen Block unseres Hooks überstimmen. |
| Eigene Bash-Allow-Liste statt `permissions.allow` | `check-bash-permission.py`, `# --allow-once` | Die eingebauten Regeln zerlegen Verkettungen und `for`-Rümpfe und verlangen für jeden Teilbefehl eine Allow-Regel; Deny-Regeln greifen auch in `$(…)` und Heredocs. `$(…)` und Heredocs mit unquotiertem Begrenzer geben Allow-Regeln aber nie frei – sie fragen immer, auch wenn jeder Teilbefehl erlaubt ist. Ein Deny meldet nur „has been denied", ohne Ausweg-Hinweis (gemessen 2.1.318 mit `claude -p`, eigene `--settings`, `--setting-sources project`). Unser Guard lässt diese Strukturen zu, prüft ihren Inhalt je Teilstück und nennt beim Block den erlaubten Weg. |
| Freigabe-Vorschau für Tracker-Schreibbefehle | `tracker_preview.py` (Kopfzeile und Warnungen) als Reason einer `ask`-Entscheidung; die Änderung zeigt der Mod `tracker-diff` mit `tracker_diff.py` | Der Permission-Prompt zeigt den Reason-Text einfarbig; umgestalten lässt er sich nicht, auch nicht per Mod. Darum steht die Änderung in einem Pane daneben. |
| Mods (`.claude/mods/`, Marktplatz `mahl-mods`) | `tracker-diff`; `naechste-aufgabe` (Band über dem Prompt beim Session-Start und nach `/clear` aus `session-agenda --ueberblick`, weg mit dem ersten Prompt); Tests per `claude plugin test`, angebunden in `tests/test_mods.py` | `session.start` wird vor dem ersten Prompt abgewartet – darum liest `naechste-aufgabe` die Agenda (rund 2 s) per `$.clock.after` im Hintergrund. Nach `/clear` feuert `session.start` nicht, wohl aber `classic.SessionStart` mit `source: 'clear'` – daran hängt das Band dort (laut API-Typen 2.1.318); die SessionStart-Injektion erreicht nur das Modell, nicht den User. Ein Pane, das ein Mod aus `tool.call` öffnet, erscheint neben dem Prompt, lässt sich aber **nicht scrollen**, solange der Prompt die Tastatur hat, und zeigt keinen Scrollbalken. Farben erscheinen darin gedämpft (gemessen 2.1.302). Ein Mod, der per `tool.check` selbst freigibt, wäre eine Freigabe-Instanz – bewusst keiner. Abweisen dagegen tut `tracker-diff`: Scheitert das echte Werkzeug schon in der Berechnung des Diffs, antwortet der Mod mit `{ deny }`, und der Freigabe-Prompt erscheint gar nicht; scheitert nur `tracker_diff.py` selbst, zeigt er das und lässt den Befehl durch. |
| Read vor Edit | Tracker per Script statt `Edit` (Kosten: `read-breakdown`, „Vor-Edit-Reads") | `Edit` verlangt ein vorheriges `Read` der Datei in der Session. |
| PostToolUse-Rückmeldung | `check-code-quality-nonblocking` (Suite, ruff, ESLint), `merke-rueckgaben` (Hinweis beim Start) | Die Ausgabe eines Exit-2-Hooks und `additionalContext` erreichen das Modell. |
| Stop-Erinnerung | `merke-rueckgaben` | Der Stop-Hook erhält `background_tasks` und `stop_hook_active`; ein Block wirkt einmal je Turn. |
| SessionStart-Injektion in Blöcken | `session-agenda.py` (fünf Blöcke) | Hook-Ausgabe über 10.000 Zeichen wird gegen Dateipfad und 2.000er-Vorschau getauscht, ohne Signal an den Hook. Matcher `compact` feuert nach einer Zusammenfassung. |
| Session-Logs als Datenquelle | `_session_logs.py`, `read-breakdown`, `tool-usage`, Skill `recall-session`, `.claude/session-types.json` | Format der jsonl: Gespräch nur in Einträgen vom Typ `user`/`assistant` (seit 2.1.300 wiederholen `api-request-blob`-Einträge Nachrichten), `attributionSkill` am Eintrag. |
| Umgebung | `CLAUDE_PROJECT_DIR`, `CLAUDE_CODE_SESSION_ID`, Scratchpad-Pfad, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Variablen und Pfad bestehen in Hooks und Bash-Aufrufen. |
| Bash-Werkzeug | Kein nacktes `cd` (`--prefix`/`-C`), `cd <Repo-Root>` bleibt im Bash-Guard absolut; absolute Repo-Pfade kürzt der Guard im ausgeführten Befehl nur, wenn `cwd` im Hook-Input der Repo-Root ist; Wrapper-Verdikte statt Rohausgabe | Der Hook-Input trägt `cwd` (gemessen 2.1.318). Das Arbeitsverzeichnis bleibt in der Hauptsession nur nach einem erfolgreichen Befehl bestehen, nach einem gescheiterten nicht; endet es außerhalb der Arbeitsverzeichnisse, setzt Claude Code es auf den Startordner zurück. In Subagenten bleibt `cd` nie über den Aufruf hinaus bestehen (alles gemessen 2.1.318). Die Ausgabe geht vollständig ins Modell; Grep und Glob fehlen unter Linux in Sessions mit Bash. |
| Hintergrundläufe | `rueckgaben.py`, `merke-rueckgaben` | Claude Code meldet das Ende per Task-Notification, merkt sich aber nicht, ob das Ergebnis verarbeitet ist. |
| Subagenten | `.claude/agents/`, Skill `review-code`, `check-agent-start` | Subagenten starten auch im Terminal ohne Einstellung im Hintergrund (gemessen 2.1.318); ihre Berechtigungsabfragen erscheinen in der Hauptsession. Das `permissionMode` einer Agent-Definition wirkt nur, wenn die Hauptsession in `default` läuft; in `auto` und `acceptEdits` übernimmt der Subagent den Modus der Hauptsession und ignoriert die Definition (gemessen 2.1.318 mit `claude -p`; für `bypassPermissions` und `dontAsk` nur laut Doku). Hintergrund-Subagenten schieben Shell-Befehle nach 3 Minuten in den Hintergrund (laut Changelog 2.1.318). |
| Skills | `.claude/skills/`, Skill-Tool | Skills laden über Name und Frontmatter; ihr Text kommt erst beim Aufruf in den Kontext. |
| Projektanweisungen | `AGENTS.md` (keine `CLAUDE.md` im Repo) | `AGENTS.md` wird geladen – über den eingebauten Mod `cc-plugin-agents-md`; ist er in `/plugin` abgeschaltet, fehlt sie. |
| Permission-Modus und Regeln | `permissions.allow` für Edit-Pfade in `.claude/settings.json` | Edits im Arbeitsverzeichnis laufen im Auto-Modus ohne Prompt; geschützte Pfade gehen an den Klassifizierer. |
| Plugins | `typescript-lsp` (LSP-Werkzeug), `tool-usage --lsp` | Das Plugin liefert das Werkzeug `LSP`. |
