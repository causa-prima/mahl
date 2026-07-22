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

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Impact:     KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Testing | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Impact/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 107 – 2026-07-22

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S107-1 – Retro-Auftakt-Sonde beim Retro-Start übersprungen**
  Quelle: Orchestrator
  Was: Die für den Retro-Beginn geplante blinde LL-Impact-Re-Rating-Sonde (OBS-S092-3, in AGENT_MEMORY „Nächste Prioritäten" vermerkt) lief nicht zu Beginn – `retro_report.py` (Schritt 2) lief davor; die Sonde wurde erst mitten in der Retro selbst nachgeholt.
  Warum: Die Sonde lebte nur als AGENT_MEMORY-Prosa; der `kaizen`-Skill hatte keinen Schritt, der retro-spezifische Auftakt-Items aus AGENT_MEMORY konsultiert und ausführt.
  Regel: Retro-/session-spezifische Auftakt-Aufgaben nicht nur als AGENT_MEMORY-Prosa parken – im Skill einen Schritt verankern, der solche Items zu Beginn zieht und abarbeitet. (Fix gelandet: Impact-Sanity-Check ist jetzt fester `kaizen`-Schritt 0.)

- **[MITTEL] [AGENT] [Kommunikation] LL-S107-2 – CM-BEWÄHRT-Evidenz vorgelegt ohne Zerlegung der Mechanismus-Aktivität**
  Quelle: Orchestrator
  Was: CM-S070-1 als BEWÄHRT-reif mit „6 sauberen Läufen" vorgelegt und freigeben lassen; erst tieferes Lesen des S104-Commits zeigte, dass das Blob-Anker-Gate für Backend bis S104 aus war → nur 2 valide Backend-Läufe. C1 musste nach bereits erteilter Freigabe revidiert werden.
  Warum: „Läufe fanden statt" nicht zerlegt in „war der wirksame Mechanismus (Gate) über die ganze Periode aktiv?" – die auffällige Lauf-Zahl fürs Ganze genommen.
  Regel: Vor einer CM-BEWÄHRT-/Wirksamkeits-Aussage prüfen, ob der steuernde Mechanismus über den **gesamten** Bewertungszeitraum aktiv war (Gate-off-Perioden zählen nicht) – Lauf-Zahl ≠ gate-gedeckte Lauf-Zahl.
  Bezug: CM-S095-2
