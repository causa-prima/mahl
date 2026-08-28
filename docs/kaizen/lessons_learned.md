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

## Session 123 – 2026-08-21

- **[HOCH] [TOOLING] [Hook/Script] LL-S123-1 – Report-Script meldete seinen Befund per Exit-Code – das Modul fiel genau im Zielfall aus**
  Quelle: Orchestrator
  Was: Die Session-Agenda meldete 'Modul retro ausgefallen (Exit 2)' und schlug einen OBS-Drain vor, obwohl der Jenga-Score bei -14 stand und eine Retro faellig war. jenga_score.py signalisierte 'Retro faellig' ueber Exit 2; session-agenda.py wertet - fuer alle Module einheitlich - jeden Exit ungleich 0 als Modulausfall. Das Retro-Modul fiel damit genau in dem Fall aus, fuer den es gebaut ist. Ohne den Blick auf die Warnzeile waere die faellige Retro erneut nicht gelaufen.
  Warum: Der Exit-Code war ein zweiter, redundanter Meldekanal neben dem stdout-Text, den kein Aufrufer je auswertete: session-agenda.py prueft 'RETRO FAELLIG' im Text, der fruehere session-start.sh griff per grep. Er war nirgends dokumentiert und von keinem Test gedeckt - eine stumme Konvention, die nur beim generischen Aufrufer Schaden anrichtete. Ein solcher Ausfall loest per Definition nichts aus: Das Modul meldet sich als kaputt, waehrend die Information, die es tragen sollte, unbemerkt verschwindet.
  Regel: Ein Script, das von einem generischen Rahmen konsumiert wird, meldet seinen Befund im stdout; der Exit-Code sagt ausschliesslich, ob der Lauf gelang. Signal-Exits nur dort, wo der Aufrufer sie nachweislich auswertet - sonst faellt das Modul genau dann aus, wenn es etwas zu melden hat. Beim Bauen eines Report-Scripts pruefen, welche Konvention seine Aufrufer voraussetzen.
  CM-Bezug: CM-S116-1

- **[MITTEL] [PROZESS] [Hook/Script] LL-S123-2 – Ausnahme im generischen Rahmen geplant, statt den einen abweichenden Aufrufer zu korrigieren**
  Quelle: User
  Was: Nachdem der Exit-2-Bug von jenga_score.py diagnostiziert war, wollte ich _laufe() in session-agenda.py um einen Parameter 'erlaubte Signal-Exits' erweitern - also die Ausnahme im gemeinsamen Rahmen aller Agenda-Module verankern. Der User hielt dagegen: Wenn nur ein Script Probleme macht, sei vermutlich dieses Script der Konventionsbruch. Die Pruefung gab ihm recht - alle anderen Report-Scripts der Agenda liefern Exit 0, der Exit-2 war nirgends dokumentiert und von keinem Aufrufer ausgewertet.
  Warum: Der Fix wurde dort angesetzt, wo der Fehler sichtbar wurde (der Rahmen meldete den Ausfall), nicht dort, wo er entstand. Uebersprungen wurde die Zerlegung 'wer braucht diese Ausnahme sonst noch?' - haette ich sie gezaehlt, waere die Antwort null gewesen. Eine Ausnahme im generischen Rahmen ist zudem teurer als sie aussieht: Sie erlaubt jedem kuenftigen Script dieselbe Abweichung und macht die Konvention damit unverbindlich.
  Regel: Weicht genau ein Element von einer etablierten Konvention ab, ist das Element verdaechtig, nicht die Konvention. Vor jeder Aenderung an einem gemeinsam genutzten Rahmen auszaehlen, wie viele Nutzer die geplante Ausnahme tatsaechlich braeuchten - bei eins gehoert der Fix an dieses eine Element.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S123-3 – grep -c zaehlt Vorkommen, nicht Objekte - Zahl als Statusbefund vorgelegt**
  Quelle: Orchestrator
  Was: Beim Regressions-Check der bewaehrten Maßnahme CM-S102-2 zaehlte ich die ref-ok-Marker im Bestand und legte vor, sie seien 'von 3 (S116) auf 7 gestiegen' - ein moeglicher Regressions-Kanal, der die Maßnahme von BEWAEHRT zurueck auf AKTIV gebracht haette. Beim Nachsehen waren es 3 echte Marker; die uebrigen 4 Treffer waren Prosa-Erwaehnungen in Session-Logs, die ueber Marker berichten statt welche zu sein.
  Warum: Ein grep-Muster trifft Zeichenketten, keine Objekte der gemeinten Art. Weil das Ergebnis eine Zahl ist und Zahlen wie Messungen aussehen, entfiel der Anlass, die Treffer anzusehen - obwohl der Filter (Ausschluss einiger Dateien) bereits zeigte, dass ich die Trefferart fuer erklaerungsbeduerftig hielt.
  Regel: Vor dem Berichten einer Zaehlung die Treffer selbst ansehen, nicht nur ihre Anzahl - besonders wenn die Zahl eine Statusaenderung tragen wuerde. Zaehlt das Muster in Dokumenten, die ueber den gesuchten Gegenstand schreiben (Logs, Retros, Archive), sind diese vor dem Zaehlen auszuschliessen.
  CM-Bezug: CM-S064-1

