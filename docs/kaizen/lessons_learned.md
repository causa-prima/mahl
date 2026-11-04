# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in docs/tech-debt.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[IMPACT] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User | Subagent | Orchestrator   (Herkunft des Eintrags)
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).
    CM-Bezug: <CM-ID> | neu     (Pflicht bei KRITISCH/HOCH, sonst optional)

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.
    CM-Bezug: neu

  Zum Feld CM-Bezug: Die ID der Maßnahme, an die das Finding anschließt, oder `neu`, wenn
  dafür erst eine entstehen muss (die ID muss in countermeasures.md existieren). Pflicht bei
  KRITISCH und HOCH; bei MITTEL/GERING optional – besteht ein Bezug, gehört er hinein, sonst
  entfällt die Zeile. `lessons.py add --cm-bezug` erzwingt und prüft es.
  (Zeilenanfang bewusst nicht „CM-Bezug:" – sonst zählt der Auswertungs-grep des kaizen-Skills
  diese Erklärung als Eintrag mit.)

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Impact:     KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Testing | Sonstiges

Alle Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (überall Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Impact/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 145 – 2026-11-04

- **[HOCH] [AGENT] [Kommunikation] LL-S145-1 – Befund per Namens- bzw. Regex-Zählung ausgegeben, ohne die Treffer anzusehen**
  Quelle: Orchestrator
  Was: In der S145-Retro meldete ich zur Testabdeckung von retro_report, die Kandidatenauswahl (_neue_kandidaten, _abgedeckte_kandidaten) sei ungetestet – gezählt hatte ich nur, wie oft die Funktionsnamen in der Testdatei vorkommen. Vier Tests über render_pattern deckten sie längst; der User entschied ‚G4 jetzt' auf dieser Grundlage. Ebenso stand ‚14 von 31 AKTIV-Maßnahmen ohne Kriterium' als Tatsache in process.md, gestützt auf eine grobe Regex; gemessen waren es 17 von 32.
  Warum: Die Zählung konnte indirekte Tests gar nicht sehen, und die Regex zählte frei formulierte Sätze mit – beide Prüfungen hätten beim Gegenteil gleich ausgesehen. Ich habe das Ergebnis weitergegeben, ohne eine Stichprobe der Treffer bzw. Nicht-Treffer anzusehen.
  Regel: Ein Befund aus einer Namens- oder Mustersuche wird erst ausgegeben, wenn mindestens ein Treffer und ein Nicht-Treffer im Kontext angesehen sind und die Frage beantwortet ist, ob die Suche den Fall überhaupt sehen könnte (indirekter Aufruf, andere Schreibweise). Bis dahin als grobe Schätzung kennzeichnen – und nie als Zahl in eine Doku schreiben.
  CM-Bezug: CM-S116-1

- **[HOCH] [AGENT] [Kommunikation] LL-S145-2 – Guard-Entwurf vorgeschlagen, ohne den Durchgangsweg der zu prüfenden Fälle nachzuverfolgen**
  Quelle: Orchestrator
  Was: Für den Poka-yoke zu CM-S070-1 (Review-Fix-Tests ohne Szenario) schlug ich in der S145-Retro eine Prüfung bei qa-check --verify gegen den Freigabe-Anker vor; der User gab das Bauen frei. Erst beim Nachlesen vor dem Bau zeigte sich: Ein Review-Fix läuft über einen eigenen Test-Review und bekommt einen eigenen Anker – die Prüfung hätte die gemeinten Tests nie gesehen.
  Warum: Ich hatte den Durchgangsweg nur als ‚nicht bis ins Detail nachgelesen' markiert, statt ihn vor dem Vorschlag nachzuverfolgen. Für ein Guard-Design verlangt das Prinzip einen Beleg je Dimension, kein Argument – die Dimension ‚Pfade' (welchen Weg nimmt der zu fangende Fall?) blieb ungeprüft.
  Regel: Vor jedem Guard- oder Gate-Vorschlag den Weg des Falls, den er fangen soll, im Skill bzw. Code bis zur geplanten Prüfstelle nachverfolgen: Erreicht der Fall die Stelle in dem Zustand, den die Prüfung sieht? Eine Unsicherheit dazu wird vor dem Vorschlag aufgelöst, nicht nur markiert.
  CM-Bezug: CM-S095-2
