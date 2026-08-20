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

## Session 116 – 2026-08-10

- **[MITTEL] [TOOLING] [Hook/Script] LL-S116-1 – Tests prüften den Regex-Baustein, nie die Funktion, die ihn anwendet**
  Quelle: Orchestrator
  Was: Beim Verifizieren der Archivierung am Ende der Retro stand der Jenga-Score bei 90/100 statt 100, obwohl die frisch aus dem Template angelegte lessons_learned.md keinen einzigen Eintrag enthält. Ursache: jenga_score.parse() liest zeilenweise und kennt keine HTML-Kommentare – der Beispiel-Eintrag LL-S084-1, der im Datei-Header das Eintrags-Format dokumentiert, wurde als echtes HOCH-Finding gezaehlt. Folge: Jede Periode startete bei 90 statt 100, die Retro wurde systematisch rund zwei Sessions zu frueh faellig. retro_report.py war nicht betroffen, weil es Findings ueber die Session-Header zuordnet und das Beispiel davor steht.
  Warum: test_jenga_score.py existierte und war gruen – die drei Tests pruefen aber ausschliesslich FINDING_RE gegen einzelne Zeilen-Strings. Die Funktion parse(), die eine Datei oeffnet und die Regex anwendet, war von keinem Test beruehrt. Der Baustein war abgesichert, seine Anwendung nicht; ein Testaufbau, der nie eine Datei liest, kann einen Datei-Parse-Fehler grundsaetzlich nicht zeigen.
  Regel: Ist eine Regex oder ein aehnlicher Baustein getestet, ist damit noch nichts ueber die Funktion gesagt, die ihn anwendet – mindestens einen Test gegen die aufrufende Funktion mit realistischem Input fuehren (hier: eine Datei mit echtem Header). Dieselbe Fixture so waehlen, dass ein Fix, der zu viel entfernt, ebenso auffaellt wie gar kein Fix.

- **[MITTEL] [AGENT] [Doku] LL-S116-2 – Aus der gerenderten Session-Start-Injektion auf den Dateiinhalt geschlossen**
  Quelle: Orchestrator
  Was: Fuer die User-Beobachtung 'Agenten erfassen Erledigtes' wurde ein Beleg gesucht und im injizierten SessionStart-Output gefunden: Der erste Punkt unter 'Naechste Prioritaeten' lautete dort 'US-904 naechster Lauf: (alle Laeufe der Story US-904 implementiert)'. Das ging als Erledigt-Meldung in einen frisch geschriebenen LL-Eintrag ein, und der Punkt sollte aus AGENT_MEMORY entfernt werden. Der User stoppte das mit der Frage, warum das dort richtig aufgehoben sei. Erst das Oeffnen der Datei zeigte: Dort steht der Platzhalter {{NEXT_RUN}}; der Satz ist gerenderte Ausgabe von next_run.py und beschreibt den Zustand korrekt. Ohne den Einwand waeren eine korrekte Zeile geloescht und ein falscher Beleg archiviert worden.
  Warum: Der SessionStart-Hook injiziert AGENT_MEMORY im gerenderten Zustand, ununterscheidbar von einem Datei-Read. Weil der Inhalt bereits im Kontext lag, entfiel der Anlass, die Datei zu oeffnen – die Ansicht wurde fuer die Quelle gehalten. Verstaerkend: Es fuehlte sich nicht wie eine Behauptung ueber Tool-Verhalten an, sondern wie das Zitieren eines Dokuments, das man ohnehin vor sich hat.
  Regel: Bevor ein Befund ueber den Inhalt eines Dokuments behauptet wird – erst recht, bevor daraus geloescht wird – die Datei selbst oeffnen. Alles, was ein Hook injiziert oder ein Script rendert, ist eine abgeleitete Ansicht: Platzhalter sind darin bereits aufgeloest, und genau die Stelle, an der etwas generiert wird, sieht im Rendering wie handgeschriebener Text aus.

## Session 117 – 2026-08-11

