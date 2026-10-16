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

## Session 134 – 2026-09-29

- **[MITTEL] [AGENT] [Doku] LL-S134-1 – Eingetretenen Fälligkeits-Anker mechanisch in jetzt übersetzt**
  Quelle: User
  Was: Als TD-S083-2 (Theme-Foundation) behoben war, setzte ich die daran verankerte Priorität 'Visuelle Konsistenz-Guideline erweitern' auf Fällig: jetzt und bot sie als nächste Aufgabe an. Erst die Frage des Users, warum jetzt der richtige Zeitpunkt sei, zeigte: Die UX-Guideline nennt im Kopf einen eigenen Auslöser (mehr als ~3 Komponenten mit denselben visuellen Entscheidungen), der mit einer einzigen Seite nicht erfüllt ist. Umgesetzt wurde daraufhin nur eine kleine Baseline der getroffenen Entscheidungen.
  Warum: Der Anker TD-S083-2 war eine Voraussetzung (ohne Theme kein Ort für die Werte), kein Auslöser. Beim Eintreten habe ich die Fälligkeit aus dem Anker abgeleitet, statt sie aus dem Zieldokument neu zu bestimmen.
  Regel: Tritt ein Fälligkeits-Anker ein, zuerst fragen: War er Voraussetzung oder Auslöser? Bei Voraussetzung die Fälligkeit aus dem Gegenstand selbst neu bestimmen – das Zieldokument kann einen eigenen Auslöser nennen.

- **[MITTEL] [AGENT] [Review] LL-S134-2 – Entscheidungsfragen mit Finding-Kürzeln gestellt, die nur ich kannte**
  Quelle: User
  Was: Nach dem Zusammenführen von vier Auditor-Berichten bat ich den User, über 'A1', 'FC-7 (Teil Pending/Fehlerzustand)' und 'FC-6' zu entscheiden – Kürzel aus Berichten, die nur ich gesehen hatte. Der User konnte nicht entscheiden und musste nachfragen; erst die zweite, selbsttragende Fassung jeder Frage machte die Entscheidung möglich.
  Warum: Rückfall zu LL-S133-4 (Entscheidungsfragen in Werkzeug- und Session-Jargon vorgelegt) – dessen Regel stand nur in lessons_learned.md, das Prinzip 'Eine Tracker-ID nie nackt nennen' deckte weiter nur Tracker-Einträge ab. Finding-IDs aus Review-Berichten fühlten sich wie gemeinsamer Kontext an, weil ich die Berichte im Kopf hatte. Als Maßnahme ist das Prinzip jetzt auf selbst vergebene Kürzel erweitert.
  Regel: Jede Frage an den User muss ohne den Bericht verständlich sein, aus dem sie stammt: Was ist der Einwand, was habe ich geprüft, was schlage ich vor. Ein Finding-Kürzel darf nur als Zusatz zum ausgeschriebenen Punkt stehen.

## Session 135 – 2026-10-08

- **[MITTEL] [PROZESS] [Gherkin] LL-S135-1 – Verstöße gegen „Tiefe je Regel“ überstanden drei Prüfrunden**
  Quelle: User
  Was: Im US-602-Workshop prüften fünf Beispielzeilen Grenzfälle der Mengen-Erkennung (Vorzeichen, Komma, Punkt am Zeilenanfang), obwohl diese zum Zerleger gehört, einer fest abgelösten Übergangsregel. Außerdem behauptete ein SKELETON-Szenario „keine Meldung am Titel“, was ein MVP-Akzeptanzkriterium derselben Story ändert. Weder ich noch drei Prüfrunden fanden das; der User fand beides bei der Durchsicht.
  Warum: Der Skill ließ offen, wie weit „das Stabile in einer Übergangsregel“ reicht – die Mengenwerte (ADR-S020-1) wurden zu großzügig auf die ganze Zahlform ausgedehnt. Und die Frage „Ablösung fest eingeplant?“ kannte nur andere Stories, nicht spätere Stufen derselben Story.
  Regel: Den stabilen Teil einer Übergangsregel über seine Quelle (ADR, Akzeptanzkriterium) benennen und nur das voll spezifizieren, was die Quelle festlegt. Bei der Ablösungsfrage auch die Akzeptanzkriterien späterer Stufen derselben Story prüfen (jetzt in GHW-regel-tiefe und agent-review.md).

