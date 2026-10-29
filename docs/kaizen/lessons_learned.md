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

## Session 142 – 2026-10-26

- **[HOCH] [PROZESS] [Review] LL-S142-1 – Findings mit dem Wortlaut der Regeln verworfen statt mit ihrer Absicht**
  Quelle: User
  Was: In der Abschluss-Triage von US-602 run-4 schlug der Orchestrator vor, zwei Review-Befunde ohne Änderung zu verwerfen: CQ-8 (Type Assertion bei useParams) mit „kommentiert, die Guideline verbietet es nicht", obwohl coding-guideline-typescript.md as-Assertions ausdrücklich nur für Tests lockert; CQ-4 (Lesepfad DB→DTO ohne Domain-Objekt) mit einem Argument über Primitives an der DTO-Grenze, das den Kern – den fehlenden ToDomain()-Schritt, längst als TD-S083-5 erfasst – nicht berührte. Ebenso übernahm er die Einstufung eines Subagenten, der Primitive-Obsession-Hinweis sei an dieser Stelle ein Fehlalarm. Der User fing beides ab („klingt danach, als würde der Geist der Guidelines dagegen sprechen").
  Warum: Geprüft wurde, ob eine Regel den Fall wörtlich verbietet, nicht, wozu sie da ist. Eine ausdrückliche Lockerung für einen Kontext wurde nicht als Aussage über die übrigen Kontexte gelesen, und ein Befund wurde an seinem schwächsten Teilargument gemessen statt an seinem Kern.
  Regel: Einen Befund erst verwerfen, wenn er auch gegen die Absicht der Regel nicht trägt – nicht schon, weil kein Wortlaut ihn verbietet. Lockert eine Regel etwas ausdrücklich für einen Kontext, gilt das Gegenteil für alle anderen. Einen Befund an seinem Kern prüfen, nicht an seinem schwächsten Argument.
  CM-Bezug: CM-S047-1

- **[HOCH] [PROZESS] [Skill-Nutzung] LL-S142-2 – Schnell behebbare Befunde dem User zum Vermerken empfohlen**
  Quelle: User
  Was: In der Abschluss-Triage von US-602 run-4 empfahl der Orchestrator, sieben Prozess-Befunde als OBS zu erfassen (qa-check prüft Given/When/Then erst nach Stryker, test-inventory übersieht mehrzeiliges it.each, Freigabe-Anker ohne -w, Auditor liest Guidelines nur angeschnitten u. a.). Fünf davon waren in Minuten behebbar, einer (Auditor-Lesefehler) potenziell folgenreich; nur einer brauchte einen eigenen Entwurf. Der User fragte „Warum nicht direkt umsetzen?" – danach waren sechs in derselben Session behoben.
  Warum: Der Pflicht-Aufschubgrund aus CM-S133-2 greift nur bei der eigenen Erfassung. Eine Empfehlung „vermerken" an den User umgeht ihn: Stimmt der User zu, entsteht der zulässige Aufschubgrund „User" von selbst – die Schwelle „verstanden und behebbar → beheben" wurde nie angelegt.
  Regel: In einer Triage dieselbe Schwelle anlegen wie bei eigener Erfassung: Verstanden und schnell behebbar oder potenziell folgenreich → „direkt umsetzen" empfehlen; „vermerken" nur mit einem Aufschubgrund, der auch ohne die Zustimmung des Users trüge.
  CM-Bezug: CM-S133-2

## Session 143 – 2026-10-29

- **[HOCH] [PROZESS] [Review] LL-S143-1 – Review-Fix-Tests mit US-Tag ohne Szenario beauftragt – Regel „Szenario vor dem Fix“ übergangen**
  Quelle: Subagent
  Was: In Review-Runde 1 von US-602 run-6 beauftragte ich als Orchestrator Komponententests für Verhalten, das kein Szenario-Beispiel nannte: ein Titel nur aus U+0085 löst keine Nachfrage aus (eine Verhaltensänderung, vorher löste er sie aus) und Text nur in Schritt 2 löst sie aus. Beide trugen den Namen US602_EdgeCase_… und nur einen ADR-Kommentar. Der Test-Quality-Auditor fand es erst in Runde 2 (TQ-1); der User entschied, die Beispiele ins Feature-File zu nehmen.
  Warum: Ich ordnete die Fälle der Diagnose c des Test-Reviews zu (ADR-Kommentar genügt) und übersah, dass der Review-Loop für Verhalten aus einem Review-Fix ausdrücklich ein Szenario vor dem Fix verlangt und einen US-Tag erst mit Szenario erlaubt. Die Regel stand im geladenen Skill; angewendet habe ich die näherliegende, aber für Review-Fixes nicht zuständige.
  Regel: Vor jedem Fix-Auftrag aus dem Review-Loop die Szenario-Frage stellen und schriftlich beantworten: Ändert der Fix beobachtbares Verhalten oder testet er Verhalten, das kein Szenario-Beispiel nennt? Dann zuerst Beispiel oder Szenario ins Feature-File (mit User-Freigabe), sonst kein US-Tag am Test. Diagnose c (ADR-Kommentar) gilt nur im Test-Review nach RED, nicht für Review-Fixes.
  CM-Bezug: CM-S070-1