- **[MITTEL] [PROZESS] [Doku] LL-S117-1 – Element wegen einer Wirkung entfernt, ohne seine Funktionen vorher zu trennen**
  Quelle: Orchestrator
  Was: Der User meldete, dass der nachrangige Abschnitt der Session-Agenda sich gleichrangig zur "Nächsten Aufgabe" liest. Ich fuehrte das auf die identische Trennerform `--- X ---` zurueck und entfernte den unteren Trenner. Damit verlor der Aufgabenabschnitt seine untere Grenze und alles danach lief optisch in ihm weiter - schlechter als vorher. Der User musste korrigieren ("Ohne die Trenner wirkt es jetzt aber, als waere es Teil der naechsten Aufgabe").
  Warum: Ich hatte fuer einen beobachteten Effekt eine plausible Erklaerung und handelte danach, statt vorher aufzulisten, welche Funktionen das Element traegt. Der Trenner trug zwei: er markierte die GRENZE und - zusammen mit seinem Label - den RANG. Die beanstandete Gleichrangigkeit hing am neutralen Label "Ebenfalls offen", nicht an der Trennerform; das Entfernen opferte die Grenze und liess die Ursache unberuehrt. Wiederholter Verstoss gegen "Vollstaendige Zerlegung vor Schluss/Empfehlung" in principles.md, hier auf ein einzelnes Artefakt statt auf einen Entscheidungsraum angewandt.
  Regel: Bevor ein Element wegen einer unerwuenschten Wirkung entfernt oder geaendert wird: seine Funktionen einzeln benennen und pruefen, an welcher davon die Wirkung tatsaechlich haengt. Traegt es mehrere, nimmt das Entfernen alle mit - die unerwuenschte Wirkung haengt oft an einer anderen Eigenschaft als der, die man opfert.

## Session 118 – 2026-08-12

- **[MITTEL] [PROZESS] [Doku] LL-S118-1 – Eine Fehlablage erbt die Wiedervorlage ihres Zielorts, nicht die ihres Inhalts**
  Quelle: User
  Was: Dass Ingredient.Id ein rohes Guid ist, verletzt eine seit jeher geltende Regel: architecture.md Kernprinzip 1 nennt Guid namentlich, coding-guideline-csharp.md Paragraph 2 nennt ItemId als kanonisches Beispiel. In S083 wurde das bemerkt und als offene Frage OQ-S083-2 abgelegt - der Eintrag zitiert die Regel sogar woertlich ('Inkonsistenz zu immer Value Objects'). Damit landete eine Regelverletzung in einer Datei fuer noch nicht getroffene Entscheidungen. Folge: kein Faelligkeitsanker, keine Terminierungspflicht, und bis S115 ueberhaupt kein Lese-Trigger. Ab S115 erschien die Frage im Agenten-Startkontext, erreichte den User aber nicht (Bezug: OBS-S117-2). In S118 zum ersten Mal wirklich vorgelegt und binnen einer Session aufgeloest - samt eines dabei aufgedeckten schwereren Befunds: ToDomain() erzeugt eine Wegwerf-Id, weil Ingredient.Create eine verlangt (Bezug: TD-S118-1, TD-S118-2).
  Warum: Die Ablage entscheidet, welche Wiedervorlage-Maschinerie ein Befund erbt - nicht sein Inhalt. tech-debt.md erzwingt seit S117 einen terminierten Anker und meldet ueber die Session-Agenda; open-questions.md kannte bis S115 gar keinen Rueckweg. Der Fehler war also nicht mangelnde Aufmerksamkeit, sondern eine Klassifikation: 'Entscheidung faellig' statt 'Entscheidung laengst gefallen, Umsetzung offen'. Eine Frage verlangt niemandem etwas ab, eine Schuld schon. Der Erstverstoss selbst ist eine weitere Instanz von CM-S047-1 (Guidelines gelesen, aber nicht angewandt) - dort seit S047 sechs Rueckfaelle.
  Regel: Vor dem Ablegen eines Befunds pruefen: Ist die Entscheidung noch offen (dann OQ), oder ist sie laengst getroffen und nur nicht umgesetzt (dann TD mit Anker)? Zitiert der Eintrag eine bestehende Guideline oder Architektur-Regel, ist er fast immer das Zweite. Generell: Wer etwas ablegt, entscheidet damit ueber seine Wiedervorlage - der Zielort muss zur Terminierung passen, die der Inhalt braucht.

## Session 120 – 2026-08-18