- **[MITTEL] [TOOLING] [Hook/Script] LL-S135-2 – Doku eines Auslösers versprach einen Zeitpunkt, den der Code nicht einhielt**
  Quelle: User
  Was: td_anchors.py beschrieb den Anker Szenario:„…“ mit „tritt ein, wenn sein Lauf drankommt“. Tatsächlich meldete die Agenda ihn erst, wenn das Szenario schon implementiert war. Auf dieser Grundlage hängte ich drei TDs auf Szenarien um; erst die Rückfrage des Users („wird das dann auch angezeigt?“) deckte auf, dass sie vor dem Lauf nirgends erschienen wären – ebenso wenig OQs mit diesem Anker.
  Warum: Die Zusage im Docstring war nie gegen den Code geprüft; getestet war nur die nachträgliche Meldung („beim Lauf nicht mitgenommen“). Ich habe mich beim Umhängen auf die Beschreibung verlassen, statt den Anzeigeweg nachzuvollziehen.
  Regel: Sagt die Doku eines Auslösers einen Zeitpunkt zu, braucht genau dieser Zeitpunkt einen Test. Bevor ich mich auf einen Anzeige- oder Auslösemechanismus verlasse, verfolge ich ihn im Code bis zur Stelle, an der er tatsächlich erscheint.
  CM-Bezug: CM-S064-1

## Session 136 – 2026-10-12

- **[MITTEL] [PROZESS] [Doku] LL-S136-1 – Regeländerung an einer Stelle, ihre Wiedergaben an anderen Stellen nicht mitgezogen**
  Quelle: Orchestrator
  Was: Im Doku-Review S136 habe ich Regeln an ihrer Hauptstelle geändert (Survivor-/Suppressionsregel, Seed-Abschnitt, Timeout-Tabelle, Gruppen-Route "" statt "/", Frontend-Teststrategie), ohne vorher alle Stellen zu suchen, die dieselbe Regel wiedergeben oder als Beispiel zeigen. Ein großer Teil der Befunde der Review-Läufe 2 und 3 waren Reste genau dieser Änderungen, darunter ein HOCH-Befund (Frontend-Implementer: „kein MSW-Test“). Das kostete zwei zusätzliche Review-Runden mit je vier Agenten.
  Warum: Die Änderung fühlte sich als redaktionelle Arbeit an einer Datei an; dass Beispiele, Agent-Definitionen, Checklisten und Kurzfassungen dieselbe Regel tragen, war nicht im Blick. Anker-Prüfung und Doku-Audit finden nur kaputte Verweise, keine inhaltlich veralteten Wiedergaben. Verwandt mit LL-S124-1 (Umbenennung ohne Verweissuche).
  Regel: Wer eine Regel ändert, sucht vorher repo-weit nach allen Stellen, die sie wiedergeben, verkürzen oder als Beispiel zeigen (Schlüsselbegriffe, Beispielcode, Agent-Definitionen, Checklisten) und zieht sie im selben Zug nach.

- **[MITTEL] [QUALITÄT] [Sonstiges] LL-S136-2 – Paket als ungenutzt entfernt, ohne die Tests ohne es laufen zu lassen**
  Quelle: Orchestrator
  Was: In S136 habe ich Microsoft.EntityFrameworkCore.InMemory in Server.Tests als tot eingestuft, weil der Code es nicht mehr verwendete. Nach dem Entfernen scheiterten 54 von 56 Backend-Tests zur Laufzeit: Das Paket hatte transitiv EF Core 10.0.5 in den Test-Build gezogen und so eine Versionsschere zu Infrastructure (10.0.4) kaschiert. Behoben durch einen expliziten Pin in Infrastructure.
  Warum: Die Einstufung stützte sich auf die Suche nach Verwendungen im Code. Ein Paket wirkt aber auch über die Versionsauflösung im Abhängigkeitsgraphen – das zeigt keine Codesuche, nur ein Lauf.
  Regel: Ob ein Paket entfernbar ist, belegt erst ein Build- und Testlauf ohne das Paket, nicht die Suche nach Verwendungen im Code. Bis dahin als Vermutung kennzeichnen.

