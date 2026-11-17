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

## Session 149 – 2026-11-16

- **[HOCH] [QUALITÄT] [Hook/Script] LL-S149-1 – Ausnahme in einem neuen Guard ohne Bestandsfall eingebaut – inkonsistent begründet**
  Quelle: Orchestrator
  Was: Im neuen Check gegen unsichtbare Zeichen in C#/TS-Tests (S149-Retro) nahm ich Variationsselektoren aus, für den Fall eines Emojis im Test. Die C#/TS-Tests enthalten kein Emoji, und dieselbe Begründung (Verlust ändert den sichtbaren Text, Test wird laut rot) hätte für Nullbreiten-Verbinder und Keycaps gegolten, die der Check sperrte. Der code-quality-auditor fand die Inkonsistenz; die Ausnahme ist entfernt.
  Warum: Ich entwarf die Ausnahme aus einem vorgestellten Fall, nicht aus dem Bestand – obwohl ich den Bestand im selben Schritt durchsucht hatte und er keinen Treffer in C#/TS lieferte. YAGNI war bekannt, wurde beim Guard-Bau aber nicht angelegt.
  Regel: Eine Ausnahme in einem Guard braucht einen Fall im Bestand; ohne ihn keine Ausnahme. Mit ihm wird jedes Element, für das dieselbe Begründung gilt, gleich behandelt – und ein Test schreibt die Entscheidung fest.
  CM-Bezug: CM-S047-1

## Session 150 – 2026-11-17

- **[HOCH] [QUALITÄT] [Testing] LL-S150-1 – Review-Fix machte eine C#-Assertion per ?. wirkungslos**
  Quelle: Orchestrator
  Was: Runde 1 des Reviews zur SPA-Auslieferung verlangte, ContentType!.MediaType null-sicher zu prüfen. Der Fix ContentType?.MediaType.Should().Be("text/html") prüfte bei fehlendem Header gar nichts mehr: ?. bricht die ganze Kette samt Assertion ab. Weder Orchestrator noch die Auditoren von Runde 2 bemerkten es; erst der Testqualitäts-Auditor in Runde 3.
  Warum: Null-Sicherheit wurde als Lesbarkeitsfrage behandelt, nicht als Frage, ob die Assertion noch anschlagen kann. Die Gegenprobe (Header weglassen → rot?) lief für diesen Satz nie, weil die Änderung als reines Aufräumen nach der Freigabe galt.
  Regel: In C#-Tests kein ?. vor .Should(): den Wert klammern ((x?.Y).Should()…), damit null in die Assertion läuft. Jede Änderung an einer Assertion – auch eine kosmetische – mit der Frage prüfen, ob sie im Fehlerfall noch rot würde (coding-guideline-csharp.md#CGC-null-conditional-assertion).
  CM-Bezug: CM-S101-1

- **[MITTEL] [QUALITÄT] [C#-Code] LL-S150-2 – SPA-Fallback unter /api verwandelte 405 in 404**
  Quelle: Orchestrator
  Was: Für die SPA-Auslieferung (ADR-S150-2) gab ich dem Backend-Subagenten in der PLANUNG MapFallback("/api/{**rest}", NotFound) vor. Der Fallback nimmt jede Methode an und gewann dadurch auch bei bekanntem Pfad mit falscher Methode: PUT /api/ingredients lieferte 404 statt 405. Erst der Korrektheits-Auditor meldete es, der RED-Test im Fix-Auftrag belegte es.
  Warum: Beim Entwurf zählte nur der gewünschte Fall (unbekannter API-Pfad → 404), nicht, welche bestehenden Antworten des Routings ein Catch-all-Endpoint überdeckt. Kein Test hielt 405 fest, deshalb blieb die Suite grün.
  Regel: Wer einen Catch-all- oder Fallback-Endpoint einführt, listet vorher die Negativ-Antworten, die das Routing bisher selbst gab (404, 405), und hält sie per Test fest, bevor der Fallback entsteht.