- **[HOCH] [PROZESS] [Mutation-Testing] LL-S120-1 – 100 % Mutation Score als Beleg gelesen, dass eine Trim-Eigenschaft gepinnt ist – Wiederholung von LL-S092-1**
  Quelle: Orchestrator
  Was: Beim Umbau auf Bounded<> war offen, ob die Längengrenze vor oder nach dem Trimmen greift; Backend-Tests 83/83 und Stryker 100 % blieben über beide Implementierungsvarianten hinweg unverändert, die Eigenschaft war also ungepinnt, ohne dass ein Gate anschlug. Erst die FC-9-Gegenprobe machte es sichtbar.
  Warum: Standard-Stryker mutiert weder .Trim() noch string.IsNullOrEmpty, und beide sitzen auf nicht-verzweigenden Anweisungen – Mutation Score und Branch Coverage können Datentransformations-Korrektheit strukturell nicht messen. Genau das steht seit S092 als LL-S092-1 im Archiv, hat aber 28 Sessionen später nicht getragen: Zu LL-S092-1 wurde nie eine Countermeasure angelegt, damit gab es keinen Wiedervorlage-Mechanismus.
  Regel: Bei Trim/Casing/Normalisierung nie aus einem grünen Mutation-/Coverage-Lauf schließen, dass die Eigenschaft festgenagelt ist. Stattdessen die Gegenprobe fahren: die andere Implementierungsvariante herstellen und prüfen, ob die Suite umschlägt – bleibt sie grün, fehlt der Test. Rückfall zu LL-S092-1: gehört in der nächsten Retro als Countermeasure-Kandidat bewertet.

- **[HOCH] [AGENT] [Agent-Prompt] LL-S120-2 – Auditor-Prompt verlangte eine Gegenprobe per Bash, obwohl die Auditoren kein Bash-Tool haben**
  Quelle: User
  Was: Die Review-Prompts gaben den Auditoren ADR-Volltexte plus den Auftrag, die Auswahl per 'python3 .claude/scripts/decisions.py' selbst gegenzuprüfen. Die Auditor-Definitionen führen aber nur Read/Grep/Glob/LSP – der Befehl war für sie nicht ausführbar, die Gegenprobe fand nie statt. Sichtbar wurde es erst, als ein Auditor 12 Findings meldete, weil ADR-S106-3 in meiner Liste fehlte und er den Mangel nicht selbst entdecken konnte.
  Warum: Beim Formulieren des Prompts habe ich vom eigenen Toolset auf das des Subagenten geschlossen, statt dessen Agent-Definition zu prüfen. Eine nicht ausführbare Anweisung schlägt nicht fehl, sie verschwindet still – der Orchestrator glaubt danach, eine unabhängige Prüfung habe stattgefunden.
  Regel: Bevor ein Prompt einem Subagenten eine Handlung aufträgt, dessen Tool-Liste in .claude/agents/<typ>.md prüfen. Ist die Handlung mit seinem Toolset nicht möglich, entweder das Werkzeug bereitstellen oder die Anweisung durch eine mit seinen Mitteln ausführbare ersetzen (Grep statt Script) – niemals eine Anweisung stehen lassen, deren Nichtausführung unsichtbar bleibt.

- **[HOCH] [PROZESS] [Agent-Prompt] LL-S120-3 – Auftrag an den Implementer widersprach der Prozessdoku, die ich nicht gelesen hatte**
  Quelle: Subagent
  Was: Mein Auftrag an den backend-layer-implementer verlangte eine reguläre EF-Core-Migration für die Schema-Änderung. dev-workflow.md schreibt für die SKELETON-Phase aber Drop+Recreate statt einer Migrations-Kette vor. Der Implementer hielt dagegen, ich verifizierte und gab ihm recht.
  Warum: Ich habe die Vorgabe aus allgemeinem EF-Core-Wissen abgeleitet, statt die zuständige Prozessdoku zu konsultieren – der Orchestrator schreibt Aufträge zu Themen, deren Doku nur die Subagenten lesen. Hätte der Implementer gehorcht, wäre der handgeschriebene SQL-Block der Migration beim nächsten Neugenerieren verlorengegangen.
  Regel: Enthält ein Subagenten-Auftrag eine konkrete Vorgehensvorgabe zu Build, DB oder Toolchain, vorher die zuständige Sektion in dev-workflow.md nachschlagen statt sie aus Allgemeinwissen abzuleiten. Und: Widerspricht ein Subagent einer Vorgabe unter Verweis auf eine Doku-Stelle, diese Stelle prüfen, bevor auf der Vorgabe bestanden wird.

