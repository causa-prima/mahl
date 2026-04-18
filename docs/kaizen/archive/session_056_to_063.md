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

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/PROCESS.md

Vor dem Eintrag prüfen: Gab es ein falsches Agenten-Verhalten das wieder auftreten kann? Nein → kein Eintrag (Infra-Wissen → DEV_WORKFLOW.md / Config). Details: docs/kaizen/PROCESS.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/PROCESS.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 063 – 2026-04-17

- **[HOCH] [AGENT] [Tooling] Hypothesen nicht als "bekannte Probleme" framen**
  Was: Stryker-0%-Score wurde ohne Quelle als "bekanntes Stryker.NET / WebApplicationFactory Kompatibilitätsproblem" bezeichnet – der User musste korrigieren, dass die alte Version (NUnit) funktioniert hatte.
  Warum: Plausible Erklärung wurde mit verifizierten Fakten gleichgesetzt; "klingt bekannt" ≠ "ist dokumentiert".
  Regel: Hypothesen explizit als Hypothesen benennen ("meine Vermutung: …"), empirisch verifizieren (manuelle Route-Test, Stryker-Versionsprüfung), erst dann als Ursache kommunizieren.

- **[MITTEL] [PROZESS] [Doku] Guidelines entstehen nach Features – Retrofit-Workshop einplanen**
  Was: `CODING_GUIDELINE_UX.md` wurde erst nach dem ersten gherkin-workshop für US-904 eingeführt – die Feature-File deckt keine UX-Anforderungen ab (z.B. Leer-Zustand ohne Erklärungstext).
  Warum: Skill-Inputs werden nicht aktualisiert wenn neue Richtlinien eingeführt werden.
  Regel: Nach Einführung einer neuen Guideline prüfen welche Skills sie lesen sollten – und ob bestehende Feature-Files einen Retrofit-Workshop brauchen.

---

## Session 061 – 2026-04-17

- **[HOCH] [AGENT] [Tooling] Annahmen über externes Systemverhalten nicht als Fakten präsentieren**
  Was: Zweimal wurden falsche Behauptungen über Claude Codes Permission-System als gesichertes Wissen präsentiert – erst musste der User aktiv nachfragen, bevor recherchiert wurde.
  Warum: Training-Wissen über Tool-Verhalten wird mit dokumentiertem Verhalten verwechselt; fehlende Unterscheidung zwischen "ich glaube" und "ich habe verifiziert".
  Regel: Behauptungen über das Verhalten externer Tools (Claude Code, APIs, Frameworks) immer mit "ich glaube" qualifizieren und sofort Verifizierung anbieten – nicht auf Nachfrage warten.

---

## Session 062 – 2026-04-17

- **[GERING] [QUALITÄT] [Tooling] replace_all trifft Konstantendefinition selbst**
  Was: Bei `_ALLOW_REASON`-Extraktion wurde `replace_all=True` versucht – hätte die frisch eingefügte Definition `_ALLOW_REASON = "..."` zu `_ALLOW_REASON = _ALLOW_REASON` umgeschrieben.
  Warum: `replace_all` ersetzt alle Vorkommen des Strings, einschließlich der Neudefinition die denselben Literal-String enthält.
  Regel: Vor `replace_all` prüfen ob der zu ersetzende String auch in der Konstantendefinition vorkommt. Falls ja: einzelne, gezielte Ersetzungen verwenden.

