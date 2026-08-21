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

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

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