- **[MITTEL] [PROZESS] [Doku] LL-S123-4 – Dieselbe Erklaerung in vier Dokumente geschrieben, eines davon verbietet Duplikate ausdruecklich**
  Quelle: User
  Was: Beim Verankern des neuen Feldes CM-Bezug schrieb ich dieselbe Erklaerung samt Session-Statistik in vier Dokumente (Template, process.md, Code-Kommentar, Testkommentar). In process.md landete zusaetzlich das Feldformat - in genau dem Abschnitt, der einleitend sagt: 'Format-Skeleton ... stehen kanonisch im Header von lessons_learned.md - hier nicht duplizieren. Dieser Abschnitt ergaenzt nur die Prozess-Regeln.' Aufgedeckt erst durch die Aufforderung des Users, die Aenderungen auf Redundanz durchzusehen.
  Warum: Beim Verankern eines neuen Konzepts wird jede beruehrte Stelle einzeln bearbeitet, und an jeder einzelnen wirkt die vollstaendige Erklaerung angemessen - die Redundanz entsteht zwischen den Stellen und ist beim Schreiben der jeweils aktuellen unsichtbar. Dass die Regel dagegen woertlich im selben Absatz stand, zeigt: Es fehlte nicht das Wissen, sondern der Blick auf das Ganze.
  Regel: Beruehrt eine Aenderung mehrere Dokumente, zuerst festlegen welches die kanonische Stelle ist; die uebrigen bekommen einen Verweis, keine zweite Erklaerung. Vor dem Schreiben in ein Dokument dessen eigene Regeln zur Arbeitsteilung lesen - sie stehen meist im Abschnittskopf.
  CM-Bezug: CM-S086-1

- **[MITTEL] [AGENT] [Doku] LL-S123-5 – Verdichten machte aus einer optionalen Angabe ein scheinbares Verbot**
  Quelle: User
  Was: Beim Kuerzen der Doku zum neuen CM-Bezug-Feld wurde aus 'bei MITTEL/GERING optional - besteht ein Bezug, gehoert er hinein' die Kurzform 'sonst weglassen'. Das liest sich als Verbot, obwohl Code und Test den freiwilligen Bezug ausdruecklich zulassen. Der User fragte nach, ob er etwas falsch verstehe - der Text stand zu diesem Zeitpunkt bereits in drei Dateien, darunter die frisch aus dem Template erzeugte lessons_learned.md.
  Warum: Kuerzen fuehlt sich wie eine rein sprachliche Operation an, nicht wie eine Aussage ueber Verhalten - der Selbst-Check fuer Behauptungen springt dabei nicht an. Verschaerfend: Die Kuerzung geschah auf ausdrueckliche Aufforderung hin, also unter dem Ziel 'weniger Worte', gegen das die verlorene Einschraenkung wie Ballast wirkte.
  Regel: Nach dem Kuerzen eines Textes, der Verhalten beschreibt, gegen das tatsaechliche Verhalten gegenlesen - Vorlage ist der Code oder der Test, nicht die eigene Langfassung. Verdichtung entfernt bevorzugt Einschraenkungen und Nebenfaelle, weil sie wie Beiwerk aussehen; der gekuerzte Satz liest sich danach widerspruchsfrei und faellt gerade deshalb nicht auf.
  CM-Bezug: CM-S116-1

