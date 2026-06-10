# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Review | Agent-Prompt | Skill-Nutzung |
            Session-Struktur | Tooling | Gherkin | Doku | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen: Gab es ein falsches Agenten-Verhalten das wieder auftreten kann? Nein → kein Eintrag (Infra-Wissen → docs/process/dev-workflow.md / Config). Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

## Session 077 – 2026-06-10

- **[HOCH] [TOOLING] [Tooling] Mutation-Gate war dekorativ – nirgends mechanisch erzwungen**
  Was: Trotz „100 % Mutation Score Pflicht" brach kein Skript bei Survivor/NoCoverage ab: Stryker-Config ohne `thresholds.break` (Default `null`), `stryker-summary.py` exit 0 trotz Survivors, `qa-check.py` prüfte nur den Stryker-Prozess-Exit. Der NoCoverage-`map`-Survivor des Vorszenarios rutschte so durch.
  Warum: Das Gate verließ sich vollständig auf manuelle/LLM-Sichtprüfung der gedruckten Survivor-Liste; kein Exit-Code erzwang den Schwellwert.
  Regel: Bei jedem „X % Pflicht"-Gate verifizieren, dass ein konkreter Exit-Code/Mechanismus den Schwellwert erzwingt – „das Skript zeigt es an" ≠ „das Skript blockiert".

- **[MITTEL] [TOOLING] [Tooling] Eigene Metrik statt der Tool-eigenen nachgerechnet**
  Was: `stryker-summary.py`/`qa-check.py` rechneten den „covered code"-Score (`Killed/(Killed+Survived+Timeout)`, NoCoverage raus) statt des Standard-Mutation-Scores (`detected/(detected+undetected)`, NoCoverage drin), den Stryker selbst im HTML zeigt. Folge: NoCoverage senkte den Score nicht.
  Warum: Der JSON-Report enthält kein Score-Feld; bei der Nachberechnung wurde die falsche der zwei Stryker-Score-Varianten gewählt.
  Regel: Wenn ein Tool eine Metrik selbst definiert (hier: HTML-Mutation-Score), exakt diese replizieren – keine abweichende Eigenvariante erfinden.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Orchestrator überschrieb Handoff-Befehl der Agent-Definition**
  Was: Der Orchestrator wies den Subagenten an, `qa-check.py` mit `--skip-stryker` zur Übergabe zu nutzen – entgegen der Agent-Definition (Übergabe = frischer Lauf). Das schwächte die Frische-Garantie des Verifikations-Hashes.
  Warum: `--skip-stryker` aus dem Orchestrator-Schritt (Verifikation) wurde fälschlich auf die Subagenten-Übergabe übertragen.
  Regel: Handoff-Befehle stehen in der Agent-Definition; nicht im Orchestrator-Prompt überschreiben. Gegenmaßnahme umgesetzt: `--skip-stryker` erzeugt keinen Hash mehr; Orchestrator verifiziert via `--verify`.

- **[GERING] [TOOLING] [Tooling] StrykerJS ignoriert JSX-`{/* … */}`-Disable-Kommentare**
  Was: `{/* Stryker disable next-line ArrowFunction */}` vor einem `{ingredients.map(...)}` wurde nicht erkannt – der Mutant blieb NoCoverage.
  Warum: StrykerJS liest Disable-Direktiven nicht aus JSX-Block-Kommentaren (JSXExpressionContainer).
  Regel: Stryker-Disable in JSX als `//`-Zeilenkommentar *innerhalb* der `{ }`-Expression setzen (eigene Zeile vor dem Ausdruck), nicht als `{/* */}`.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Subagent-Vorschläge + zurückgestellte ⚠️-Findings fielen durch**
  Was: Der Frontend-Subagent lieferte 3 Prozessverbesserungs-Vorschläge; 2 (jest-dom, git-stash) wurden nicht behandelt, einer nur zufällig (ein Auditor meldete dasselbe). Auch als „später vermerken" zugesagte ⚠️-Findings landeten zunächst nicht in AGENT_MEMORY.
  Warum: `implementing-scenario` hatte keinen Schritt, der Subagenten-Returns auf Vorschläge prüft / offene Punkte triagiert – sie hingen allein an der Orchestrator-Disziplin.
  Regel: Offene Punkte (Subagent-Vorschläge, zurückgestellte Findings) am Szenario-Ende explizit dem User vorlegen (umsetzen/vermerken/ignorieren) – nicht der Erinnerung überlassen. Gegenmaßnahme umgesetzt: Triage-Schritt in implementing-scenario Schritt 6.