- **[MITTEL] [PROZESS] [Review] LL-S143-2 – Fehlende Given-Kommentare im Test-Review nicht gemeldet**
  Quelle: Orchestrator
  Was: Im Test-Review von US-602 run-5 gab ich vier Komponententests ohne // Given frei. Der Punkt „Given/When/Then-Struktur: fehlen die Kommentare → Finding melden“ aus IMP-test-review fiel aus. Erst der Übergabelauf von qa-check brach per Check 5 vor Stryker ab; die Testdatei musste nach der Freigabe noch geändert werden.
  Warum: Ich habe das Test-Review auf Per-Assertion-Zuordnung und Gold-Plating konzentriert und die Checkliste nicht Punkt für Punkt abgearbeitet. Den Ausfall fing nur das mechanische Gate auf; die Checkliste selbst ist nicht der Fehler.
  Regel: Das Test-Review geht die vier Punkte aus IMP-test-review vollständig durch und nennt zu jedem ein Ergebnis, auch „Given/When/Then: vorhanden“. Ein Punkt ohne genanntes Ergebnis gilt als nicht geprüft.
  CM-Bezug: CM-S070-1

## Session 144 – 2026-10-29

- **[MITTEL] [QUALITÄT] [Review] LL-S144-1 – Vom UI-Entwurf geforderte Assertion im Test-Review als Gold-Plating gestrichen**
  Quelle: Orchestrator
  Was: Im Test-Review von US-602 run-8 (S144) habe ich die Assertion toBeInvalid() am Titelfeld als Gold-Plating streichen lassen, weil kein Gherkin-Kriterium „markiert“ sagt. Der vom User freigegebene UI-Entwurf zeigte den Titel aber ausdrücklich rot. Folge: der error-Prop des Titels blieb ungetestet und überlebte als Mutant; eine Review-Runde später musste derselbe Test (diesmal über aria-invalid) zurück.
  Warum: Ich habe die Per-Assertion-Pflicht nur gegen die Gherkin-Szenarien geprüft und den im selben Lauf freigegebenen UI-Entwurf nicht als Spec-Quelle mitgedacht.
  Regel: Beim Test-Review gelten der freigegebene UI-Entwurf und die Szenarien gemeinsam als Spec für sichtbare UI-Details – eine Assertion, die der Entwurf trägt, ist kein Gold-Plating.

- **[HOCH] [QUALITÄT] [Mutation-Testing] LL-S144-2 – 100 % Mutation-Score als verifiziert gemeldet, obwohl Timeouts 13 Survivors verdeckten**
  Quelle: Orchestrator
  Was: In US-602 run-8 (S144) habe ich den Frontend-qa-check mit 100 % und gültigem Hash als verifiziert gemeldet, obwohl 101 von 240 Mutanten als Timeout endeten (Vormittagsläufe: 36–44). Erst der Code-Review-Abgleich zeigte, dass auch Mutanten ohne mögliche Schleife (error={…} → false) als Timeout liefen; mit timeoutMS 60000 standen 13 Survivors da, im Gesamtlauf zusätzlich ein seit run-3/run-4 verdeckter. Dieselbe Klasse war als OBS-S143-1 bereits zweimal erfasst – ich hatte sie vor der Aussage nicht nachgeschlagen.
  Warum: Der Hash belegt Frische, nicht, dass jeder Mutant getötet wurde; Stryker zählt Timeouts als erkannt, und qa-check gated nicht darauf. Ich habe die auffällige Timeout-Zahl zwar bemerkt, sie aber als Kann-Artefakt durchgewinkt statt sie vor der Aussage aufzulösen.
  Regel: Ein Mutation-Score mit nennenswertem Timeout-Anteil ist kein Beleg: Vor „verifiziert“ jeden Timeout im geänderten Code ansehen (kann der Mutant eine Schleife erzeugen? sonst wie Survivor behandeln) und bekannte Beobachtungen zum Werkzeug nachschlagen (hier OBS-S143-1).
  CM-Bezug: CM-S116-1