- **[HOCH] [AGENT] [Kommunikation] LL-S123-6 – Mehrpfadigen Mechanismus an einem Pfad geprueft und das Ergebnis fuers Ganze genommen**
  Quelle: User
  Was: Zur Frage, warum OBS-S116-5 seit S116 nie im Drain behandelt wurde, pruefte ich die Wert-Lane (Score 1 liegt unter der Schwelle 2) und schloss daraus, der Drain haette den Eintrag 'in keinem kuenftigen Drain-Satz' aufgegriffen - der Weg sei strukturell unmoeglich. Der Drain hat aber eine zweite Lane: Ab 15 Sessions Alter erzwingt die Alters-Lane eine Entscheidung, der Eintrag waere also ab S131 erschienen. Der User korrigierte mit 'works as intended'. Die falsche Begruendung stand zu diesem Zeitpunkt bereits in CM-S078-2 und im OBS-Archiv.
  Warum: Geprueft wurde der Pfad, der die Beobachtung erklaerte, und die Pruefung endete mit der Erklaerung statt mit der Aufzaehlung aller Pfade. Erschwerend: Die Alters-Lane stand als eigener Abschnitt in genau dem Drain-Satz, den ich zu Session-Beginn gelesen hatte - es fehlte kein Wissen, sondern die Zerlegung. Ein negativer Befund ueber einen Mechanismus ('greift nie') ist eine Allaussage und verlangt deshalb alle Pfade, waehrend ein positiver an einem Beispiel haengt.
  Regel: Bevor behauptet wird, ein Mechanismus greife in einem Fall nicht, seine Auswahlpfade vollstaendig aufzaehlen und jeden einzeln pruefen - eine Negativaussage ueber einen Mechanismus ist eine Allaussage. Konkret bei Auswahl-Mechanismen mit mehreren Lanes, Schwellen oder Triggern: Die Konfiguration im Script nachlesen, nicht vom beobachteten Verhalten auf die Regel schliessen.
  CM-Bezug: CM-S095-2

- **[MITTEL] [TOOLING] [Hook/Script] LL-S123-7 – Befehl gegen eine Fixture geprueft, die den Datei-Header nicht enthielt**
  Quelle: Orchestrator
  Was: Fuer den kaizen-Skill dokumentierte ich den Auswertungsbefehl grep '^  CM-Bezug:' und pruefte ihn gegen eine selbst gebaute Fixture - Ergebnis korrekt, also in den Skill geschrieben und als verifiziert dargestellt. An der echten Datei zaehlte derselbe Befehl einen Treffer zu viel: die Erklaerzeile aus dem HTML-Kommentar des Datei-Headers, die zufaellig dieselbe Einrueckung trug. Der Befehl haette in jeder kuenftigen Retro einen Phantom-Bezug angezeigt. Gefunden nur, weil ich den Befehl nach dem Erfassen der Eintraege noch einmal real laufen liess.
  Warum: Die Fixture enthielt genau die Zeilen, um die es ging, und nichts sonst - sie bildete den Rahmen der echten Datei nicht ab. Genau dieselbe Ursache wie bei LL-S116-1, wo jenga_score.parse() den Beispiel-Eintrag aus dem Header als echtes Finding zaehlte; der Header ist bei diesen Dateien Teil des Formats und traegt absichtlich Beispielzeilen im Eintragsformat.
  Regel: Einen Befehl oder Parser, der auf eine reale Projektdatei angewandt werden soll, mindestens einmal gegen genau diese Datei laufen lassen - eine selbst gebaute Fixture belegt nur, dass er die gemeinten Zeilen findet, nicht dass er sonst nichts findet. Bei Dateien mit dokumentierendem Header gilt das doppelt: Der Header traegt Beispielzeilen im Eintragsformat und ist damit die wahrscheinlichste Quelle falscher Treffer.
  CM-Bezug: CM-S116-1

## Session 124 – 2026-08-27

- **[HOCH] [PROZESS] [Doku] LL-S124-1 – Nummer entfernt, ohne nach Verweisen darauf zu suchen**
  Quelle: Orchestrator
  Was: Bei der Anker-Migration wurden nummerierte Abschnitte umbenannt, ohne vorher zu pruefen, wer per Nummer darauf zeigt. Zweimal in derselben Session: erst starben sechs Verweise in .editorconfig, eslint.config.js, IngredientsEndpoints.cs und IngredientsPage.test.tsx (gefunden von einem Sichter-Subagenten), danach - trotz des ersten Vorfalls - zwei weitere in countermeasures.md auf den umbenannten Retro-Berichtsabschnitt (gefunden erst in der Nachpruefung).
  Warum: Die Umbenennung fuehlt sich lokal an: Man sieht die Datei, die man aendert. Der Verweis liegt aber woanders und in einer anderen Notation - eine ESLint-Meldung, ein C#-Kommentar, ein Wirksamkeitskriterium. anchors.py prueft Anker, nicht Namen in Prosa; kein Werkzeug deckt diese Richtung ab.
  Regel: Vor dem Entfernen oder Umbenennen einer Nummer, eines Abschnittsnamens oder eines Ausgabe-Labels zuerst repoweit nach Verweisen darauf suchen - auch in Code, Config und Script-Ausgaben, nicht nur in Markdown. Erst danach aendern.
  CM-Bezug: CM-S124-3