- **[MITTEL] [QUALITÄT] [Review] LL-S120-4 – Gegenprobe vorgeschlagen, die die beiden Varianten mathematisch gar nicht unterscheiden kann**
  Quelle: Subagent
  Was: Um zu belegen, ob die Längengrenze vor oder nach dem Trimmen greift, schlug ich als Gegenprobe einen 31-Zeichen-Namen mit Padding vor, der 422 liefern sollte. Der Implementer wies nach, dass der Fall beide Implementierungen gleich beantwortet, weil die getrimmte Länge nie größer als die rohe ist – nur ein Wert, der getrimmt unter und roh über der Grenze liegt, trennt sie.
  Warum: Ich habe die Gegenprobe nach Plausibilität gewählt (Grenzwert plus Padding klingt nach dem kritischen Fall), ohne durchzurechnen, ob die beiden Hypothesen für diese Eingabe wirklich verschiedene Ausgaben haben. Das Prinzip 'Gegenprobe' (CM-S116-1) fordert genau diesen Schritt und wurde auf die Gegenprobe selbst nicht angewandt.
  Regel: Eine Gegenprobe erst ansetzen, wenn für die konkrete Eingabe gezeigt ist, dass die konkurrierenden Hypothesen unterschiedliche Ausgaben liefern. Frage vor dem Ausführen: 'Welches Ergebnis sagt Hypothese A vorher, welches B?' – sind beide gleich, ist es keine Gegenprobe, sondern eine Bestätigung.

## Session 121 – 2026-08-20

- **[MITTEL] [TOOLING] [Hook/Script] LL-S121-1 – Tracker-Schreibscript zerstoerte einen Eintrag strukturell; Schaden fiel erst zehn Sessions spaeter auf**
  Quelle: Orchestrator
  Was: Beim Drain in S121 liess sich OBS-S111-4 nicht per obs.py set abschliessen – Abbruch mit 'hat kein Feld - Entscheidung/Maßnahme'. Der Eintrag war strukturell beschaedigt: Das Feld stand mitten in der Beobachtungszeile statt am Zeilenanfang, dahinter drei spaeter angehaengte Absaetze. Reparatur nur per Hand-Edit der Datei moeglich – also genau ueber den Pfad, den die Script-Pflicht vermeiden soll.
  Warum: append_beobachtung() haengt per Design an die Beobachtungs-ZEILE an, weil Felder einzeilig sind (obs_entry.py:158). Rutscht ein Folgefeld einmal auf diese Zeile, wachsen alle weiteren Anhaenge hinter das Folgefeld, und der Parser findet es nicht mehr. Keines der Schreibscripte prueft nach dem Schreiben, ob der Eintrag noch alle Pflichtfelder je genau einmal am Zeilenanfang traegt. Der Fehler ist damit stumm: Er meldet sich erst, wenn jemand denselben Eintrag schreiben will – hier beim Abschluss, zehn Sessions nach der Entstehung.
  Regel: Ein Script, das ein strukturiertes Dokument schreibt, prueft nach dem Schreiben die Struktur des geaenderten Eintrags – nicht nur die Eingaben davor. Garantierte Form beim Anlegen ersetzt keine Kontrolle nach dem Aendern, denn beschaedigt wird der Eintrag erst durch spaetere Schreibzugriffe.