## Session 137 – 2026-10-13

- **[MITTEL] [PROZESS] [Kommunikation] LL-S137-1 – Werkzeug-Verhalten in einer Erklärung als Tatsache dargestellt**
  Quelle: Orchestrator
  Was: Beim Erklären von PrivateAssets sagte der Agent dem User, analyzers privat zu halten verhindere, dass Analyzer-Regeln in referenzierenden Projekten greifen. Gestützt war das nur auf die NuGet-Doku. Über Projekt-Referenzen stimmt es nicht: Der OpenAPI-Source-Generator lief trotz PrivateAssets=analyzers in Server.Tests (das SDK liest Analyzer aus dem Paketordner, project.assets.json führt sie nicht). Korrigiert wurde es erst eine Antwort später, als der Build daran scheiterte.
  Warum: Im Erklärmodus springt die Selbstprüfung 'belegt oder nur angenommen?' nicht an – die Antwort fühlt sich wie Wissensvermittlung an, nicht wie eine Behauptung über Werkzeug-Verhalten. Eine Doku-Aussage wurde ungeprüft auf einen Fall übertragen (Projekt- statt Paket-Weitergabe), den die Doku gar nicht beschreibt.
  Regel: In Erklärungen bei jeder Aussage über Werkzeug-Verhalten die Quelle kennzeichnen: Doku, eigener Lauf in dieser Session oder Gedächtnis. Eine Doku-Aussage gilt nur für den Fall, den die Doku beschreibt; für einen anderen Weitergabe- oder Aufrufweg ist sie ungeprüft, bis ein Lauf sie bestätigt.

- **[MITTEL] [PROZESS] [Bash/Permission] LL-S137-2 – Schreibender Befehl als Informationsquelle missbraucht**
  Quelle: User
  Was: Um die gültigen Kontext-Tags für OBS-Einträge zu erfahren, setzte der Agent 'obs add' mit absichtlich ungültigem Kontext ab, in der Erwartung, die Fehlermeldung nenne die gültigen Werte. Wäre der geratene Wert doch gültig gewesen, hätte der Befehl einen Müll-Eintrag in observations.md geschrieben. Der User lehnte den Aufruf ab ('was soll dieser Befehl? Du schreibst damit ein OBS').
  Warum: Der Agent behandelte die Fehlermeldung eines schreibenden Werkzeugs als bequeme Auskunft und übersah, dass der Erfolgsfall Schreiben heißt. Die Information lag lesbar vor: Die Tag-Tabelle in docs/kaizen/process.md ist laut obs.py die einzige Quelle der erlaubten Werte.
  Regel: Zum Erkunden nie einen schreibenden Befehl verwenden, auch nicht mit absichtlich ungültigen Argumenten. Erlaubte Werte stehen in der Quelle, die das Werkzeug selbst liest, oder in --help.

- **[MITTEL] [PROZESS] [Hook/Script] LL-S137-3 – Guard-Änderung ohne Abgleich mit dem Altverhalten öffnete neue Umgehungen**
  Quelle: Orchestrator
  Was: Der erste Fix am Wrapper-Filter von check-bash-permission öffnete vier Umgehungen, die der alte Hook abfing: Klammer im Argument, Substitution in Anführungszeichen, Zwischenstufen der Pipeline, Schleifen. Aufgefallen ist das erst im Review, nicht in den eigenen Tests.
  Warum: Getestet wurden nur die neu zu behandelnden Fälle. Das Verhalten des alten Guards galt nicht als Referenz – was er abfing, war in keinem Test festgehalten und ging beim Umbau unbemerkt verloren.
  Regel: Bei jeder Änderung an einem Guard das alte Verhalten als Referenz nehmen: Fälle, die er abfing, werden Regressionstests, und der protokollierte Bestand läuft alt gegen neu durch, bevor die Änderung als fertig gilt. Der Abgleich findet beide Richtungen – neue Durchlässe und neue Fehl-Ablehnungen.

