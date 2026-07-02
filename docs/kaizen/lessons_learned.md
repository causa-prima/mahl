# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in docs/tech-debt.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User | Subagent | Orchestrator   (Herkunft des Eintrags)
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Schwere/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 098 – 2026-07-02

- **[MITTEL] [TOOLING] [Sonstiges] LL-S098-1 – Prozess-Env für gespawnte Tools kann still überschrieben werden**
  Quelle: User
  Was: In der Playwright-`webServer.env` gesetztes `ASPNETCORE_ENVIRONMENT=E2E` wurde von `launchSettings.json` (`dotnet run` nutzt per Default das Launch-Profil) still auf `Development` überschrieben → der E2E-Reset-Endpoint war nie gemappt (404) → verwirrende Akkumulations-Debuggerei (ich konnte anfangs nicht erklären, warum ein Empty-State-Test grün war). Fix: `--no-launch-profile`.
  Warum: Angenommen, das im Runner gesetzte Env erreiche die App 1:1 – ohne zu prüfen, dass eine gelagerte Konfigurationsquelle (Launch-Profil) Vorrang hat.
  Regel: Hängt ein Mechanismus daran, dass eine Env-Variable/Config einen gespawnten Prozess erreicht, empirisch mit einer **lauten** Laufzeit-Assertion absichern, dass sie wirklich griff – nicht auf Propagierung vertrauen (gelagerte Config/Profile können lautlos gewinnen).