- **[MITTEL] [PROZESS] [Session-Struktur] Abschluss-Artefakte von Hand statt via closing-session**
  Was: 077-Lessons-Header + AGENT_MEMORY-Zeile + Retro-Trigger wurden mitten im Flow von Hand geschrieben, ohne `closing-session` zu durchlaufen → Jenga-Score nicht neu berechnet, kein Session-Log, Retro-Trigger fehlte bis zum User-Hinweis.
  Warum: Der Abschluss wurde stückweise vorweggenommen statt als ein Schritt am Ende ausgeführt.
  Regel: Session-Abschluss-Artefakte (Lessons, AGENT_MEMORY-Stand, Jenga, Retro-Trigger, Log, Index) nur gebündelt via `closing-session` erzeugen – nie einzeln von Hand vorwegnehmen.

## Session 076 – 2026-06-10

- **[HOCH] [PROZESS] [Tooling] Datei-Rename brach einen funktionalen Pfad-Matcher, nicht nur Links**
  Was: Die docs/-Umbenennung auf kebab-case hebelte eine Schutz-Regex (`DEPENDENCIES\.md$`) in `check-dependency-allowlist.py` aus – die zu schützende Datei wurde danach nicht mehr erkannt.
  Warum: Annahme, eine Referenz-Migration betreffe nur Text-/Doku-Links; funktionale Pfad-Logik (Regex-Guards, Datei-Reads, Globs in Hooks/Scripts) wurde nicht mitgedacht.
  Regel: Bei Datei-Renames nicht nur Text-Verweise, sondern auch funktionale Pfad-Matcher prüfen – und Verhalten verifizieren (Tests laufen lassen), nicht nur Link-Existenz.

- **[MITTEL] [PROZESS] [Tooling] Referenz-Migration muss alle Verweis-Formen abdecken**
  Was: Pass 1 fasste nur `docs/X.md`-Pfade; bare Referenzen ohne `docs/`-Präfix und Wildcards (`docs/CODING_GUIDELINE_*`) blieben zurück und mussten in zwei Nachläufen gefixt werden.
  Warum: Eine einzelne Grep-Klasse deckt nur ein Referenz-Format ab; das Projekt nutzt prefixed, bare und Wildcard-Verweise parallel.
  Regel: Vor einem Massen-Rename die Verweis-Formen quantifizieren (prefixed + bare + Wildcard) und die Migration mit Gegen-Grep über alle Klassen verifizieren.

- **[MITTEL] [TOOLING] [Agent-Prompt] `: ` in Agent-`description` bricht Registrierung stumm**
  Was: `workflow-auditor` tauchte nicht in `/agents` auf, weil seine `description:` ein `: ` (Doppelpunkt+Leerzeichen) enthielt – ungültiger unquoted YAML-Plain-Scalar; der Agent-Parser ist strikter als der Skill-Parser.
  Warum: Hypothese zunächst falsch verworfen, weil ein *Skill* dasselbe Muster toleriert – Vergleich über inkompatible Parser.
  Regel: In Agent-`description:` kein `: ` (sonst quoten). Bei „Agent fehlt in /agents" zuerst Frontmatter-YAML prüfen; Mechanismus-Hypothesen nur an gleichartig verarbeiteten Artefakten falsifizieren.