- **[HOCH] [AGENT] [Kommunikation] LL-S124-2 – Pruefung behauptet, die ihren Gegenstand gar nicht pruefen konnte**
  Quelle: User
  Was: Auf die Frage, ob vor dem Abbruch wirklich alle Edits abgeschlossen waren, durchsuchte ich den Diff nach TODO/FIXME/TBD-Markern und gab das leere Ergebnis als Beleg fuer Vollstaendigkeit aus. Bei dieser Arbeit wurden nie solche Marker gesetzt - die Suche konnte gar nichts finden und belegte nichts. Der User deckte den Fehlschluss auf; die richtige Pruefung (Abgleich der vier Sichter-Berichte gegen den Ist-Zustand) foerderte dann einen offenen Befund zutage.
  Warum: Das Beduerfnis, eine Behauptung zu belegen, sucht sich das naechstliegende Werkzeug statt das passende. Ein gruenes Ergebnis fuehlt sich wie ein Beleg an, auch wenn der Test den Gegenstand nie beruehrt hat - das ist genau die Form, in der eine Pruefung still versagt (CM-S116-1).
  Regel: Vor dem Ausgeben eines Pruefergebnisses die Gegenfrage stellen: Haette diese Pruefung anschlagen KOENNEN, wenn der Fehler vorlaege? Lautet die Antwort nein, ist das Ergebnis kein Beleg und darf nicht als solcher praesentiert werden.
  CM-Bezug: neu

- **[MITTEL] [AGENT] [Kommunikation] LL-S124-3 – Fehlalarmquote auf dem bereits bereinigten Bestand gerechnet**
  Quelle: User
  Was: Nach der Sichtung von 44 Fundstellen meldete ich '40 von 44 legitim, also ~91 Prozent Fehlalarm' als Argument gegen einen schaerferen Hook. Die Zahl galt aber erst NACH der Korrektur der echten Faelle - die behandelten Treffer waren aus der Grundgesamtheit verschwunden. Auf dem urspruenglichen Bestand gerechnet lag die Quote bei 65-75 Prozent. Der User erkannte den Survivorship Bias.
  Warum: Wer eine Menge bearbeitet und danach misst, misst die Ueberlebenden. Die Reihenfolge Bearbeiten-dann-Zaehlen ist die natuerliche, und das Ergebnis stuetzt bequemerweise die Entscheidung, nichts weiter zu bauen.
  Regel: Eine Quote immer auf der Grundgesamtheit zum Messzeitpunkt bilden und den Zeitpunkt dazusagen. Wurde zwischendurch bereinigt, ist die Zahl vor der Bereinigung die aussagekraeftige - oder die Messung gilt ausdruecklich nur fuer den Rest.

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S124-4 – Befund aus einer Subagenten-Liste verloren, weil der naechste Bericht dazwischenkam**
  Quelle: Orchestrator
  Was: Von vier parallel arbeitenden Sichter-Subagenten trafen die Berichte zeitversetzt ein. Ein Befund des Docs-Sichters (process.md Noise-Filter) war bereits per grep verifiziert; dann kam der Bericht des Code-Sichters mit toten Verweisen herein, die Arbeit sprang dorthin, und der offene Befund kehrte nie zurueck. Aufgefallen erst zwei Runden spaeter durch eine Nachfrage des Users.
  Warum: Die Befundliste lebte nur im Gespraechsverlauf. Ein eingehender Bericht verdraengt die laufende Liste, ohne dass irgendwo sichtbar bleibt, was davon noch offen ist - und es gab keinen Abgleich am Ende.
  Regel: Bei mehreren parallel liefernden Subagenten die Befunde nach Eingang in einer sichtbaren Liste mit Status je Eintrag fuehren und vor dem Abschluss gegen den Ist-Zustand abgleichen - nicht im Kontext mitfuehren.
  CM-Bezug: neu

## Session 125 – 2026-08-28

