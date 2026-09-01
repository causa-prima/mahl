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

## Session 128 – 2026-09-02

- **[HOCH] [QUALITÄT] [Hook/Script] LL-S128-1 – 59 gruene Tests deckten einen CLI-Parameter, der nie ausgewertet wurde**
  Quelle: Orchestrator
  Was: session-agenda.py bekam --block <name>, um je einen Injektionsblock auszugeben; settings.json registriert den Aufruf fuenfmal. Der Parameter wurde per argparse deklariert, aber in main() nie ausgewertet - jeder der fuenf Hooks haette dieselbe Agenda injiziert, principles.md und Allow-Liste waeren ersatzlos verschwunden. Alle 59 Tests der Datei waren dabei gruen. Aufgefallen ist es erst beim Nachmessen der Blockgroessen von Hand: alle fuenf lieferten identische 3.155 units.
  Warum: Die Tests riefen rendere_block() direkt auf - die Funktion. Der Hook ruft die CLI. Zwischen beiden lag die Luecke, und keine Zusicherung ueberspannte sie. Der Aufbau war gruen und pruefte den Gegenstand nie: Er konnte gar nicht unterscheiden, ob die Verdrahtung existiert. Dieselbe Bruchstelle wie beim Anlass der Session - session-agenda.py lief fehlerfrei, waehrend ihre Wirkung ausblieb.
  Regel: Bei einem Werkzeug mit Aufrufpfad (CLI, Hook, Registrierung) mindestens eine Zusicherung ueber den ECHTEN Pfad ziehen, nicht nur ueber die Funktion dahinter: den Prozess starten, die Ausgabe pruefen, und bei mehreren Varianten pruefen, dass sie sich UNTERSCHEIDEN. Ein Test, der jede Variante einzeln fuer plausibel haelt, faellt nicht auf, wenn alle dasselbe liefern.
  CM-Bezug: neu

- **[HOCH] [AGENT] [Kommunikation] LL-S128-2 – Eine WebFetch-Zusammenfassung als Quelle behandelt und eine falsche Zahl weitergegeben**
  Quelle: User
  Was: Zum undokumentierten Hook-Output-Limit von Claude Code lieferte WebFetch auf das GitHub-Issue eine Antwort mit '10.000 intern, 50.000 dokumentiert (Mismatch)'. Ich habe daraus einen Befund gebaut und ihn als Recherche-Ergebnis vorgelegt. Der User fragte nach, ob ich auch die Kommentare gelesen haette. Hatte ich nicht: WebFetch laesst ein kleines Modell den Prompt gegen die Seite beantworten - was zurueckkommt, ist eine Zusammenfassung unbekannter Vollstaendigkeit. Der Zugriff per gh auf dasselbe Issue lieferte neun Kommentare mit dem tatsaechlichen Stand: 10.000 UTF-16 units, empirisch mit fuenf Proben bestimmt, Cap pro registriertem Command (das war die Entscheidungsgrundlage fuer die ganze Umbaurichtung), Reihenfolge nicht garantiert. Die 50.000 waren ein veralteter Doku-Wert.
  Warum: Ein Werkzeug, das Text zurueckgibt, fuehlt sich wie eine Quelle an. WebFetch ist aber ein Leser mit eigenem Urteil darueber, was relevant ist - und dieses Urteil ist beim Zusammenfassen bereits gefallen, unsichtbar. Verschaerfend: Die Antwort war fluessig, nannte Zahlen und wirkte vollstaendig. Ohne die Nachfrage waere der Umbau auf einer Wette statt auf einem Beleg gestanden, denn genau die tragende Aussage (Cap pro Command) fehlte in der Zusammenfassung.
  Regel: Traegt eine Aussage aus einer WebFetch-Antwort eine Entscheidung, ist sie unverifiziert, bis die Quelle im Volltext vorlag. Bei GitHub 'gh issue view --comments' statt WebFetch; sonst die Antwort ausdruecklich als Zusammenfassung kennzeichnen. Insbesondere: Das Fehlen einer Angabe in einer Zusammenfassung ist kein Beleg fuer ihr Fehlen in der Quelle.
  CM-Bezug: neu

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S128-3 – Verstandenen Bug in den Backlog erfasst, statt ihn in 15 Minuten zu beheben**
  Quelle: User
  Was: Beim Vermessen von principles.md fiel auf, dass doc.py eine eingerueckte Beispiel-Ueberschrift als echte liest und deshalb 82 Prozent eines Abschnitts still verschluckt. Ursache und Fix waren im selben Moment klar. Ich habe daraus trotzdem einen OBS-Eintrag geschrieben. Der User fragte, warum das in den Tracker gehoert und nicht direkt behoben wird. Die Behebung samt Tests und Bestandssichtung dauerte danach rund 15 Minuten; der Eintrag wurde ersatzlos aus observations.md geloescht und der nachfolgende umnummeriert.
  Warum: Der Drain-Skill praegt die Erfassung als Standardreaktion auf jeden Befund - Erfassung ist billig, also erfasse ich. Die Frage, ob der Tracker-Zyklus (erfassen, drainen, entscheiden, umsetzen) teurer ist als die sofortige Behebung, stellt sich dabei nicht von selbst. Beim doppelten Preis: Der Eintrag kostet Backlog-Kapazitaet, die er nie gebraucht haette, und speist genau den Zufluss, dessen Konvergenz in OBS-S126-1 beobachtet wird.
  Regel: Vor dem Erfassen pruefen, ob ueberhaupt erfasst werden muss. Erfassen lohnt nur, wenn die Behebung (a) eine Entscheidung braucht, die dem Agenten nicht zusteht, (b) den Sessionfokus sprengt, oder (c) der Befund noch nicht verstanden ist. Trifft keines zu - typisch bei einem verstandenen Bug in einem Werkzeug, das gerade in der Hand liegt - direkt beheben.