## Session 075 – 2026-06-09

- **[MITTEL] [PROZESS] [Doku] Strukturelle Skill-Änderung ohne Sync der abhängigen Dateien**
  Was: Nach der Entscheidung „Frontend-Subagent implementiert beide Schichten in einem Aufruf" wurde SKILL.md aktualisiert, aber die agent-description und die Spawn-Regel nicht gleichzeitig – der Widerspruch wurde erst im nächsten Review-Lauf gefunden.
  Warum: Änderungen an einem Dokument werden gedanklich als abgeschlossen betrachtet, ohne systematisch zu prüfen welche anderen Dateien dieselbe Information redundant halten.
  Regel: Bei strukturellen Änderungen (Spawn-Verhalten, Schicht-Reihenfolge, Agent-Aufruf-Anzahl) immer alle zugehörigen Dateien gleichzeitig prüfen: SKILL.md + agent-descriptions + Spawn-Regeln.

- **[GERING] [AGENT] [Review] Reviewer verwechselt Review-Prompt-Kontext mit Systemkontext**
  Was: Ein Review-Subagent meldete OVERLOAD-Findings für Inhalte die nur im SKILL.md stehen – weil dieselben Infos in meinem Review-Prompt als Kontext-Block übergeben wurden und der Reviewer glaubte, sie seien dauerhaft verfügbar.
  Warum: Review-Prompts enthalten bewusst Kontext-Informationen für den Reviewer; dieser kann diese nicht von produktiven SKILL.md-Inhalten unterscheiden wenn er keinen Hinweis auf den Prompt-Ursprung hat.
  Regel: Bei Reviewer-Findings die OVERLOAD auf Mechanismus-Erklärungen melden: prüfen ob die Information im Review-Prompt stand oder ob sie wirklich doppelt vorkommt.

## Session 074 – 2026-06-08

- **[HOCH] [AGENT] [Doku] Two-Pass-Replacement ohne longest-first Sortierung korruptiert IDs**
  Was: Subagent schrieb ein Python-Script für Temp-ID → finale-ID Rename, sortierte die Keys aber nur in Pass 1 (Temp→Temp-Schutz), nicht in Pass 2 (Temp→Final). Kurze Keys wie `ADR-TEMP-1` matchten in längeren (`ADR-TEMP-10`), ~30 IDs wurden korrupt.
  Warum: Two-Pass-Replacement ist ein nicht-triviales Muster – Sortierung muss in beiden Passes sichergestellt werden, aber Subagenten-Review prüft oft nur Korrektheit der Logik, nicht aller Edge Cases.
  Regel: Bei programmatischen String-Transformationen durch Subagenten immer einen Test-Run auf kleinem Subset verlangen und Output vor Anwendung auf das Gesamtdokument prüfen; bei Two-Pass-Replacement explizit longest-first in beiden Passes spezifizieren.

- **[MITTEL] [TOOLING] [Tooling] docs/reference/dependencies.md-Hook blockiert auch reine Refactoring-Edits**
  Was: Der Dependency-Prozess-Hook verhinderte String-Replace (`decisions.md` → `adr.md`) in docs/reference/dependencies.md – auch ohne Paketänderung.
  Warum: Hook prüft Dateiname, nicht Intent der Änderung.
  Regel: Bei Refactoring-Edits auf Hook-geschützten Dateien User vorab informieren, dass manuelle Anpassung nötig ist – nicht erst nach einem Deny feststellen.

## Session 073 – 2026-06-05

- **[MITTEL] [TOOLING] [Tooling] JSON vor SHA-256 normalisieren**
  Was: Frontend-Stryker-Hash war zwischen zwei identischen Läufen instabil – Mutanten 8 und 9 tauschten Array-Position im JSON.
  Warum: StrykerJS garantiert keine stabile Serialisierungsreihenfolge von Mutanten innerhalb einer Datei.
  Regel: Bei inhaltsbasierten SHA-256-Hashes über JSON immer normalisieren: `sort_keys=True` + stabile Sortierung aller relevanten Listen vor dem Hashing.