- **[HOCH] [PROZESS] [Skill-Nutzung] LL-S125-1 – Zaehleinheit stillschweigend getauscht: Vorkommen als Sessions ausgegeben**
  Quelle: User
  Was: Als tragendes Argument dafuer, OBS-S124-1 zu behandeln, wurde gemeldet, das Prioritaeten-Modul habe "in 30 Session-Starts nie den Aufgaben-Slot bekommen". Gemessen hatte das Script 31 Vorkommen der Agenda-Injektion, verteilt auf 11 Session-Logs - eine Session enthaelt die Injektion mehrfach (Resume, /clear, manuelle --only-Aufrufe). Der User hielt die Zahl fuer zu hoch und fragte nach; die Nachmessung ergab 11 statt 30, und das Modul existierte ueberhaupt erst seit acht Sessions. Damit fiel das Hauptargument weg.
  Warum: Das Script zaehlte Treffer, die Aussage sprach von Ereignissen. Zwischen beiden liegt eine Aggregationsebene, die nie benannt und daher nie geprueft wurde. Der Fehler faellt nicht auf, weil beide Zahlen plausibel klingen und dieselbe Groessenordnung suggerieren.
  Regel: Vor dem Ausgeben einer gemessenen Zahl die Zaehleinheit ausdruecklich benennen (was genau ist ein Treffer?) und pruefen, ob sie die behauptete Einheit ist. Bei Treffern aus Logs zusaetzlich fragen, ob ein Ereignis mehrere Treffer erzeugen kann - Resume, Wiederholung, Duplikat im selben Log.
  CM-Bezug: neu

- **[MITTEL] [PROZESS] [Review] LL-S125-2 – Fertig gemeldet nach einer Gegenprobe, die nur einen Teil des Gegenstands beruehrte**
  Quelle: Orchestrator
  Was: Nach dem Bau von doc.py wurden drei Mutationen von Hand in die Scope-Logik gesetzt; zwei wurden von mehreren Tests gefangen, die dritte deckte eine Testluecke auf, die geschlossen wurde. Daraufhin wurde dem User "P1 steht" gemeldet, ausdruecklich mit dem Hinweis, die Gegenprobe sei gefahren. Der anschliessende Review durch drei Auditoren fand vier echte Fehler, die keine der Handmutationen beruehrt hatte - darunter einer, der genau die Fehlerklasse einbaute, gegen die das ganze Design entschieden worden war (eine stille Kuerzung in der Funktion, die stille Kuerzungen verhindern soll).
  Warum: Handmutationen treffen die Stellen, an die der Autor beim Mutieren denkt - dieselbe Auswahl, die schon beim Testschreiben gewirkt hat. Alle drei gesetzten Mutationen lagen in der Kernregel; alle vier gefundenen Fehler lagen an den Nahtstellen zwischen Regeln. Die Gegenprobe war also nicht falsch, sondern deckungsgleich mit dem bereits Getesteten - sie konnte per Konstruktion nichts Neues zeigen.
  Regel: Eine Gegenprobe rechtfertigt kein "fertig", solange sie nur dort mutiert, wo ohnehin Tests liegen. Vor der Fertig-Meldung fragen, welche Stellen die Mutationen NICHT beruehrt haben - typischerweise die Uebergaenge zwischen zwei Regeln, nicht die Regeln selbst. Ist das nicht abgedeckt, die Meldung entsprechend einschraenken statt sie zu verallgemeinern.
  CM-Bezug: CM-S116-1

- **[MITTEL] [PROZESS] [Doku] LL-S125-3 – Ausschlusskriterium nur an der neuen Option geprueft, nicht am Status quo**
  Quelle: User
  Was: Gegen den Vorschlag, die Session-Historie in die Commit-Nachricht zu verlagern, wurde eingewendet, die Konvention "Session NNN:" sei von niemandem erzwungen - eine ID-Vergabe darauf zu stellen waere ein Rueckschritt. Der User fragte zurueck, wer denn die bestehende Konvention erzwinge. Die Pruefung ergab: niemand. Die Session-Datei wird ebenfalls nur von einem Schritt in closing-session angelegt, kein Hook sichert sie ab, und der Lueckenfall ist im Bestand belegt (session_104 fehlte). Das Argument traf den Status quo genauso hart und fiel damit weg.
  Warum: Das Kriterium wurde ausschliesslich auf die neue Option angewandt. Was bereits laeuft, erscheint als gesetzt und wird nicht mehr gegen dieselbe Anforderung gehalten - der Status quo bekommt einen Vertrauensvorschuss, den er nicht verdient hat.
  Regel: Wird eine neue Option mit einem Kriterium verworfen (nicht erzwungen, nicht pruefbar, nicht robust), dasselbe Kriterium vor dem Aussprechen am bestehenden Verfahren pruefen. Faellt der Status quo auch durch, trennt das Kriterium die Optionen nicht und darf die Entscheidung nicht tragen.

