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
