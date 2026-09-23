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

## Session 129 – 2026-09-07

- **[HOCH] [QUALITÄT] [Testing] LL-S129-1 – Gegenprobe mit erfundenen Daten prueft den Aufbau, nicht die Kette**
  Quelle: Orchestrator
  Was: Der neue mutmut-Wrapper hatte 21 Tests samt Gegenprobe und meldete trotzdem gruen, obwohl er nur 13 Prozent der Mutanten ausgewertet hatte: Ein Mutant mit Exit -9 bringt 'mutmut results' mit KeyError zu Fall, mitten in der Ausgabe. Der Wrapper prueft den Exit-Code des Subprozesses nicht und las die abgeschnittene Ausgabe als vollstaendig. Saemtliche Tests arbeiteten mit handgeschriebenen Statuszeilen; keiner beruehrte je eine echte Ausgabe des fremden Werkzeugs.
  Warum: Die Fixtures wurden aus der Vorstellung gebaut, wie die Ausgabe aussieht - und die war richtig. Getestet wurde damit der Parser, nie die Kette Subprozess-Ausgabe-Auswertung. Ein Abbruch des Subprozesses lag ausserhalb dessen, was die Fixtures abbilden konnten. Gefunden hat den Fehler allein eine Plausibilitaetsfrage an einer echten Zahl: 69 bewertete Mutanten bei 646 vorhandenen kann nicht stimmen.
  Regel: Wer die Ausgabe eines fremden Werkzeugs auswertet, prueft dessen Exit-Code und fuehrt mindestens einen Test gegen dessen ECHTE Ausgabe. Erfundene Fixtures pruefen den eigenen Parser, nicht die Schnittstelle. Und: Jede Zahl, die ein neues Werkzeug erstmals liefert, gegen eine unabhaengig bekannte Groessenordnung halten.
  CM-Bezug: CM-S116-1

- **[HOCH] [AGENT] [Kommunikation] LL-S129-2 – Erfundene Erklaerung fuer einen Widerspruch, statt die Historie zu pruefen**
  Quelle: User
  Was: Der Freigabedialog rendert ANSI nicht mehr, obwohl zwei Docstrings das Gegenteil behaupteten und sich dabei auf eine Messung aus S124 beriefen. Ich habe den Widerspruch mit der Behauptung aufgeloest, die damalige Pruefung habe die Terminal-Ausgabe statt den Dialog gesehen - frei erfunden, und in beide Docstrings geschrieben. Der User widersprach; das Session-Log belegte, dass er das Bild damals real im Dialog gesehen und zurueckgemeldet hatte. Claude Code hatte das Verhalten still geaendert, undokumentiert.
  Warum: Ein Widerspruch zwischen dokumentiertem Befund und aktueller Messung verlangt eine Erklaerung, und die naechstliegende - der Vorgaenger hat schlecht gemessen - war sofort verfuegbar und klang plausibel. Sie kostete nichts zu formulieren und wurde deshalb nicht als Behauptung ueber fremdes Verhalten erkannt, sondern als Randbemerkung geschrieben. Die Historie lag greifbar im Session-Log, wurde aber erst auf Aufforderung geprueft.
  Regel: Widerspricht eine aktuelle Messung einem frueher dokumentierten Befund, ist die erste Handlung die Pruefung der Historie - nicht die Erklaerung. Bleibt die Ursache danach offen, gehoert genau das in den Text: 'hat frueher funktioniert, jetzt nicht mehr, Ursache unbekannt'. Eine erfundene Erklaerung entwertet den festgehaltenen Befund mit.
  CM-Bezug: CM-S064-1

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S129-3 – TD-Eintrag angelegt, statt das Problem im selben Zug zu beheben**
  Quelle: User
  Was: Fuer die Subprozess-Aufrufe in session-agenda.py habe ich einen TD-Eintrag samt Prioritaeten-Punkt in AGENT_MEMORY angelegt, mit der Begruendung, der Umbau sei ein eigener Eingriff mit eigenem Risiko. Auf die Rueckfrage des Users, was dagegen spreche, es direkt zu erledigen, war es in wenigen Minuten getan - derselbe Handgriff, den ich fuenf Minuten zuvor an derselben Datei schon gemacht hatte. Eintrag und Prioritaeten-Punkt mussten wieder entfernt werden.
  Warum: Die Erfassung fuehlte sich als sorgfaeltige Buchhaltung an und war deshalb kein Anlass innezuhalten. Verglichen habe ich das Risiko der Aenderung mit dem Nichtstun - nicht die Kosten der Erfassung (Eintrag, Prioritaeten-Punkt, Wiedervorlage, spaeteres Wiedereinlesen des Kontexts) mit den Kosten der Behebung. Der Kontext war zu diesem Zeitpunkt maximal frisch, das Testnetz lag vor, die Datei war offen.
  Regel: Vor dem Anlegen eines TD-Eintrags die Behebung abschaetzen: Ist sie im aktuellen Kontext billiger als Erfassung plus Wiedervorlage, wird sie erledigt. Ein Eintrag, den dieselbe Session wieder entfernt, war nie einer.