- **[MITTEL] [TOOLING] [Bash/Permission] LL-S125-4 – Backticks im Bash-Argument zerstoerten den geschriebenen Tracker-Eintrag**
  Quelle: Orchestrator
  Was: Der Entscheidungstext fuer OBS-S124-1 wurde per obs.py set uebergeben, in doppelten Anfuehrungszeichen und mit Markdown-Backticks um Code-Bezeichner (`Fällig: jetzt`, `priorities`). Bash fuehrte die Backtick-Inhalte als Command-Substitution aus - sichtbar an Meldungen wie "Fällig:: command not found" -, und der Eintrag wurde mit geloeschten Passagen geschrieben. Das Script meldete Erfolg. Erst das anschliessende Nachlesen zeigte die Luecken; der Text musste neu gesetzt werden.
  Warum: Markdown-Backticks sind in Tracker-Texten die Normalform fuer Code-Bezeichner, und in doppelten Anfuehrungszeichen sind sie zugleich Bash-Syntax. Die Substitution schlaegt nicht fehl, sie ersetzt still durch Leerstring - Exit-Code 0, Erfolgsmeldung, beschaedigter Inhalt.
  Regel: Tracker-Texte immer in EINFACHEN Anfuehrungszeichen an die Scripte uebergeben; dort ist keine Substitution moeglich. Nach jedem Schreibvorgang mit Sonderzeichen den Eintrag einmal per get gegenlesen - die Erfolgsmeldung des Scripts sagt nichts ueber den Inhalt.

## Session 126 – 2026-08-28

- **[HOCH] [TOOLING] [Hook/Script] LL-S126-1 – Auswertung mit stummem Regex ausgegeben – Nullwerte als Befund präsentiert**
  Quelle: Orchestrator
  Was: Die Trend-Auswertung ueber die Retro-Perioden lief mit einem Regex, der ohne re.MULTILINE kompiliert war. Der Zeilenanker traf damit nur den Dateianfang, die Auswertung fand 0 Learnings in jeder Periode und gab eine vollstaendige Tabelle mit LL-Gewicht 0,0 und einer konstanten Kadenz von 20,0 aus. Die Zahlen wurden dem User gezeigt, bevor mir auffiel, dass sie nicht Null Learnings, sondern Null Treffer bedeuteten. Im selben Lauf ein zweiter Fall derselben Klasse: Der Trendvergleich erste-gegen-zweite-Haelfte lief ueber Perioden, in denen das OBS-Backlog noch gar nicht existierte, und mass damit dessen Abwesenheit als niedrigen Zufluss.
  Warum: Der Regex wurde aus jenga_score.py uebernommen, wo er zeilenweise angewandt wird; im neuen Script lief er per findall gegen den gesamten Dateitext. Die Uebernahme kopierte das Muster, nicht seine Anwendungsbedingung. Vor der Ausgabe gab es keinen Plausibilitaets-Check gegen einen bekannten Wert - jenga_score.py meldet fuer die laufende Periode 15 Findings, ein Abgleich haette den Nullbefund sofort widerlegt.
  Regel: Bevor eine selbstgebaute Auswertung ausgegeben wird, muss mindestens ein Wert gegen eine unabhaengige Quelle stimmen, die denselben Gegenstand zaehlt. Ein flaechendeckender Nullbefund ist bis zum Gegenbeweis ein Defekt der Messung, nicht ein Ergebnis. Und: Ein Trendvergleich darf nur ueber Zeitraeume laufen, in denen der gemessene Gegenstand existierte.
  CM-Bezug: CM-S116-1

