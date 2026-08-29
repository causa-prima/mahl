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

## Session 127 – 2026-08-29

- **[MITTEL] [AGENT] [Doku] LL-S127-1 – Umzug eines Eintrags begonnen, ohne den Mechanismus zu klären – Zwischenzustand fiel still aus dem Parser**
  Quelle: Orchestrator
  Was: Beim Verschieben von CM-S124-1 und CM-S078-2 in die BEWÄHRT-Sektion setzte ich zweimal einen Platzhalter an die Stelle der Überschrift – eine Operation, die den Rumpf gar nicht bewegt. Beide Male musste ich zurückrudern. Zwischen den Schritten stand der Eintrag ohne Überschrift in der Datei; retro_report.load_cm hätte ihn dort nicht mehr als Maßnahme gesehen, ohne dass etwas fehlgeschlagen wäre.
  Warum: Ich habe begonnen, bevor feststand, wie die Operation überhaupt ausführbar ist: Das Edit-Werkzeug kann nicht verschieben, der Block muss zwangsläufig einmal gelöscht und einmal neu geschrieben werden. Statt das einmal zu entscheiden, rollte ich die Kostenfrage mehrfach neu auf und begann zwischendurch Teilschritte, die zum Ziel nichts beitrugen.
  Regel: Vor dem ersten Schritt eines mehrschrittigen Umbaus den vollständigen Ablauf festlegen: Welche Operationen kann das Werkzeug, und welche Zwischenzustände entstehen dabei? Bei einem maschinell geparsten Dokument gilt das doppelt – ein Zwischenzustand, in dem ein Eintrag seine Kopfzeile verloren hat, fällt still aus der Auswertung, statt laut zu scheitern.

- **[MITTEL] [PROZESS] [Kommunikation] LL-S127-2 – Maßnahme aus der Fehlerbeschreibung abgeleitet, ohne die Entstehungsumstände zu kennen**
  Quelle: User
  Was: Für LL-S124-4 (Befund aus einer Subagenten-Liste verloren) schlug ich in der Retro einen Pflichtschritt in review-code und implementing-scenario vor: eingehende Befunde in einer sichtbaren Tabelle führen. Der User ergänzte, dass der Fall in Ad-hoc-Arbeit ohne laufenden Skill entstand, verschärft durch ein /compact nach einer Budget-Unterbrechung. Die Maßnahme hätte damit an einer Stelle gegriffen, an der der Fehler gar nicht entstanden war; sie ist entfallen und der Impact des LL wurde auf MITTEL zurückgenommen.
  Warum: Der LL-Text beschreibt den Ausgang, nicht die Umstände. Ich habe die Maßnahme am Symptom entworfen und dabei die Entstehungswege nie aufgezählt – die Frage, ob überhaupt ein Skill lief, kam nicht vor. In der Retro ist das systematisch, weil dort Maßnahmen aus Einträgen abgeleitet werden, deren Kontext Sessions zurückliegt und im Text nicht steht.
  Regel: Bevor in der Retro aus einem LL eine Maßnahme abgeleitet wird, die Entstehungsumstände klären: Lief ein Skill oder war es Ad-hoc-Arbeit? Gab es eine Unterbrechung, eine Kontext-Verdichtung, mehrere parallele Quellen? Steht das nicht im Eintrag und ist es nicht rekonstruierbar, beim User nachfragen – eine Maßnahme am falschen Ort kostet dauerhaft Prozessgewicht und lässt die echte Ursache offen.
  CM-Bezug: CM-S095-2