## Session 130 – 2026-09-09

- **[HOCH] [AGENT] [Kommunikation] LL-S130-1 – Wirkung eines Mechanismus beurteilt, ohne alle Pfade zu prüfen – zweimal in einer Session**
  Quelle: User
  Was: Zwei Aussagen ueber Mechanismen, beide aus nur einer Blickrichtung geprueft, beide vom User gekippt. (1) Der Bare-Root-Ersatz in check-bash-permission.py wurde zweimal als 'reine Kosmetik, loest kein Deny-Problem' bezeichnet und darauf eine Empfehlung gestuetzt (Entfernen). Geprueft war nur, ob die ALLOW_PATTERNS ihn brauchen. Auf Nachfrage des Users durchgemessen: drei Stellen haengen daran, darunter cd_npm_conflict, wo sein Fehlen 'cd <root> && npm run x' faelschlich blockt. (2) Behauptet, der Drain-Slot sei durch Abarbeiten praktisch nicht freizubekommen, weil drei der alternden Eintraege selbst in den Top-5 stehen. Uebersehen, dass triggers() ausschliesslich NEU-Eintraege zaehlt – ein abgearbeiteter Eintrag faellt aus Wert- UND Alters-Trigger zugleich.
  Warum: Beide Male wurde die Frage nur aus der Richtung gestellt, aus der ich gerade kam: bei (1) 'brauchen die Allow-Muster das?' statt 'wer liest diese Stelle sonst noch?', bei (2) 'welche Eintraege altern?' statt 'was passiert mit ihnen bei Bearbeitung?'. In beiden Faellen lag eine billige mechanische Gegenprobe bereit und wurde nicht gezogen: die Stelle entfernen und die Suite fahren (zwei Minuten, deckte alle drei Abhaengigkeiten auf) bzw. die zehn Zeilen von triggers() lesen. Das Argument fuehlte sich jeweils vollstaendig an, weil es in sich schluessig war – Schluessigkeit ersetzt aber keine Zerlegung.
  Regel: Vor einer Aussage ueber die Wirkung eines Mechanismus die Leser und Pfade aufzaehlen, nicht nur den eigenen Blickwinkel abschliessen. Wo eine mechanische Gegenprobe existiert – Stelle entfernen und Suite fahren, die entscheidende Funktion lesen – ist sie billiger als das Argument und ersetzt es. Besonders bei dem Satz 'das leistet nichts': Er ist eine Aussage ueber ALLE Leser einer Stelle und damit nie aus einer Richtung belegbar.
  CM-Bezug: CM-S095-2

## Session 131 – 2026-09-09