- **[HOCH] [AGENT] [Kommunikation] LL-S126-2 – Score-Verteilung des Zuflusses behauptet, nur die Anzahl gemessen**
  Quelle: User
  Was: Zur Frage, wie viel Drain vor der Implementierung noch ansteht, habe ich den OBS-Zufluss gemessen - aber nur in ANZAHL der Eintraege (2,7 je Session) - und daraus eine Aussage ueber den SCORE abgeleitet ("zwei neue Eintraege mit Score 2 heben die Top-5-Summe wieder ueber die Schwelle"). Der Score war nie gemessen. Der User wies darauf hin, dass 2,7 Eintraege je Session nichts ueber deren Score sagen und es ebenso gut Kleinigkeiten sein koennten. Die nachgeholte Messung ergab Mittel 2,60 und Median 2,0 je Eintrag - die Empfehlung stimmte, aber aus Zufall, nicht aus Beleg.
  Warum: Der Trigger des Drains rechnet in Score, meine Messung lieferte Anzahl. Die fehlende Dimension ist mir nicht aufgefallen, weil das Ergebnis plausibel klang und in dieselbe Richtung zeigte wie die Vermutung. Das ist der Fall aus CM-S095-2: eine Empfehlung aus einem Raum, der nicht vollstaendig zerlegt war - hier fehlte die zweite Achse der Groesse, die im Mechanismus selbst steht.
  Regel: Wenn ein Mechanismus in einer bestimmten Groesse rechnet, muss die Messung, die eine Aussage ueber ihn stuetzt, in genau dieser Groesse erfolgen. Eine Ersatzgroesse (Anzahl statt Score) ist erst zulaessig, wenn ihr Zusammenhang mit der Zielgroesse selbst belegt ist.
  CM-Bezug: CM-S095-2

- **[MITTEL] [AGENT] [Kommunikation] LL-S126-3 – Bestehenden Mechanismus als Präzedenz angeführt, ohne seinen Adressaten zu prüfen**
  Quelle: User
  Was: Beim Entwurf der Regel gegen nackte Tracker-IDs habe ich modul_open_questions aus session-agenda.py als Praezedenzfall angefuehrt: Dort steht der Fragetext im Ausgabeblock, mit der Begruendung, ein blosser Einzeiler sei wirkungslos gewesen. Ich las das als bereits geloesten Fall desselben Problems und baute eine Empfehlung darauf. Der User korrigierte: Das Modul schreibt in den AGENTEN-Kontext, nicht an ihn. Es loest damit eine Voraussetzung des Pitches - der Agent hat den Inhalt billig zur Hand - aber nicht den Pitch selbst. Auf derselben Verwechslung stand mein Vorschlag, den Titel mechanisch in die td-due-Ausgabe aufzunehmen; er ist danach entfallen.
  Warum: Die Begruendung im Docstring des Moduls passte woertlich auf mein Problem ("es setzte voraus, dass jemand die Datei aufschlaegt"), und ich habe die Passung des Textes fuer eine Passung des Falles genommen, ohne zu pruefen, wer der Empfaenger der Ausgabe ist. Zwei Ebenen - was der Agent weiss und was der User sieht - waren im selben Satz zusammengefallen.
  Regel: Wird ein bestehender Mechanismus als geloester Praezedenzfall angefuehrt, ist vor der Uebernahme sein Adressat zu bestimmen: Wer liest die Ausgabe, und ist das derselbe, dem im neuen Fall etwas fehlt? Eine passende Begruendung belegt keine passende Konstellation.
  CM-Bezug: CM-S064-1

- **[MITTEL] [PROZESS] [Kommunikation] LL-S126-4 – Regel in einer Ausschlussliste hob eine andere Regel derselben Liste auf**
  Quelle: User
  Was: Fuer den Inhalt der Abschluss-Commit-Nachricht entstand eine Liste dessen, was NICHT hineingehoert. Ein Punkt strich die Aufzaehlung erzeugter Tracker-IDs, weil die Session bereits in der ID steht. Ein anderer Punkt derselben Liste verlangte fuer Inhalte mit eigenem Ablageort "nur die ID als Zeiger" - und fuehrte damit genau die Aufzaehlung wieder ein, die der erste gestrichen hatte. Der User bemerkte den Widerspruch; ohne den Hinweis waere die Regel mit einer eingebauten Gegenregel in den Skill gewandert.
  Warum: Die beiden Punkte entstanden aus verschiedenen Blickrichtungen - einer aus der Frage "was ist redundant", der andere aus "wo lebt der Inhalt" - und wurden nacheinander formuliert, ohne sie gegeneinander zu lesen. Die Liste wurde als Sammlung gepruegt, nicht als System: jeder Punkt fuer sich plausibel, das Zusammenspiel ungeprueft.
  Regel: Eine neu aufgestellte Regelliste wird vor der Uebernahme paarweise gegengelesen: Hebt ein Punkt einen anderen auf, verengt oder erweitert er ihn? Erst danach in eine Guideline oder einen Skill uebernehmen.

