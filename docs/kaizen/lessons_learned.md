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

## Session 133 – 2026-09-25

- **[HOCH] [AGENT] [Kommunikation] LL-S133-1 – Treffer-Bestand per Klasse abgezogen statt gesichtet – und nur eine von zwei Datenquellen gelesen**
  Quelle: User
  Was: Für die Entscheidung über das Mengenangaben-Log (C1b) legte ich „13 Chronik-Treffer, 7 übrige, davon 3 echt“ vor und empfahl Streichen. Die 13 hatte ich als Klasse abgezogen, ohne einen davon im Kontext anzusehen, und falsch gezählt (tatsächlich 15/5). Der User fragte, was mit den restlichen 4 sei. Erst die Einzelsichtung zeigte: Seit dem Paket-Umzug in S129 schrieb der Hook still nach prozesscode/tmp statt .claude/tmp – das zweite Log mit 33 Einträgen hatte ich nie gelesen. Die vorgelegten Zahlen deckten nur die Zeit bis S129 ab und trugen eine Entscheidung des Users.
  Warum: Die Chronik-Klasse wirkte offensichtlich, also schien Sichten unnötig – genau der Fall aus dem Prinzip „Bestände werden gesichtet, nicht gefiltert“. Dazu kam, dass ich die Datenquelle für vollständig hielt, weil sie existierte und plausible Zahlen lieferte; ob der Schreiber noch dorthin schreibt, prüfte ich nicht.
  Regel: Bevor Zahlen aus einem Log eine Entscheidung tragen: prüfen, ob der Schreiber heute noch in genau diese Datei schreibt (Pfad im Code nachlesen, jüngster Eintrag datiert?), und jede abgezogene Klasse mit mindestens einer angesehenen Stichprobe belegen. Eine Klasse ohne gesichtetes Beispiel ist ein Filter, keine Sichtung.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S133-2 – Alternative mit einem Kostenargument verworfen, das für die eigene Empfehlung genauso galt**
  Quelle: User
  Was: Für A1 (erfasst statt behoben) empfahl ich eine Regel in CLAUDE.md und verwarf ein Pflichtfeld bei der Erfassung mit „verteuert jeden Eintrag“. Der User hielt dagegen, die Begründung müsse so oder so gedacht werden – der Aufwand sei derselbe. Das Argument trug nicht; das Pflichtfeld wurde umgesetzt und ist zudem der einzige Ort, den jede Erfassung passiert (beide Vorfälle entstanden mitten in der Session, nicht beim Abschluss).
  Warum: Ich habe die Kosten nur an der verworfenen Option benannt und nie gegen die empfohlene gehalten – dieselbe Form wie LL-S125-3 (Ausschlusskriterium nur an der neuen Option geprüft). Zudem habe ich die Entstehungswege der beiden Vorfälle nicht aufgezählt, sonst wäre die Platzierungsfrage anders ausgefallen.
  Regel: Ein Kostenargument gegen eine Alternative erst aussprechen, nachdem es an der empfohlenen Option gemessen ist. Trifft es beide gleich, trennt es die Optionen nicht. Bei der Frage, wo eine Maßnahme greifen soll, zuerst die Entstehungswege der Vorfälle aufzählen.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S133-3 – Aus einer einzigen Beobachtung eine Fallklasse gemacht**
  Quelle: User
  Was: Ich meldete, qa-check gebe „auch im Fehlerfall“ rund 200 Zeilen ADR-Liste aus. Gesehen hatte ich das genau einmal, bei einem ungültigen Hash. Auf die Rückfrage des Users („Was für Fehlerfälle?“) zeigte der Code: Die Liste kommt in jedem Lauf, gerade im Erfolgsfall – decisions check gab jede gültige Fundstelle aus. Die Verallgemeinerung hätte einen Fix nur für den Fehlerpfad nahegelegt, der am Problem vorbeigegangen wäre.
  Warum: Die Beobachtung passte zur vorhandenen Wrapper-Regel („im Fehlerfall nur das Nötige“), und die Formulierung der Regel lieferte die Kategorie gleich mit. Wann die Ausgabe entsteht, habe ich nicht nachgelesen, obwohl es zwei Zeilen Code waren.
  Regel: Eine einzelne Beobachtung als Einzelfall berichten („bei --verify mit ungültigem Hash gesehen“), bis die Bedingung im Code nachgelesen ist. Eine Aussage über „den Fehlerfall“ oder „jeden Lauf“ ist eine Allaussage und braucht die Stelle, die sie erzeugt.
  CM-Bezug: CM-S064-1

- **[MITTEL] [AGENT] [Kommunikation] LL-S133-4 – Entscheidungsfragen in Werkzeug- und Session-Jargon vorgelegt**
  Quelle: User
  Was: Viermal in einer Session musste der User nachfragen, worum es überhaupt ging: „C1b“ (was ist das Problem, was die Lösung?), „CLI-Verdrahtung wovon“, „E2/E3 – was geprüft, was sagen die Ergebnisse“, „Was ist CHECK 6?“. Jedes Mal hatte ich einen Befund mit internem Kurzlabel und Werkzeugbegriff vorgelegt, ohne Gegenstand, Problem und Bedeutung der Optionen zu erklären. Die Entscheidung verzögerte sich jeweils um eine Runde; bei C1b ging die frühere Erklärung zudem in einer langen Nachricht unter.
  Warum: Die Labels waren mir aus der laufenden Arbeit geläufig, und ich habe sie für geteiltes Wissen gehalten. Das Prinzip „Tracker-ID nie nackt nennen“ deckt nur Tracker-IDs ab – Befund-Labels, Werkzeug- und Prüfnamen fühlen sich nicht wie IDs an, tragen aber dasselbe Problem.
  Regel: Vor jeder Frage an den User prüfen, ob sie ohne Session-Kontext verständlich ist: Was ist der Gegenstand (ein Satz), was ist das Problem, was bedeutet jede Option? Selbst vergebene Labels (A1, C1b, CHECK 6) nur zusammen mit dieser Erklärung, nie allein. Entscheidungsfragen am Ende einer langen Nachricht gesammelt wiederholen.