- **[MITTEL] [PROZESS] [Testing] LL-S131-1 – Fixture mit einem Eintrag prueft einen Fall, den es real nie gibt**
  Quelle: Agent
  Was: Die neu gebaute Kuerzungs-Warnung fuer Tracker-Schreibbefehle sammelte Feldwerte dateiweit in ein dict. Da jeder Eintrag dieselben Feldnamen traegt, ueberschrieb der letzte Eintrag alle vorigen - verglichen wurde nur sein Wert. Acht Tests waren gruen; alle arbeiteten mit genau EINEM Eintrag, waehrend jede echte Tracker-Datei viele hat. Folge: Der Datenverlust, den die Warnung verhindern sollte, trat unmittelbar danach ein zweites Mal ein (vier Saetze Begruendung in OQ-S119-3 ueberschrieben, beide Male nur durch git diff bemerkt).
  Warum: Die Fixtures entstanden aus dem Minimalfall, der die Funktion aufruft, nicht aus der Form des echten Datenbestands. Ein Fixture mit einem Eintrag kann den Fehler strukturell nicht zeigen: Bei einem Eintrag ist das dateiweite dict identisch mit dem eintragsbezogenen. Erfolg und Misserfolg waren im Aufbau nicht unterscheidbar, das gruene Ergebnis trug also nichts. Gefangen wurde es allein durch die Gegenprobe am echten Werkzeug.
  Regel: Fixture-Form am echten Datenbestand ausrichten: Prueft eine Funktion eine Datei mit vielen Eintraegen, braucht das Fixture mehr als einen - sonst prueft der Test einen Fall, den es real nie gibt. Bei jedem Fixture fragen, worin es sich vom Produktivdatensatz unterscheidet und ob der Fehler in dieser Form ueberhaupt auftreten koennte.
  CM-Bezug: CM-S116-1 (Rueckfall, Auspraegung „untauglicher Pruefaufbau" – dieselbe Form wie LL-S123-7: gegen eine selbstgebaute Fixture geprueft statt gegen das echte Artefakt)

## Session 132 – 2026-09-23

- **[HOCH] [PROZESS] [Testing] LL-S132-1 – Beleg durch die eigene Änderung erzeugt: Stryker 50/50 unter [ExcludeFromCodeCoverage]**
  Quelle: User
  Was: Nach dem Ausschluss ganzer Methoden per [ExcludeFromCodeCoverage] meldete Stryker auf IngredientsEndpoints.cs 50/50 Mutanten getötet. Daraus wurde zweimal behauptet, die getestete Logik in diesen Methoden bleibe durch Stryker gedeckt; damit wurde ein Review-Finding (fehlende Stryker-Suppression laut ADR-S111-2) abgelehnt und die Ablehnung in einen ADR-Nachtrag geschrieben. Tatsächlich verwirft Stryker.NET Mutanten in so markiertem Code (Status Ignored, 18 Stück) – die 50 waren die Überlebenden der eigenen Änderung. Aufgedeckt erst durch den Einwand des Users, der JSON-Report enthalte jeden Mutanten mit Status.
  Warum: Die Messung wurde als unabhängige Bestätigung der Änderung gelesen, obwohl die Änderung selbst in den Messaufbau eingriff. Die Gegenfrage „hätte das Ergebnis anders ausgesehen, wenn die Logik ungedeckt wäre?" wurde nicht gestellt; der Blick auf Ignored-Mutanten und deren Gründe im Report fehlte.
  Regel: Greift eine Änderung in ein Prüfwerkzeug ein (Attribut, Ausschluss, Konfiguration), belegt ein grünes Ergebnis desselben Werkzeugs nichts über sie. Vorher die Grundgesamtheit vergleichen (Anzahl geprüfter Mutanten/Zeilen vor und nach) und die ausgeschlossenen Elemente samt Grund ansehen.
  CM-Bezug: CM-S116-1

- **[MITTEL] [PROZESS] [Doku] LL-S132-2 – Gescheiterter Versuch als „nicht erneut probieren" erfasst, ohne Ursache: richtiger Weg blieb 40 Sessions gesperrt**
  Quelle: Orchestrator
  Was: Der TD-Eintrag zum abgeschalteten Backend-Coverage-Gate (S089) führte coverlet.MTP unter „Nicht erneut probieren", weil es mit einer TypeLoadException gescheitert war. Die Ursache war nicht die Engine, sondern ein gemischter Graph: das Paket xunit.v3 ist die mtp-v1-Variante, coverlet.MTP verlangt MTP 2. Das Gate blieb rund 40 Sessions aus; in der Zeit liefen zwei echte Testlücken auf. Gelöst in S132 mit genau der als gescheitert markierten Engine – nach einem Blick in die nuspec-Abhängigkeiten.
  Warum: Festgehalten wurde das Symptom (Exception-Text) samt Verbot, nicht die geprüfte oder vermutete Ursache. Ein späterer Leser kann ein Verbot ohne Begründung nicht gegen eine veränderte Lage prüfen und respektiert es – der Eintrag wirkte als Sperre statt als Wissen.
  Regel: Einen gescheiterten Versuch nur mit diagnostizierter Ursache als Ausschluss erfassen; ist die Ursache unbekannt, das so benennen („gescheitert mit X, Ursache ungeklärt") statt „nicht erneut probieren". Vor dem Verwerfen einer Paket-Kombination die Abhängigkeiten der beteiligten Pakete vergleichen (nuspec).