- **[MITTEL] [PROZESS] [Doku] LL-S126-5 – Migrationsnotiz statt Zustandsbeschreibung in einen Docstring geschrieben**
  Quelle: User
  Was: Beim Herausloesen von repo_kontext.py aus obs_parse.py habe ich in beide Docstrings erklaert, was NICHT mehr dort liegt und wo es frueher lag ("Ausdruecklich NICHT hier: Repo-Wurzel und Session-Nummer ... bis S126 lagen sie hier"). Der User verwarf das: Wer die Datei heute neu schriebe, haette den Satz nicht geschrieben - man begruendet keine Imports. Beide Stellen sind entfernt bzw. auf die zeitlose Begruendung gekuerzt.
  Warum: Ich habe die Doku aus der Perspektive des Umbaus geschrieben statt aus der des kuenftigen Lesers. Fuer den Umbauenden ist die Abwesenheit auffaellig und erklaerungsbeduerftig, fuer jeden spaeteren Leser ist sie einfach der Zustand. Dieselbe Klasse trifft auch Migrationsspuren in Kommentaren und Skills, nicht nur Docstrings.
  Regel: Test vor dem Schreiben einer Erklaerung in Doku, Docstring oder Kommentar: Haette jemand, der die Datei heute ohne Kenntnis der Vorgeschichte neu anlegt, diesen Satz geschrieben? Wenn nein, ist es eine Migrationsnotiz und gehoert in die Commit-Nachricht oder den Tracker-Eintrag, nicht an den Ort der Wirkung. Ausnahme: Der Satz erklaert, warum etwas Vorhandenes so aussieht, wie es aussieht.

- **[MITTEL] [AGENT] [Skill-Nutzung] LL-S126-6 – recall-session ungemessen als zu teuer verworfen und auf die Rohdateien ausgewichen**
  Quelle: Orchestrator
  Was: Beim Sichten der Session-Datei-Zugriffe fuer die Entscheidung ueber die Session-Historie fiel auf: In einem der geprueften Faelle waehlte ein Agent die Session-Einzeldateien statt des Skills recall-session, mit der ausdruecklichen Begruendung, das sei billiger - ohne die Kosten eines der beiden Wege gemessen zu haben. Mit dem Loeschen der Einzeldateien in dieser Session ist der Ausweichweg fort; die woertliche Rekonstruktion einer frueheren Session laeuft jetzt allein ueber recall-session.
  Warum: Eine Kostenvermutung ueber ein Werkzeug wurde wie gesichertes Wissen behandelt. Genau die Klasse aus CM-S114-2, nur in der Gegenrichtung: Dort wurden Volltexte gelesen, weil das gezielte Werkzeug fehlte; hier existierte es und wurde aufgrund einer Schaetzung gemieden.
  Regel: Wird ein bereitstehendes Werkzeug wegen vermuteter Kosten uebergangen, ist die Vermutung vor dem Ausweichen zu pruefen - ein Probeaufruf genuegt. Faellt die Pruefung aus, wird das Werkzeug genutzt, nicht umgangen.
  CM-Bezug: CM-S114-2

- **[MITTEL] [TOOLING] [Hook/Script] LL-S126-7 – Trailer-Formatierung am falschen Beispiel verifiziert**
  Quelle: Orchestrator
  Was: Fuer den neuen Abschluss-Trailer habe ich geprueft, ob git log --format=%(trailers:key=...) funktioniert - aber an Co-Authored-By, das im letzten Absatz der Nachricht steht. Der eigene Trailer Session-Ende landete in einem eigenen Absatz davor. Git parst ausschliesslich den LETZTEN Absatz als Trailer-Block, also lieferte der Abruf leer. Aufgefallen erst nach dem Abschluss-Commit, beim Nachsehen der eigenen Ausgabe. Die Nummernableitung selbst war nie betroffen (sie greppt ueber %B), wohl aber der Befehl, den ich im kaizen-Skill dokumentiert hatte.
  Warum: Die Verifikation lief an einem vorhandenen Trailer statt an dem, der gebaut wurde - dieselbe Klasse wie LL-S126-1 in dieser Session: Ein Mechanismus wurde an einem Fall geprueft, der die entscheidende Eigenschaft des Zielfalls nicht hatte. Verschaerfend die Fehlerform: Der eine Weg (grep) funktionierte weiter, der andere (Trailer) lieferte still leer - eine Kombination, die ohne gezieltes Nachsehen nicht auffaellt.
  Regel: Eine Verifikation muss an genau dem Artefakt laufen, das spaeter benutzt wird - nicht an einem gleichartig aussehenden. Wenn zwei Abrufwege auf dieselbe Information zeigen und nur einer bricht, ist der stille Weg der gefaehrliche: Beide sind zu pruefen.
  CM-Bezug: CM-S116-1
