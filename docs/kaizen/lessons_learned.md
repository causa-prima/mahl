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

## Session 065 – 2026-04-18

- **[MITTEL] [TOOLING] [TS-Code] test.fail() läuft durch und timeoutet statt sofort zu überspringen**
  Was: `test.fail('name', fn)` in Playwright führt den Test-Body aus und timeoutet (30s), wenn das Feature noch nicht implementiert ist – Exit-Code 1 wie bei echtem Fehler.
  Warum: `test.fail()` markiert einen erwarteten Assertion-Fehler, nicht einen erwarteten Nicht-Lauf; Timeouts zählen nicht als „erwarteter Fehler".
  Regel: Für „noch nicht implementiert"-Tests immer `test.skip` verwenden, nie `test.fail`.

- **[GERING] [TOOLING] [TS-Code] toBeInTheDocument() ohne jest-dom-Setup verwendet**
  Was: `expect(...).toBeInTheDocument()` scheitert mit "Invalid Chai property", weil `@testing-library/jest-dom` nicht eingebunden ist.
  Warum: Matcher aus der Testing-Library-Dokumentation sind nicht standardmäßig verfügbar.
  Regel: Vor `toBeInTheDocument()` prüfen ob jest-dom im Setup-File registriert ist; sonst `findByRole` oder `findByText` verwenden (werfen bei Nicht-Vorhandensein von sich aus).

- **[MITTEL] [QUALITÄT] [TS-Code] Stryker-Survivor auf useQuery-Default `= []` nicht testbar ohne Loading-State-Infrastruktur**
  Was: Die Mutation `= []` → `= ["Stryker was here"]` überlebte, weil MSW immer Daten liefert und der Default nie aktiv ist.
  Warum: Der Default-Wert dient als TypeScript-Null-Safety, ist aber erst nach Einführung eines Loading-State-Tests killbar.
  Regel: Solche Survivor bewusst mit Kommentar supprimieren (`-- Default [...] nie getestet: data ist während Tests nie undefined [...]. Entfällt wenn Loading-State-Szenario implementiert ist.`) – nicht stillschweigend belassen.

## Session 064 – 2026-04-18

- **[MITTEL] [AGENT] [Tooling] retro_report.py-Cluster vor CM-Vorschlag nicht einzeln geprüft**
  Was: `[MITTEL][PROZESS][Tooling] 2×` als Cluster gemeldet → CM "Hook-Tests nach Änderungen" vorgeschlagen, ohne zu prüfen dass die beiden Einträge (S048: Edit-ohne-Read; S060: Hook-Tests) semantisch verschieden sind.
  Warum: Cluster-Label als inhaltliche Aussage übernommen statt die Einzel-Einträge zu lesen.
  Regel: Retro-Script-Cluster sind Tag-Kombinationen, keine semantischen Gruppen – immer die Einzel-Einträge lesen bevor ein Maßnahmenvorschlag formuliert wird.

- **[MITTEL] [PROZESS] [Skill-Nutzung] BEWÄHRT-Prüfung ohne Session-File-Lektüre durchgeführt**
  Was: CM2 (Ad-hoc-Bash) als BEWÄHRT-Kandidat vorgeschlagen, obwohl die meisten Sessions keine Coding-Sessions mit Test-/Build-Befehlen waren – erst User-Nachfrage hat das aufgedeckt.
  Warum: INDEX.md-Kurzfassungen genutzt statt die relevanten Session-Dateien zu lesen, wie der Kaizen-Skill es vorschreibt.
  Regel: Bei BEWÄHRT-Prüfung immer die gefilterten Session-Dateien lesen (nicht nur INDEX) – nur so ist erkennbar ob die Maßnahme wirklich 3× in relevantem Kontext beobachtet wurde.

---
