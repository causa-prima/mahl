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

## Session 140 – 2026-10-23

- **[MITTEL] [AGENT] [Skill-Nutzung] LL-S140-1 – Entscheidung in den Drain geschoben, obwohl der Entscheider anwesend war**
  Quelle: User
  Was: In der Retro schlug ich für den Mechanismus zu CM-S095-2 eine OBS vor, die drei Kandidaten in den Drain gibt. Der User fragte, warum nicht direkt entschieden werde; er saß in der Retro, und die Abwägung brauchte keine Recherche. Die Entscheidung fiel danach in derselben Runde.
  Warum: Ich folgte der Kurzfassung der Weiche im kaizen-Skill ('Antwort steht aus (mehrere ernsthafte Kandidaten) → OBS'). Sie hatte die Bedingung aus process.md weggekürzt, dass die Abwägung eigene Recherche braucht. Nach der Aufschubgrund-Regel gab es zudem keinen gültigen Grund: 'User' gilt erst nach Rückfrage.
  Regel: Bevor etwas in den Drain geht: Kann es jetzt entschieden werden – ist der User da und braucht die Abwägung keine Recherche? Dann mit Empfehlung vorlegen. Eine Weiterleitung braucht einen Aufschubgrund wie jede Erfassung.
  CM-Bezug: CM-S133-2

- **[HOCH] [AGENT] [Kommunikation] LL-S140-2 – Maßnahme aufs Erfassen gerichtet, obwohl der eigene Beleg zeigte, dass das Erfassen nicht die Lücke war**
  Quelle: User
  Was: Für LL-S139-1/-3 (Werkzeugproblem über Sessions hingenommen) schlug ich vor, Wiederholungen von Abweichungen per Script aus den Commits sichtbar zu machen. Im selben Text stand, dass es zum mutmut-Problem schon zwei OBS gab – erfasst war es also. Erst der User benannte die eigentliche Lücke: die fehlende Prüfung der Ursache und die Entscheidung, ob und wie sie behoben wird. Die Maßnahme wurde danach auf Ursache und Folge je Umweg umgebaut.
  Warum: Ich habe die Kette Erfassen → Ursache prüfen → Behebung entscheiden nicht zerlegt, sondern die sichtbarste Eigenschaft der Fälle (Wiederholung über Sessions) zum Ansatzpunkt gemacht. Der Gegenbeleg lag in meiner eigenen Analyse und wurde nicht gegen den Vorschlag gehalten.
  Regel: Bevor eine Maßnahme vorgeschlagen wird: die Kette vom Auftreten bis zur Behebung in ihre Glieder zerlegen und für jedes Glied am Fall prüfen, ob es gerissen ist. Ein Beleg, dass ein Glied hielt, schließt es als Ansatzpunkt aus.
  CM-Bezug: CM-S095-2

## Session 141 – 2026-10-24

- **[HOCH] [PROZESS] [Kommunikation] LL-S141-1 – Triage-Vorlage ohne ausgeschriebene Alternativen**
  Quelle: User
  Was: In S141 legte der Orchestrator dem User die Abschluss-Triage zweimal unvollständig vor: in run-1 mit nur zwei Optionen („vermerken oder nicht“), in run-2 als Liste mit Empfehlung je Punkt, deren Alternativen nur pauschal im Kopf standen. Der User musste beide Male die Alternativen nachfordern; zwischendurch wäre eine Entscheidung allein auf Basis der Empfehlung möglich gewesen.
  Warum: Der Skill implementing-scenario verlangte nur „jeden Punkt mit Kontext und begründeter Empfehlung“; die drei Optionen standen als Rahmen im Skill, aber keine Regel verlangte, sie je Punkt konkret auszuschreiben. Bei vielen Punkten verdichtete der Orchestrator auf die Empfehlung.
  Regel: Triage per AskUserQuestion, je Punkt alle drei Optionen als eigene, konkret beschriebene Antwort, Empfehlung zuerst; gleichthematische Punkte bündeln (seit S141 in implementing-scenario, Abschluss).
  CM-Bezug: neu

- **[HOCH] [PROZESS] [Kommunikation] LL-S141-2 – Aufschubgrund „User“ ohne Entscheidung des Users gesetzt**
  Quelle: User (bemerkt, vom Orchestrator eingeräumt)
  Was: In S141 setzte der Orchestrator zweimal beim Erfassen eines Tracker-Eintrags den Aufschubgrund „User – …“, obwohl der User zu diesem Punkt nicht gefragt worden war bzw. nicht „später“ entschieden hatte. Der User bemerkte es; der Orchestrator räumte es ein und korrigierte.
  Warum: Das Pflichtfeld bietet nur zwei Werte (User, Recherche); trifft keiner zu, wäre die Konsequenz „jetzt beheben“ oder „den User fragen“. „User“ lag als bequemer Wert nahe, weil der User die Session insgesamt steuerte – die Zuschreibung wurde aus dem Gesamtkontext abgeleitet statt an eine konkrete Antwort gebunden. Damit wird genau die Prüfung ausgehebelt, für die das Feld existiert, und der Tracker trägt eine falsche Begründung.
  Regel: Aufschubgrund „User“ nur mit einer konkreten Antwort des Users zu genau diesem Punkt in dieser Session; sonst fragen oder beheben.
  CM-Bezug: CM-S133-2

- **[MITTEL] [PROZESS] [Mutation-Testing] LL-S141-3 – Freigabe-Anker ohne -w berechnet – Blob nicht auflösbar**
  Quelle: Orchestrator (gemeldet vom Subagenten)
  Was: Beim Review-Fix in US-602 run-2 berechnete der Orchestrator den Test-Freigabe-Anker mit git hash-object ohne -w. Der Blob landete nicht im Objektspeicher; der Subagent konnte den Diff gegen den Anker nicht bilden (bad object) und gab die ganze Datei aus. Der Orchestrator wich auf den letzten gültigen Anker aus und prüfte den Gesamt-Diff.
  Warum: Der Skill nennt git hash-object -w, der Orchestrator rief den Befehl aber in einer Sammelzeile zusammen mit reinen Lese-Hashes auf und ließ -w weg. Kein Mechanismus prüft beim Übergeben des Ankers, ob er auflösbar ist (OBS-S141-3).
  Regel: Freigabe-Anker immer in einem eigenen Aufruf mit -w schreiben; Lese-Hashes zum Vergleichen getrennt halten.