- **[MITTEL] [QUALITÄT] [Doku] LL-S128-4 – Eigener Zwischentitel zog 3.600 Zeichen fremden Text in seine Abrufeinheit**
  Quelle: Orchestrator
  Was: In process.md wurde unter '## Session-Agenda' ein '### Warum fuenf Hooks und nicht einer' eingefuegt. Der Text danach - Aufbau der Agenda, Rangfolge, Extremschwellen, Ausfallverhalten - gehoerte weiterhin zur uebergeordneten Ebene, lief markdown-technisch aber unter der neuen Ueberschrift. 'doc.py get KPR-injektions-cap' lieferte damit 5.172 statt rund 1.500 Zeichen. Aufgefallen beim Verdichtungs-Check zum Sessionende, nicht beim Schreiben. Behoben durch einen Geschwister-Anker KPR-agenda-aufbau.
  Warum: Beim Einfuegen einer Zwischenueberschrift denkt man an den eigenen Text, nicht an den, der danach steht - der war schon da und wirkte unveraendert. Die Wirkung ist trotzdem eine Umgliederung des Bestehenden. Besonders unauffaellig, weil die gerenderte Datei fuer einen menschlichen Leser voellig unveraendert aussieht: Nur der maschinelle Abruf verschiebt sich, und der meldet nichts.
  Regel: Nach dem Einfuegen einer Zwischenueberschrift den Abschnitt einmal abrufen (doc.py get) und pruefen, wo er endet. Faustregel: Eine neue Ueberschrift auf Ebene N zwingt den nachfolgenden Text derselben Ebene ebenfalls unter eine Ueberschrift - sonst wird er stillschweigend eingemeindet.

- **[MITTEL] [AGENT] [Bash/Permission] LL-S128-5 – Eine Grenze als absolut gemeldet, obwohl der Ausweg im Deny-Text stand**
  Quelle: User
  Was: Nach dem PEP-668-Fehlschlag von pip habe ich dem User gemeldet, ich koenne die Werkzeuge 'nicht selbst installieren', und ihn um Ausfuehrung gebeten. Der User fragte zurueck, ob nicht --allow-once genau dafuer da sei. War es. Der Mechanismus steht woertlich im Deny-Text jedes geblockten Befehls und in der Allow-Liste, die am Session-Start injiziert wird - ich hatte beides im Kontext.
  Warum: Ein Deny liest sich als Endpunkt, nicht als Verzweigung. Der Ausweg steht zwar in derselben Meldung, aber hinter der Absage, und die Absage beantwortet die Frage bereits - danach wird nicht weitergelesen. Verschaerfend: In derselben Session bin ich mehrfach in Denies gelaufen und habe den Hinweis jedes Mal gesehen, ohne ihn auf den Installationsfall anzuwenden.
  Regel: Bevor eine Grenze an den User weitergereicht wird ('geht nicht', 'kann ich nicht'), den Deny-Text auf seinen Ausweg pruefen und ihn benennen - entweder als genutzten Weg oder mit dem Grund, warum er hier nicht traegt. Eine Absage ohne diese Pruefung ist unbelegt.