- **[HOCH] [PROZESS] [Messung] LL-S121-2 – Gemessen wurde, wofuer Daten dalagen - nicht, was die Frage beantwortet**
  Quelle: User
  Was: Fuer die Bewertung der Bash-Permission-Reibung (OBS-S111-4) wertete ich zuerst nur denied-commands.log aus und legte darauf eine vollstaendige Kandidatenliste vor. Der User musste die Analysebasis dreimal korrigieren: (1) die vom User selbst freigegebenen Befehle sind das staerkere Signal, weil dort keine Alternative existierte, (2) die Zahlen mussten am letzten groesseren Umbau geschnitten werden, sonst mischen sich zwei verschiedene Hooks, (3) entscheidend ist nicht der Deny, sondern was danach geschah - Umweg gefunden oder Ziel aufgegeben. Erst die zweite Analyse trug: 61 Prozent der Denies endeten in einem Umweg, die Freigabequote lag bei 93 Prozent, und keine einzige der vier Ablehnungen war eine Sicherheitsablehnung.
  Warum: Das Deny-Log lag als Datei bereit und war trivial auszuwerten. Ich habe die Verfuegbarkeit einer Datenquelle mit ihrer Aussagekraft verwechselt und die Zerlegung des Messraums uebersprungen - genau das, was principles.md unter Vollstaendige Zerlegung vor Schluss/Empfehlung verlangt. Erschwerend: Das Ergebnis sah quantitativ aus (822 Denies, Kategorien, Prozente) und wirkte dadurch belastbarer, als es war.
  Regel: Vor dem Messen bestimmen, welches Signal die Frage beantworten wuerde, und erst dann pruefen, welche Daten dafuer vorliegen - nie umgekehrt. Bei Reibungs- und Wirksamkeitsfragen gehoeren immer drei Richtungen dazu: was wurde geblockt, was wurde erlaubt oder freigegeben, und was geschah danach. Fehlt eine, ist die Aussage unvollstaendig, egal wie viele Zahlen die vorhandene traegt.

- **[HOCH] [QUALITÄT] [Testing] LL-S121-3 – 810 Zeilen Hook-Tests uebersahen monatelang, dass der Hook seinen eigenen Zweck verfehlte**
  Quelle: Orchestrator
  Was: check-bash-permission.py erlaubte jeden mehrzeiligen Befehl vollstaendig, sobald die ERSTE Zeile ein Allow-Muster traf: 'ls -la' plus zweite Zeile 'rm -rf /tmp/x' lief durch, ebenso 'git status' plus 'rm -rf Client/' und 'echo' plus 'git push --force'. Verifiziert gegen die HEAD-Fassung, also vorbestehend und nicht in S121 eingebaut. Die Luecke bestand seit dem Bestehen des Splitters; das Deny-Log zeigt sie nicht, weil mehrzeilige Befehle in der Praxis fast immer mit VAR= oder for beginnen - der Deny kam also zufaellig zustande, nicht durch Pruefung. Aufgefallen ist sie erst, als ich fuer ein NEUES Feature einen Guard-Test schrieb und dabei die Gegenprobe formulierte.
  Warum: Die 810 Zeilen Tests pruefen durchweg, was der Hook TUT: dieser Befehl wird erlaubt, jener geblockt, dieses Segment so gesplittet. Kein einziger Test fragte, was er VERHINDERN MUSS - also ob es eine Formulierung gibt, mit der ein destruktiver Befehl durchkommt. Ein Sicherheitsmechanismus ohne Umgehungstests bestaetigt nur seine bekannten Faelle; sein Ausfall loest per Definition nichts aus, weil er nicht abstuerzt, sondern schweigt und erlaubt.
  Regel: Fuer jeden Mechanismus, dessen Zweck das Verhindern ist, gehoeren Umgehungstests zur Grundausstattung, nicht zur Kuer: nicht nur 'blockt X', sondern 'es gibt keine Schreibweise von X, die durchkommt'. Beim Bauen oder Aendern eines solchen Mechanismus mindestens eine Umgehung aktiv suchen und als Test festschreiben - Verhaltenstests allein decken die Ausfallart nicht ab, um die es geht.

## Session 122 – 2026-08-21