## Session 072 – 2026-06-05

- **[MITTEL] [TOOLING] [Tooling] Custom-Subagent in derselben Session nicht nutzbar**
  Was: Ein neu erstellter Custom-Subagent (`test-bidirectional`) konnte nicht via `subagent_type` aufgerufen werden – die Fehlermeldung "Agent type not found" kam erst beim Spawn-Versuch.
  Warum: Custom-Subagenten werden beim Session-Start geladen; Dateien die während einer laufenden Session in `.claude/agents/` abgelegt werden, werden erst nach Neustart registriert – das war in den Docs explizit dokumentiert, aber nicht vorab geprüft.
  Regel: Vor dem Erstellen eines Custom-Subagenten prüfen ob er in derselben Session verwendet werden soll – falls ja, stattdessen `general-purpose` mit denselben Instruktionen im Prompt nutzen.

- **[GERING] [QUALITÄT] [Tooling] Attestierungs-Hash über Rohdaten, nicht abgeleitete Werte**
  Was: Erster Entwurf von `qa-check.py` hashte den Score-String (`"98.5%"`) statt den Report-Inhalt – ein Subagent hätte den Hash durch Übergabe eines manipulierten Score-Strings fälschen können.
  Warum: Convenience: Score lag als String bereits vor; Implikation für Fälschbarkeit wurde erst auf User-Nachfrage analysiert.
  Regel: Attestierungs-Hashes immer über die primäre Datenquelle (Dateiinhalt, Rohdaten) berechnen, nie über abgeleitete Werte – abgeleitete Werte sind fälschbar ohne die Quelle zu kennen.

## Session 071 – 2026-06-04

- **[HOCH] [AGENT] [Doku] Dateiinhalt ohne Verifikation zitiert**
  Was: Die Zeichenfolge "Bei Löschen, Archivieren, Überschreiben" wurde zweimal als konkretes Zitat aus einer Datei präsentiert (erst docs/guidelines/coding-guideline-ux.md, dann CLAUDE.md) — sie existiert in keiner der beiden.
  Warum: Schlussfolgerung aus dem Kontext als Zitat präsentiert, ohne Read-Tool-Verifikation.
  Regel: Vor dem Zitieren einer konkreten Zeichenfolge aus einer Datei immer mit Read-Tool verifizieren — Paraphrasen und Schlussfolgerungen sind kein Zitat.

- **[MITTEL] [PROZESS] [Gherkin] Szenarien-Reihenfolge im Workshop nicht korrekt angewandt**
  Was: Neue Szenarien ohne Backend-Interaktion (Feld-Init, Abbrechen) wurden nach dem bestehenden "Zutat anlegen"-Szenario eingefügt statt davor.
  Warum: Die Sortierregel "trivialster zuerst" wurde nicht auf Backend-Unabhängigkeit als Komplexitätskriterium angewandt.
  Regel: Szenarien ohne Backend-Interaktion kommen vor Szenarien mit mutierenden Server-Anfragen — gilt auch beim Einfügen in bestehende Feature-Files.

## Session 070 – 2026-06-04

- **[MITTEL] [TOOLING] [Agent-Prompt] Hintergrund-Subagenten scheitern an Edit/Write-Permissions**
  Was: A8- und E1-Subagenten wurden mit `run_in_background: true` gestartet und konnten keine Dateien editieren, obwohl der User mündlich Freigabe erteilt hatte.
  Warum: Hintergrund-Agenten haben keinen interaktiven Bestätigungskanal – Permission-Prompts für Edit/Write können nicht an den User weitergeleitet werden.
  Regel: Subagenten die Dateien editieren müssen als Vordergrund-Agenten starten (kein `run_in_background: true`); alternativ relevante Pfade vorab in `settings.json` unter `permissions.allow` eintragen.

---