- **[MITTEL] [QUALITÄT] [C#-Code] LL-S098-2 – Provider-spezifische API direkt in Program.Main bricht den InMemory-Test-Host**
  Quelle: Orchestrator
  Was: Ein `MigrateAsync()`-Aufruf (EF-Relational) direkt in `Program.<Main>$` – hinter einem `if E2E`-Guard, der in Tests nie läuft – ließ **alle** 15 Backend-Integrationstests mit `FileNotFoundException` (Relational-Assembly) scheitern, weil der Test-Host (WebApplicationFactory, InMemory-Provider) beim JIT von `Main` alle Methodrefs auflösen muss, auch die des ungenommenen Zweigs.
  Warum: JIT ist per-Methode lazy, aber innerhalb einer Methode werden alle referenzierten Assemblies beim Kompilieren aufgelöst – ein untaken Branch schützt nicht.
  Regel: Provider-/Assembly-spezifische Aufrufe (Relational, Npgsql o.ä.), die nur unter einer bestimmten Umgebung laufen, nicht inline in `Program.Main` setzen, sondern in eine eigene Methode auslagern – deren Body JITtet erst beim tatsächlichen Aufruf, sodass Test-Hosts mit anderem Provider nicht am fehlenden Assembly scheitern.

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S098-3 – Fällige Infra-Schuld im Architektur-Check nicht proaktiv gefunden**
  Quelle: User
  Bezug: OBS-S090-5 (Materialisierung der dort vorhergesagten Lücke)
  Was: TD-S083-5 (E2E-DB-Reset) war laut eigenem Trigger („vor weiteren E2E-abhängigen Szenarien") fällig, wurde im Schritt-0-Architektur-Check aber nicht gefunden – erst reaktiv, als der E2E-Test an DB-Residuen scheiterte (Debugging-Kosten). Obwohl run-1 erkennbar E2E-lastig war, habe ich `tech-debt.md` in Schritt 0 nie geöffnet; AGENT_MEMORY listete andere TDs (S094-1/S077-1), nicht dieses.
  Warum: Schritt 0 hat keinen formalen `tech-debt.md`-Scan; das TD-Surfacing hing allein an AGENT_MEMORY, das dieses Infra-TD nicht trug – exakt der von OBS-S090-5 beschriebene Fall (Schuld ohne Szenario-Bezug fällt durchs Raster).
  Regel: Im Architektur-Check bei szenario-relevantem Kontext (z.B. E2E-lastiger Lauf) aktiv `tech-debt.md` nach fälliger Schuld durchsuchen (Trigger-Text lesen), statt sich allein auf die AGENT_MEMORY-Prioritätenliste zu verlassen. (Formalisierung offen → Retro, OBS-S090-5.)

## Session 097 – 2026-07-01

- **[MITTEL] [QUALITÄT] [TDD] LL-S097-1 – Regressionstest mit zufällig deckungsgleicher Reihenfolge maskierte echten Sortier-Bug**
  Quelle: User
  Was: `group_runs()` (next_run.py) sortierte Läufe nach Datei-Position des ersten Auftretens statt nach Run-Nummer → das reale `ingredients.feature` (run-7 steht als erstes Szenario in der Datei, hat aber eine höhere Nummer/spätere Build-Priorität als run-1) hätte fälschlich `run-7` als „nächsten Lauf" empfohlen. Die eigene Testfixture hatte Run-Nummern zufällig in Datei-Reihenfolge vergeben, sodass kein Test den Bug zeigte – der User bemerkte ihn erst beim Ausprobieren des echten Outputs.
  Warum: Beim Schreiben der Regressionstests für Sortierlogik mit zwei Kandidaten-Ordnungen (Position im Quelltext vs. deklarierte Sequenznummer) wurde nur eine „normale" Fixture gebaut, keine mit absichtlich divergierenden Ordnungen.
  Regel: Tests für Sortier-/Reihenfolge-Logik mit mehreren möglichen Ordnungskriterien immer mit einer Fixture absichern, in der die Kriterien **auseinanderfallen** – eine Fixture, die zufällig beide Ordnungen erfüllt, beweist nichts.

## Session 096 – 2026-06-30

- **[GERING] [AGENT] [Review] LL-S096-1 – Reviewer-/eigene Behauptungen ungeprüft weitergereicht**
  Quelle: User
  Was: FlowReview5s „P1 ≈ 1 Zeile"-Kostenschätzung als billigen Fix präsentiert (der Re-Park-Trail existiert gar nicht) und eine konstruierte OBS-Überschneidung (S092-2↔S094-1) behauptet – beides vom User korrigiert.
  Warum: Behauptung nicht am echten Datenmodell/Sachverhalt verifiziert, bevor sie weitergereicht wurde.
  Regel: Reviewer-Aussagen UND eigene Querbezüge vor dem Weiterreichen am konkreten Artefakt prüfen (Datenmodell/Format/Inhalt), nicht plausibilitäts-halber übernehmen.

## Session 095 – 2026-06-24

- **[MITTEL] [PROZESS] [Doku] LL-S095-1 – Zustandswechsel nur als Prosa-Notiz, nicht im geparsten Status-Feld**
  Quelle: Orchestrator
  Was: Beim Wiederaufgreifen von OBS-S085-3 wurde eine Notiz „Status → IN BEOBACHTUNG" ergänzt, das eigentliche `- Status:`-Feld blieb aber auf „UMGESETZT" → das Archivierungs-Skript keyte aufs Feld und verschob den Eintrag fälschlich ins Archiv (manuelle Rückholung nötig).
  Warum: Der menschenlesbare Zusatz wurde mit der maschinell geparsten Wahrheit verwechselt; beide drifteten auseinander.
  Regel: Ändert sich der Zustand eines getrackten Eintrags, das **kanonische, maschinell geparste Status-Feld selbst** ändern – eine widersprechende Prosa-Notiz genügt nicht und führt Skripte in die Irre.

- **[MITTEL] [AGENT] [Kommunikation] LL-S095-2 – BEWÄHRT-Hochstufung auf Evidenz, die das Gemessene nicht isoliert**
  Quelle: User
  Was: CM-S070-4 (Subagent-Tooling-Feedback) als BEWÄHRT vorgeschlagen, gestützt auf „OBS Quelle: Agent" – das unterscheidet aber Subagent- nicht von Orchestrator-Feedback, trägt die „bewährt"-Behauptung also nicht; vom User zurückgewiesen.
  Warum: „Arbeit fand statt" mit „die Maßnahme wurde nachweislich wirksam ausgeübt" verwechselt – die Evidenz isolierte nicht, was die Maßnahme kontrolliert.
  Regel: Vor einer BEWÄHRT-Hochstufung prüfen, ob die Evidenz genau das Verhalten isoliert, das die Maßnahme steuern soll – sonst AKTIV lassen und die Beobachtbarkeit erst herstellen.
  Bezug: CM-S064-1

- **[MITTEL] [PROZESS] [Doku] LL-S095-3 – Gerade etablierte Regel im selben Edit selbst verletzt**
  Quelle: User
  Was: Beim Dokumentieren der Modell-Maßnahme eine frische `(OBS-S085-8/S093-2)`-Referenz in die *stabile* `implementing-scenario`-SKILL geschrieben – exakt der stabil↛volatil-Verstoß, den dieselbe Session als Regel/CM etablierte.
  Warum: Die neue Regel wurde als „Thema für andere Stellen" behandelt, nicht auf den eigenen, gleichzeitigen Edit angewandt.
  Regel: Eine in derselben Session etablierte Regel sofort auf die eigenen Dokumentations-Edits anwenden – die nächste Gelegenheit, sie zu brechen, ist der Edit, der sie beschreibt.
  Bezug: CM-S095-1

- **[GERING] [PROZESS] [Skill-Nutzung] LL-S095-4 – Rückfall vs. Abdeckungs-Erweiterung fehlklassifiziert**
  Quelle: User
  Was: LL-S094-1 zunächst als „Rückfall" von CM-S070-5 notiert; tatsächlich deckte die Checkliste ihre Klassen korrekt ab und die Formular-UX-Baseline war eine nie enumerierte angrenzende Sub-Klasse (kein Agenten-Fehlverhalten) → Umformulierung nötig.
  Warum: „Problem trat erneut auf" pauschal als Rückfall gewertet, ohne zu prüfen, ob die Maßnahme den Fall je abdeckte.
  Regel: In der Retro „Maßnahme existierte, wurde aber nicht angewandt" (Rückfall) von „neue, nie abgedeckte Sub-Klasse" (Abdeckungs-Erweiterung) trennen – nur Ersteres ist ein Rückfall.

---