- **[MITTEL] [AGENT] [Doku] LL-S122-1 – Feld nach breitem Kriterium befuellt, nach engem dokumentiert**
  Quelle: User
  Was: Beim Einfuehren des Feldes Zusammen-erledigen habe ich es im Bestand nach einem breiten Kriterium befuellt - OBS-S116-1 kam in den Cluster, obwohl ich im selben Arbeitsschritt notiert hatte, dass dieselbe Loesung es nur halb betrifft - und zugleich eng dokumentiert: 'Erledigt eine Loesung beide?'. Beide Fassungen entstanden innerhalb einer Stunde in zwei Artefakten. Der Widerspruch fiel erst dem User auf, der das Kriterium als zu eng gefasst hinterfragte.
  Warum: Die Regel wurde in Abgrenzung zu etwas anderem formuliert (die bestehende Datei-Kolokation erschien zu grob), das Feld dagegen am konkreten Fall befuellt. Zwei verschiedene Denkbewegungen, nie gegeneinander gehalten. Die Doku beschrieb damit nicht die eigene Praxis, sondern die Reaktion auf einen Nachbarmechanismus.
  Regel: Nach dem Formulieren einer Erfassungsregel die eigenen frisch erfassten Eintraege gegen sie pruefen: Wuerde die Regel mein eigenes Ergebnis durchlassen? Weicht die Praxis ab, ist meist die Regel falsch - sie entstand am Reissbrett, die Befuellung am Fall.

- **[HOCH] [PROZESS] [TDD] LL-S122-2 – Drei Pruefmittel gebaut, keines gegengeprobt**
  Quelle: Orchestrator
  Was: In einer Session entstanden drei Pruefmittel, die Erfolg und Misserfolg nicht unterscheidbar anzeigten. (a) Zwei neue Tests behaupteten, eingehende Kanten wuerden angezeigt - sie prueften auf eine nackte OBS-ID, die im Fixture ohnehin als Bezug stand, und waeren ohne jede Implementierung gruen gewesen. (b) Ein Migrations-Pruefscript zeigte 'keiner' und 'Feld fehlt' identisch an; es meldete die Migration als vollstaendig, waehrend OBS-S118-1 unmigriert war - aufgefallen erst nach Reparatur des Scripts. (c) Eine Gegenprobe-Erwartung war gegen einen veralteten Bestand formuliert und schlug fehl, obwohl der Code stimmte.
  Warum: Alle drei Faelle folgen demselben Muster: Das Pruefmittel wurde gebaut, um eine erwartete Bestaetigung einzuholen, nicht um zwischen zwei Ausgaengen zu trennen. Das Prinzip 'Die Gegenprobe' steht seit S116 in principles.md und ist per CM verankert - es fehlte also kein Wissen, sondern die Anwendung im Moment des Bauens. Verschaerfend: Ein falsch-positiver Test ist selbst ein Pruefmittel, das lautlos ausfaellt.
  Regel: Beim Bauen eines Pruefmittels - Test, Messcript, Gegenprobe - vor dem ersten Lauf einmal den Misserfolgsfall herstellen und bestaetigen, dass er anders aussieht. Bei Assertions auf IDs oder Namen zusaetzlich pruefen, ob der erwartete String im Fixture schon aus anderem Grund vorkommt.

- **[MITTEL] [AGENT] [Skill-Nutzung] LL-S122-3 – Eigene Ankuendigung als Freigabe behandelt, waehrend eine Frage offen war**
  Quelle: User
  Was: Nach einer laengeren Design-Diskussion habe ich vier Kandidaten vorgelegt, zu einem davon ausdruecklich eine Rueckfrage gestellt und im selben Zug geschrieben 'Ich lege jetzt los' - und begonnen umzusetzen. Der User hatte die Rueckfrage noch nicht beantwortet und ruegte das ausdruecklich ('Da du einfach losgelegt hast, ohne eine Rueckmeldung von mir zu holen').
  Warum: Die vorangegangenen Antworten des Users hatten die Richtung bestaetigt, was sich wie eine allgemeine Freigabe anfuehlte. Die eigene Ankuendigung 'ich lege los' wirkte dabei als Selbstermaechtigung: Sie fuellte die Stelle, an der eine Antwort haette stehen muessen. Eine offene Frage im selben Text macht die Ankuendigung aber gerade ungueltig - man kann nicht gleichzeitig fragen und das Ergebnis vorwegnehmen.
  Regel: Steht im eigenen letzten Beitrag eine Frage an den User, ist der Turn zu Ende - unabhaengig davon, wie klar die Richtung scheint. Entweder fragen oder handeln, nie beides in einer Nachricht. Wer handeln will, laesst die Frage weg und benennt stattdessen die getroffene Annahme.