- **[MITTEL] [AGENT] [Review] Reviewer-Finding mit falscher Regex-Semantik nicht validiert**
  Was: Subagent behauptete `(?![\w:])` würde `\n`/`\t` nicht matchen (Finding #4, npm test). Das ist falsch – `\n` ist kein `[\w:]`, der negative Lookahead greift korrekt. Die vorgeschlagene Alternative `(?:\s|$)` hätte außerdem eine Regression erzeugt.
  Warum: Reviewer-Analyse hat Negativ-Lookahead-Semantik falsch interpretiert; die Behauptung wurde nicht vor der Bewertung verifiziert.
  Regel: Regex-Behauptungen von Review-Agenten immer selbst nachvollziehen. Insbesondere: Negativ-Lookahead `(?!X)` matcht wenn `X` NICHT folgt – `\n` ist kein `[\w:]`, also matcht es.

---

## Session 060 – 2026-04-16

- **[MITTEL] [PROZESS] [Tooling] Hook-Tests nach Hook-Änderungen sofort prüfen**
  Was: Nach Änderungen an WRONG_APPROACH/ALLOW-Patterns in check-bash-permission.py waren bestehende Tests in test-bash-permission.py veraltet (npx via cmd.exe als allow statt deny erwartet).
  Warum: Tests spiegeln den alten Zustand wider — beim Umbau von ALLOW → WRONG_APPROACH werden sie nicht automatisch angepasst.
  Regel: Nach jeder Änderung an WRONG_APPROACH_PATTERNS oder ALLOW_PATTERNS sofort test-bash-permission.py öffnen und betroffene Testfälle aktualisieren.

- **[GERING] [QUALITÄT] [Doku] Progressive Disclosure bei Guidelines explizit definieren**
  Was: UX-Guideline-Verlinkung wurde zunächst pauschal für TypeScript gesetzt, dann auf src/components/ und src/pages/ eingeschränkt.
  Warum: "TypeScript" ist zu breit — auch Services und Domain-Code sind TypeScript, aber UX-Regeln gelten nur für UI-Komponenten.
  Regel: Bei neuen Guidelines vor der Verlinkung den genauen Trigger definieren (Dateipfad, Dateityp, Kontext) — nicht die Sprache, sondern die Rolle der Datei ist das Kriterium.

---

## Session 059 – 2026-04-15

- **[MITTEL] [QUALITÄT] [Doku] Positive Umformulierung verliert implizite Information**
  Was: Mehrere Edits beim Umformulieren negativer Anweisungen in positive wurden abgelehnt, weil Signalwörter oder Nuancen verloren gingen (boolean-Flags als Signal, "auch auf Strings", "unnötig" ≠ "erlaubt").
  Warum: Positive Formulierungen fokussieren auf das Korrekte und lassen dabei Warnsignale weg, die für Agenten als Trigger wichtig sind.
  Regel: Vor jedem positiven Umformulieren prüfen: Gehen implizite Signale oder Nuancen verloren? Falls ja, explizit einbauen oder die negative Formulierung beibehalten.

---

## Session 058 – 2026-04-15

- **[MITTEL] [AGENT] [Doku] Regelgültigkeit vor Dokumentieren prüfen**
  Was: Die ETag-Guideline wurde zunächst mit "alle mutierbaren Ressourcen" formuliert – zweimal vom User korrigiert, weil der Begriff falsch war (ETags gelten für alle GET-Endpoints, unabhängig von Mutierbarkeit).
  Warum: Terminologie aus der Diskussion ("mutable endpoints") wurde unreflektiert übernommen, ohne die tatsächliche Reichweite der Regel zu prüfen.
  Regel: Vor dem Formulieren einer Regel den exakten Gültigkeitsbereich bestimmen – wer ist betroffen, welche Ausnahmen gibt es? Erst dann schreiben.

- **[MITTEL] [AGENT] [Doku] Entscheidung nicht dokumentieren, bevor der Entscheidungsbaum vollständig ist**
  Was: Beim ETag-Thema wurde fast dokumentiert, bevor die Collection-ETag-Frage geklärt war – User hat das Speichern abgebrochen.
  Warum: Zu früh in den "Dokumentieren"-Modus gewechselt.
  Regel: Decisions.md erst beschreiben, wenn alle Teilentscheidungen getroffen sind – nicht nach dem ersten "Ja".

---

## Session 057 – 2026-04-15

- **[GERING] [PROZESS] [Agent-Prompt] Review-Prompt übernahm nicht explizit vorher geäußerten Refactoring-Wunsch**
  Was: Der User hatte vor der Review-Beauftragung erwähnt, dass ein späteres Review mit Refactoring folgen soll – der Review-Prompt enthielt diesen Scope dennoch nicht.
  Warum: Der Agent hat den früheren Kontext nicht in den Prompt übertragen; Agenten reviewen nur was explizit gefragt wird.
  Regel: Wenn der User in der laufenden Unterhaltung Scope für ein Review genannt hat (z.B. "inkl. Refactoring"), diesen Scope beim Formulieren des Review-Prompts explizit aufnehmen – nicht davon ausgehen, dass der Agent ihn kennt.

- **[HOCH] [AGENT] [TS-Code] Agenten schlagen nicht proaktiv HTTP-Level-Mocking vor**
  Was: MSW als Mocking-Strategie wurde erst auf User-Initiative eingeführt – mehrere Sessions lang wurde kein Test für `ingredientsApi.ts` geschrieben, und bei der Diskussion über Stryker-Coverage wurde zunächst `vi.stubGlobal('fetch', ...)` als Option B geframt, nicht MSW.
  Warum: Agenten wählen den direktesten Weg zur Lösung des unmittelbaren Problems (NoCoverage-Fix), ohne das übergeordnete Ziel (Best-Practice-Testarchitektur) aktiv anzuwenden. Das Ziel "Software nach Lehrbuch entwickeln" ist nicht operationalisiert genug, um Agenten zuverlässig zu leiten.
  Regel: Beim Einrichten von Tests für HTTP-kommunizierende Module immer MSW als ersten Kandidaten evaluieren – nicht `vi.mock` auf Funktionsebene oder `stubGlobal`. Gilt auch retrospektiv: vorhandene `vi.mock`-Tests auf HTTP-Ebene migrationswürdig markieren.

---

## Session 056 – 2026-04-14

- **[MITTEL] [PROZESS] [Doku] Architekturentscheidung braucht mehrere Iterationen bis zur richtigen Abstraktion**
  Was: Die Entscheidung plain Promise vs. ResultAsync entwickelte sich über viele Runden – erster Ansatz (throw für Domain-Fehler im Service) war semantisch falsch und musste korrigiert werden.
  Warum: Komplexe Architektur-Trade-offs (React Query, TypeScript structural typing, Poka-yoke) wurden schrittweise durch User-Fragen aufgedeckt, nicht von Anfang an vollständig durchdacht.
  Regel: Bei Framework-Integrationsentscheidungen zuerst die semantische Korrektheit prüfen (ist ein Fehler ein Wert oder eine Ausnahme?), dann die technische Umsetzung ableiten – nicht umgekehrt.

- **[GERING] [TOOLING] [Tooling] CM-Status nach Umsetzung nicht sofort aktualisiert**
  Was: Die Bash-Permission-CM wurde in der Retro auf OFFEN gesetzt und in derselben Session umgesetzt, aber der Status in countermeasures.md blieb bis zum Session-Abschluss auf OFFEN.
  Warum: AGENT_MEMORY wurde noch nicht aktualisiert; CM-Status-Update fehlte im Implementierungsflow.
  Regel: Beim Abschließen einer CM-Umsetzung sofort countermeasures.md auf AKTIV setzen, nicht auf den Session-Abschluss warten.