## Session 138 – 2026-10-16

- **[HOCH] [QUALITÄT] [Hook/Script] LL-S138-1 – Auditor-Sperre im Bash-Hook galt nicht für benannt gestartete Auditoren**
  Quelle: Orchestrator
  Was: Die Nur-Lese-Weiche für Auditoren (check-bash-permission, AUDITOREN) erkennt Auditoren am Feld agent_type der Hook-Eingabe. Mit Gegenproben, Lückenprobe und einer Live-Probe (agent_type kommt an) galt sie als belegt. Erst eine spätere Live-Probe für ein anderes Thema zeigte: Wird ein Agent mit name gestartet, steht in agent_type der Name statt des Typs – ein code-quality-auditor namens cq-probe durfte touch ausführen. Bis August 2026 waren 57 von 113 Auditor-Starts benannt.
  Warum: Die Live-Probe prüfte, DASS das Feld ankommt, an genau einer Startform (unbenannt). Die Formen, in denen der Auslöser vorkommt (benannt, unbenannt, Team), wurden nie aufgezählt; die Annahme 'agent_type = Typ' stammte aus dieser einen Form. Die Gegenproben brachen den Guard an seinen Mustern, nicht an seiner Erkennung.
  Regel: Hängt ein Guard an einem Feld der Hook-Eingabe, vor dem Fertig die Formen aufzählen, in denen der Auslöser auftreten kann (bei Agenten: mit/ohne name, Hintergrund, Team), und je Form einmal live prüfen, was in dem Feld ankommt – nicht nur, dass es ankommt.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S138-2 – Agenten-Namen für selten erklärt, ohne Logs oder alle Skills anzusehen**
  Quelle: User
  Was: Zur Abwägung fail-open gegen fail-closed behauptete ich, kein Skill vergebe Agenten-Namen, der Fehlalarm treffe also fast nie. Der User fragte nach einem Beleg. Die Logs zeigten 113 benannte Starts (bis August der Normalfall, bei Implementern ausnahmslos), und implementing-scenario schreibt Namen für Implementer sogar vor – ich hatte nur review-code angesehen.
  Warum: Ich habe aus der Vorschrift eines einzigen Skills auf die Praxis geschlossen, also zweimal verkürzt: ein Dokument statt aller, und Vorschrift statt Bestand. Die Regel 'Eine Vorschrift beschreibt nicht die Praxis' kannte ich; der Selbst-Check sprang nicht an, weil die Aussage nur ein Nebensatz in einer Abwägung war.
  Regel: Stützt eine Häufigkeitsaussage eine Abwägung (selten, nie, fast immer), sie vor dem Aussprechen am Bestand belegen (Logs, alle Skills) oder ausdrücklich als ungeprüft kennzeichnen – auch als Nebensatz.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S138-3 – Gleichgewicht des Drain-Triggers aus einer Phase ohne Implementierung geschlossen**
  Quelle: User
  Was: Für OBS-S122-1 rekonstruierte ich den Drain-Trigger über S128–S138 und empfahl, den Eintrag zu verwerfen: Die Frequenz liege zwar bei 1 von 7 statt 1 von 3, der Backlog sei aber im Gleichgewicht. Der User fragte, ob die Daten dafür reichen – in den sechs stillen Sessions lief kein einziger Implementierungs-Lauf, also gerade die Phase, die vermutlich die meisten und gewichtigsten Beobachtungen erzeugt.
  Warum: Ich habe korrekt gemessen, aber die Aussage auf den Normalbetrieb ausgedehnt, ohne zu prüfen, ob das Messfenster ihn enthält. Die Zusammensetzung der Sessions stand im Commit-Verlauf, den ich für dieselbe Prüfung schon gelesen hatte; das Gleichgewicht selbst war zudem gerechnet (Zulauf gegen Drain-Leistung), nicht gemessen.
  Regel: Vor einem Schluss aus einem Messfenster fragen, welche Betriebsarten die Aussage abdecken soll, und prüfen, ob das Fenster jede davon enthält. Fehlt eine, die Messung als Basislinie dieser Phase festhalten statt als Urteil.
  CM-Bezug: CM-S127-1
