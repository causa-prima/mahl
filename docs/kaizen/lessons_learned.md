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
