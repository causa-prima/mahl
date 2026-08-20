# Kaizen-Prozess

<!--
wann-lesen: Beim Schreiben eines lessons_learned-Eintrags (Impact/Kategorie/Kontext bestimmen),
            beim Starten einer Retro, beim Bewerten einer Maßnahme.
-->

## Was gehört in lessons_learned?

Ein Eintrag ist sinnvoll wenn er ein **Agenten-Verhalten** beschreibt das wieder auftreten könnte.

**Nicht dokumentieren:**
- Infrastruktur- oder Setup-Fehler die durch eine Konfigurationsänderung dauerhaft behoben sind
  → Dieses Wissen gehört in `docs/process/dev-workflow.md`, eine Config-Datei oder einen Code-Kommentar
- Reine Fakten über Tool-Verhalten ohne Konsequenz für künftiges Agenten-Verhalten
- Fehler aus einer **einmaligen Situation, die grundsätzlich nicht wiederkehren kann** und unter der **keine wiederkehrende Tätigkeits-Klasse** liegt (z.B. ein Fehler, der nur an eine einmalige Repo-Umstellung gebunden war)
  → Achtung Abstraktionsebene: Liegt unter der einmaligen konkreten Auslösung eine wiederkehrende Klasse (z.B. „programmatische String-Transforms", „Datei-Renames"), ist der Eintrag sinnvoll – aber auf der **Klassen-Ebene** formuliert, nicht auf der Einmal-Situation.

**Test vor jedem Eintrag (alle drei Fragen müssen mit Ja beantwortet werden, sonst kein Eintrag):**
1. „Könnte ein Agent diesen Fehler wieder machen – auch wenn die Konfigurationsänderung schon vorhanden ist?" (Nein → Infra-/Config-Noise)
2. „Kann die auslösende Situation grundsätzlich wiederkehren – bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter?" (Nein → einmalige Situation, kein Eintrag)
3. „Beschreibt die *Regel* ein **Agenten-Verhalten oder -Urteil**, das schiefgehen kann – oder ist sie eine **statische Tatsache**, die man einmal nachschlägt und danach kennt?" (statische Tatsache → Noise, gehört nach `docs/process/dev-workflow.md` oder in einen Code-Kommentar)

> Warum Frage 3 nötig ist: Frage 1 allein trennt Tool-Fakten nicht sauber ab – ein Agent „könnte" fast jeden Tool-Fakt wiederholen, weil er Tool-Verhalten nicht auswendig kennt, womit Frage 1 fast nie Nein ergibt. Erst Frage 3 zieht die Linie: wiederkehrendes Verhaltensmuster bleibt, nachschlagbare Tatsache ist Noise.

Alle drei Ja → dokumentieren (Frage 2: auf Klassen-Ebene formulieren, nicht auf der einmaligen Auslösung).

---

## Zwei Brillen: lessons_learned vs. observations

Das Kaizen-System hat zwei Tracks, **keine Partition** – dieselbe Sache kann aus zwei Blickwinkeln in beiden Dateien stehen:

- `lessons_learned.md` = **konkrete schlechte Ausgänge dieser Session** (Symptome: Rework, Fehler, verschwendeter Aufwand, Defekt). Speisen den Jenga-Score.
- `observations.md` = **vorausschauende System-Design-Beobachtungen** (Optimierungen, Reibung, „so wäre es besser"). Speisen Jenga **nicht**.

**Billige Erfassungs-Tests (gelten bei `closing-session`, auch für user-gemeldete Punkte):**
- LL: „Ist diese Session ein **konkreter schlechter Ausgang** aufgetreten – Rework, Fehler, verschwendeter Aufwand, ein Defekt?" → ja → `lessons_learned.md` (mit Impact). Der Noise-Filter (die 3 Fragen oben) gilt für ALLE Einträge.
- Observations: „Eine **vorausschauende** Notiz, wie das System besser wäre?" → `observations.md`.
- **Beides wahr → beides**, per `Bezug:` verlinkt.

**Quer-Bewegung (kein Duplikat-Fehler):** Eine Beobachtung darf als **Symptom** in `lessons_learned.md` UND als **Design-Fix** in `observations.md` stehen, über `Bezug:` verbunden. Das ist dieselbe Sache aus zwei Blickwinkeln, keine Duplikat-Panne.

**Erfassung ist billig, Klassifikation ist teuer:** Erfassung ist lokal/stabil und braucht kein Gesamt-Prozesswissen. Die teure, argumentierbare Klassifikation – Konformanz-Slip vs. Design-Mangel, beste Antwort, Quer-Bewegung LL↔Backlog – passiert in der **Retro** und ist dort jederzeit revidierbar. Die harte Frage „verstößt es gegen den Prozess?" ist **kein Erfassungs-Test**, sondern Retro-Root-Cause.

---

## observations.md – Beobachtungs-Backlog

Der proaktive Track für System-Design-Beobachtungen. **Eintrags-Format, ID-Schema, Impact/Häufigkeit-Werte und Erfassungs-Regel stehen kanonisch im Header von `docs/kaizen/observations.md`** (dort werden Einträge geschrieben) – hier nicht duplizieren.

---

## Gefahr & Kandidaten-Bewertung

**Gefahr ist eine Eigenschaft eines KANDIDATEN** (der geplanten Änderung), **nicht der Beobachtung/des Findings.** Sie ist daher kein Header-Feld in `observations.md`, sondern wird bei der **Kandidaten-Auswahl** abgewogen. Dieselbe Disziplin gilt beim Wählen einer **CM** für ein LL-Muster.

- **Sorgfalt UND Beweisbarkeit skalieren mit Gefahr:** Je höher die Gefahr eines Kandidaten, desto wichtiger der nachträgliche **Beweis**, dass durch die Änderung **kein neues/anderes Problem** entstanden ist (Verifikation / Pilot / Vorher-Nachher).
- **Evaluierungs-Gate:** Nicht-triviale oder höher-Gefahr-Antworten werden **NICHT sofort** umgesetzt → Kandidaten erarbeiten, abwägen (für OBS beim **Drain**, für ein LL-Muster bei der **CM-Wahl**), dann begründet committen. Trivial / niedrige Gefahr → sofort umsetzen + Einzeiler.
- **Vertrauens-/Ermüdungs-Multiplikator:** Der wahre Impact einer Agent-Auffälligkeit ist **größer als ihr lokaler Defekt** – jede Auffälligkeit erodiert zusätzlich das User-Vertrauen, was mehr manuelle Kontrolle und Ermüdung nach sich zieht (sich selbst verstärkender Kreis). Konsequenzen für die Kandidaten-Bewertung: (1) den Multiplikator zum lokalen Impact **hinzuzählen** – scheinbar „geringe" Auffälligkeiten summieren sich über diesen Kanal; (2) bei gleichem lokalem Impact schlägt der **strukturelle/mechanische Guard (Poka-Yoke)** den Wachsamkeits-Guard („der Agent passt besser auf" / „der User fängt es beim Mitlesen ab"), weil letzterer den Ermüdungskreis nicht bricht, sondern speist. Priorisierungs-Linse, kein Einzel-Fix.

---

## Backlog-Abbau: kontinuierlicher Drain (nicht Retro)

Offene OBS (Status `NEU`) werden **kontinuierlich pro Session** abgebaut, **nicht** in der Retro. Grund: OBS-Verarbeitung ist *generatives Design* (Reibung → Kandidaten → lohnt-sich-Entscheidung), die Retro ist *diagnostisch* (Symptom → Muster → Root Cause). Design in den Diagnose-Container zu zwingen, lässt die Retro mit OBS-Themen volllaufen (OBS-S095-1).

**Trigger:** Der SessionStart-Hook schlägt jede Session einen Drain-Satz vor (un-vergessbar – Disziplin allein scheiterte). Orchestrator schlägt vor, User bestätigt/vertagt. Der Zustand ist **sichtbar** („N vorgeschlagen, Backlog bei M, davon K behandlungswürdig"), aber **ohne Strafscore** – OBS speisen Jenga nicht.

### Score und Behandlungswürdigkeit (S122)

**Score = Impact × Häufigkeit** – Gesamtschaden = Schaden je Vorfall × Zahl der Vorfälle. Die Werte sind nicht frei gewählt (mechanisch in `obs_parse.py`, `IMPACT`/`FREQ`):

| | gelegentlich (1) | häufig (2) | dauerhaft (4) |
|---|---|---|---|
| **GERING (0)** | 0 | 0 | 0 |
| **MITTEL (1)** | 1 | 2 | 4 |
| **HOCH (3)** | 3 | 6 | 12 |
| **KRITISCH (9)** | 9 | 18 | 36 |

**GERING = 0**, weil die Impact-Rubrik GERING als „*keine* Qualitäts- oder Prozessfolge" definiert – nicht als „wenig". Was folgenlos ist, bleibt es auch gehäuft, und darf in einer Cluster-Summe nichts beitragen; fünf folgenlose Einträge sind zusammen immer noch folgenlos. Die Impact-Stufen springen um Faktor 3 (qualitativ verschieden, nicht linear), die Häufigkeit verdoppelt je Stufe. Eine naheliegende lineare Skala (1–4 × 1–3) scheitert daran, dass `GERING × dauerhaft` dann gleichauf mit `HOCH × gelegentlich` läge – ein folgenloses Dauerärgernis so schwer wie ein seltener schwerer Befund.

**Behandlungswürdig ab Score 2** = `MITTEL × häufig`: die kleinste Kombination, in der beide Dimensionen über der Bagatellstufe liegen. Darunter kostet die Einzelbehandlung mehr, als sie einbringt – solche Einträge verlassen den Pool über die Alters-Lane, nicht die Wert-Lane.

**Einheit = Cluster oder Einzeleintrag.** Einträge, die sich **in einem Zug miterledigen lassen** (Feld `- Zusammen-erledigen:`, Pflichtangabe bei der Erfassung), bilden über die transitive Hülle eine Einheit mit summiertem Score; sie wird gemeinsam priorisiert **und gemeinsam bearbeitet**. Maßstab ist **Bearbeitungs-Kolokation**, nicht Problem-Identität:

> *Wenn ich A bearbeite – liegt B dann ohnehin offen vor mir, und kostet es dadurch deutlich weniger?*

Typisch trifft das zu, wenn dieselben Artefakte in ähnlicher Weise berührt sind oder dieselbe Sache betroffen ist. **Nicht** gemeint sind: (a) zwei Einträge, die *dasselbe* Problem beschreiben – die gehören **konsolidiert** (s. unten), nicht geclustert; (b) eine **Vorfrage**, die vor dem anderen zu entscheiden wäre – eine Reihenfolge-Abhängigkeit macht nichts billiger; (c) bloße Themen-Ähnlichkeit ohne gemeinsames Artefakt.

Beim Aufgreifen ist die Zusammengehörigkeit am Volltext zu prüfen und ein nicht tragendes Mitglied herauszulösen (es behält seinen Einzel-Score) – die teure Beurteilung gehört in den Drain, nicht in die billige Erfassung. Kanten zu erledigten Einträgen bilden keine Einheit, bleiben aber als Kontext auffindbar: Ein neuer Eintrag am selben Artefakt sagt, dass die frühere Lösung dort unvollständig war.

*Reichweite:* Cluster entstehen vor allem im Rückstau. Bei gesundem Backlog sind verwandte Einträge selten gleichzeitig offen (der S122-Bestand trug genau einen echten Cluster, aus Einträgen über fünf Sessions hinweg) – das Cluster-Scoring ist daher überwiegend ein Altlast-Werkzeug, das `Zusammen-erledigen:`-Feld dagegen dauerhaft nützlich.

### Lanes und Trigger

**Wie viele pro Session:** Der Satz zeigt **alle** behandlungswürdigen Einheiten – ungedeckelt. Ein Deckel begrenzte nur den Vorschlag, nicht die Arbeit, und versteckte damit Behandlungswürdiges; für verdauliche Portionen sorgt der Skill, der wenige Einheiten auf einmal vorlegt. Die **Backlog-Größe steuert bewusst nichts**: Sie misst Menge, nicht Wert.

**Lanes des Drain-Satzes:**
- **Wert-Lane:** behandlungswürdige Einheiten nach Score (Hauptbudget).
- **Alters-Lane:** **alle** Einträge älter als `ALT_AB` = **15 Sessions**, sonst das älteste (1 Slot) – gezwungen zur Entscheidung → Anti-Starvation. Alter = aktuelle Session − Erfassungs-Session (aus der OBS-ID). Der Vollzugriff ist nötig, weil mehr als ein Eintrag pro Session nachaltert; ein Slot je Drain führte den Zufluss nicht ab. **`ALT_AB` steuert nicht den Durchsatz** – der entspricht im Gleichgewicht dem Zufluss, unabhängig von der Grenze – sondern den **stehenden Bestand** ≈ Zufluss × `ALT_AB` (bei ~1,4 nicht-behandlungswürdigen Einträgen je Session also ~20).
- **Wiedervorlage-Lane:** fällige geparkte Items (s. „Drei Ausgänge"), garantiert und außerhalb des Budgets.
*(Offene Fragen hingen bis S116 als vierte Lane hier mit dran; seit S117 sind sie ein eigenes Modul der Session-Agenda – s. unten.)*

**Trigger – wann beansprucht der Drain die Session?** Zwei Lanes, zwei Auslöser, ODER-verknüpft (`obs-drain.triggers()`):
1. **Wert:** Summe der **Top-5**-Einheiten ≥ **9**. Die Kappung bei 5 ist die gemessene Kapazität einer Drain-Session (S109…S121: 7/5/5/5/3/1/3): Was mehr wert ist, als eine Session abarbeiten kann, darf nicht mittriggern – sonst löst eine lange Liste Bagatellen dieselbe Summe aus wie ein schwerer Befund. Die **9** = `KRITISCH × gelegentlich`, der kleinste Einzelbefund, der eine Session allein rechtfertigt. Gedeckelt ist nur die Trigger-*Frage*, nicht der Satz.
2. **Alter:** ≥ **4** Einträge über `ALT_AB`. Ohne eigenen Auslöser hinge die Alters-Lane am Wert-Trigger und käme genau dann nie zum Zug, wenn sie am nötigsten ist – wenn nur noch Bagatellen übrig sind.

**Warum nicht die Backlog-Größe** (bis S121: `B ≥ 13`): Sie misst Menge statt Wert, und sie ist selbsterhaltend – jede Drain-Session erzeugt neue Einträge und hält B damit über der Schwelle. Zwischen S112 und S121 kam so zehn Sessions lang keine Feature-Arbeit mehr dran.

**Same-Artefakt-Kolokation:** Berührt ein anderes offenes OBS dieselbe Datei (Skript/Hook *oder* Skill/Doc), Mitnahme erwägen – spart Kontext-Laden, vermeidet Konflikt-Fixes über Sessions, bündelt teure Doc-QA. Verhältnis zu `Zusammen-erledigen:`: Beide fragen nach Bearbeitungs-Kolokation, auf verschiedenen Wegen – die Kolokation **mechanisch** (gleiche Datei, aus dem Text erkannt), als bloßer Hinweis; das Feld **beurteilt**, und es trägt auch über Dateigrenzen (dieselbe Sache in mehreren Dateien). Nur das Feld bildet die Einheit.

**Drei Ausgänge je Item:** umsetzen / **verwerfen** (mit Grund → Archiv) / **aufschieben** → `IN BEOBACHTUNG bis S<NNN>` (mit Grund + **Pflicht-Wiedervorlage**: ab dieser Session kommt das Item automatisch zurück in den Drain). Geparkte Items fallen bis dahin aus dem Pool; zum Termin injiziert `obs-drain.py` sie als fällige Wiedervorlage. Fehlt das `bis S<NNN>`, gilt das Item **sofort** als fällig (+ Warnung) – so kann ein geparktes Item nie still liegenbleiben. Für event-basierte Reaktivierung („wieder aktiv wenn X") zusätzlich eine Re-Trigger-Notiz; der Termin bleibt der verlässliche Backstop.

**Bias-Auslöschung (Relevanz wird zweimal beurteilt):** heiß bei der Erfassung (Bias *für* Aufnahme), kalt bei der Behandlung (Bias *zur* Abwertung) – entgegengesetzt, daher kalibrierter zusammen. Damit die kalte Abwertung nichts Wertvolles killt, wendet der Drain (Skill `draining-observations`, Schritt „**Entscheiden**") den **Kalt-Abwertungs-Prüfsatz** an.

**Vorprägung (Anker-Bias, getrennt vom Obigen):** Schon genanntes Lösungswissen – vom User geäußerte Maßnahmen, vermutete Ursachen, Analogieschlüsse – wird nicht getilgt (Informationsverlust) und nicht in die Beobachtung gemischt, sondern steht im optionalen Feld `- Vorprägung:`. Es wird beim normalen `obs.py get` **nicht mitgelesen**, nur als Hinweis angekündigt; Abruf per `--vorprägung`, und zwar erst **nach** eigener Kandidatenbildung. Begründung (S115): Eine Verifikationspflicht *nach* dem Lesen kommt zu spät – wer den Volltext gesehen hat, ist geprägt, unabhängig davon, was die Regel danach fordert. Umgekehrt wäre stilles Verbergen so schädlich wie Tilgen, deshalb sind Hinweis im `get` und `+Vorprägung`-Marker im Drain-Satz Pflicht. Der Inhalt ist zudem **agentenformuliert** und daher beim Drain gegen das tatsächliche Ziel des Users zu verifizieren, nicht als Auftrag zu lesen – genau daran ist der S115-Drain zunächst gescheitert.

**Durchführung:** Skill `draining-observations` (guardrailed Discovery + Entscheidung).

**Aufgelöste Einträge** (Status `UMGESETZT` oder `VERWORFEN`) → nach `docs/kaizen/archive/observations_archive.md` verschieben, damit die Live-`observations.md` scannbar bleibt. Das übernimmt **mechanisch** `python3 .claude/scripts/obs-archive.py` (kein Hand-Cut/Paste); solange es aussteht, listet der Drain-Satz sie als **Hygiene-Reminder**.

### Rolle in der Retro

Die Retro behandelt OBS nicht (das macht der Drain), berührt sie aber an einer Stelle:
- **Verlinkte OBS als LL-Input:** Beim Root-Causing eines LLs die per `Bezug: LL-…` daran hängenden OBS als **Design-Input** mitdenken (Zwei-Brillen-Quer-Bewegung). Die Suche ist **ID-gezielt** (`Bezug: LL-<diese-ID>`), daher auch im Archiv (`docs/kaizen/archive/observations_archive.md`) eindeutig – kein Relevanz-Scan über alle Einträge, nur die Treffer auf genau dieses LL.

---

## Session-Agenda: was verlangt zum Session-Start eine Entscheidung?

Der SessionStart-Hook ruft `python3 .claude/scripts/session-agenda.py` (Module: `--list`,
einzeln abrufen: `--only <name>`). Ziel ist **Fokus**, nicht Tokensparen – ein Session-Start mit
mehreren konkurrierenden Aufträgen zeigt in keine Richtung.

Ausgegeben wird erst der **Rahmen** (`principles`, Allow-Liste) – über Sessions unverändert und
beim Lesen überspringbar –, danach die **Agenda**. Sie steht am Schluss, direkt vor der ersten
Nachricht des Users: Das einzig session-spezifische Stück gehört an die Stelle, an der es am
ehesten wirkt. Die Agenda enthält zusammenhängend:

1. **Zustand** – Phase, Story, nächster Lauf. Drei Zeilen, ohne Titel und ohne Kurzfassung.
2. **Nächste Aufgabe** – genau *eine*, nach der Rangfolge unten. Ihr Text ist **buchstäblich**
   die Ausgabe von `--only <name>` für dieses Modul; keine zusammenfassende Kopfzeile davor,
   die den Inhalt darunter doppelte. Umgekehrt heißt das: Jeder Modulinhalt muss ohne
   Rahmenzeile sagen, worum es geht und was zu tun ist.
3. **Einzeiler** – je unterdrücktem Modul eine Zeile **mit seinem Messwert** (`Backlog 21
   drainbar`, `Jenga 89`). Ein unterdrückter Block darf nie verschwinden: Man kann nicht
   anfordern, wovon man nicht weiß, dass es existiert, und der User übersteuert regelmäßig.
   Der Rang steht im **Label** des Abschnitts („Nachrangig – nicht Gegenstand dieser Session,
   außer der User sagt es an"), nicht in der Trennerform: Trenner markieren die *Grenze* (ohne
   den unteren liefe der Abschnitt optisch in der Aufgabe weiter), Labels den *Rang*. Ein
   neutrales Label wie „Ebenfalls offen" las sich dagegen gleichrangig zur Aufgabe.

**Rangfolge** (hier kanonisch, mechanisch in der `MODULE`-Liste des Scripts):

| Rang | Modul | Beansprucht, wenn |
|------|-------|-------------------|
| 1 | `retro` | Jenga ≤ 0 |
| 2 | `obs-drain` | `triggers()` erfüllt – Top-5-Score ≥ 9 oder ≥ 4 Einträge über 15 Sessions alt |
| 3 | `priorities` | ein AGENT_MEMORY-Punkt trägt `Fällig: jetzt` |
| 4 | `next-run` | die aktuelle Story hat einen offenen Lauf |

`open-questions`, `td-due` und `ungeplante-szenarien` beanspruchen **nie** – sie verlangen eine
Entscheidung, keinen Arbeitstag; als Aufgabe verdrängte eine 34 Sessions alte Frage eine
laufende Story.

**`priorities` zeigt nur den obersten Punkt voll**, den Rest als Titel + Fälligkeit mit Zeiger
auf `AGENT_MEMORY.md`. Die Liste ist ein Terminplan, kein Auftrag: Neun Punkte im Volltext –
davon aktuell fünf mit `Fällig: jetzt` – wären wieder genau die konkurrierenden Aufträge, gegen
die die Rangfolge gebaut ist. Voll gezeigt wird der erste `jetzt`-Punkt, weil `jetzt` der
Auslöser ist; ohne einen solchen (Übersteuerungs-Pfad `--only priorities`) der erste überhaupt.

**Warum `next-run` story-gebunden auflöst und trotzdem nichts verschwindet:** Ein Szenario ohne
`# @run-N` gilt in `next_run.py` als eigener Einzel-Lauf (Rückwärtskompatibilität für
ungeclusterte Storys). Ohne Story-Filter meldete die Agenda deshalb querschnittliche Szenarien
als offene Läufe, obwohl ihre Feature-Datei den Scope ausdrücklich zurückstellt – eine
behauptete Arbeit. Mit Filter fielen sie ganz heraus – eine behauptete Vollständigkeit. Deshalb
beides: `next-run` beansprucht nur für die aktuelle Story, und `ungeplante-szenarien` macht
sichtbar, was geschrieben ist, aber auf keinem Weg vorgelegt wird. Der Status dort ist
**ungeklärt**, nicht „fällig".

**Warum der Drain nicht an der Backlog-Größe hängt:** s. „Lanes und Trigger" oben.

**Keine Extremschwellen** (etwa „sehr volles Backlog schlägt fällige Retro"): nicht
kalibrierbar – in S116 zeigten Backlog-Rückgang und tiefer Jenga-Stand gleichzeitig auf die
Retro, die Erklärungen sind konfundiert. Eine falsch gesetzte Schwelle kostet dasselbe wie keine
(eine formlose Übersteuerung), zusätzlich aber Pflege. Der User übersteuert informiert – die
Messwerte stehen in den Stubs.

**Ausfallverhalten:** Jedes Modul scheitert einzeln und sichtbar (Warnzeile mit Einzelabruf);
die Agenda läuft weiter. Ein Totalausfall wäre von „nichts zu tun" ununterscheidbar.

---

## Eintrag-Format (lessons_learned.md)

**Format-Skeleton, Tags-Liste, Beispiel und Erfassungs-Test stehen kanonisch im Header von `docs/kaizen/lessons_learned.md`** (dort, wo Einträge geschrieben werden) – hier nicht duplizieren. Definitionen der Tags: Abschnitte unten. Dieser Abschnitt ergänzt nur die Prozess-Regeln zu IDs/Quelle:

**ID für neue LL-Einträge:** `LL-S<NNN>-<n>` (3-stellige Session-Nummer, laufende Nummer innerhalb der Session). Platziert **HINTER den Tags** im Titel: `- **[HOCH] [PROZESS] [TDD] LL-S084-1 – Kurztitel**`. Vor `**[` würde die ID die Parsing-Regexes der Scripts brechen – daher zwingend hinter die Tags.

**Quelle-Markierung:** Pflicht-Zeile `Quelle: User | Subagent | Orchestrator` – Herkunft des Eintrags (KEINE Session – die steckt in der ID); `Subagent`/`Orchestrator` machen die Feedback-Quelle beobachtbar (z.B. ob Schicht-Implementer-Feedback ankommt). Keine Noise-Filter-Ausnahme: der 3-Fragen-Test gilt auch für user-gemeldete Einträge.

**Keine retroaktiven IDs:** Bestands-Einträge bekommen NICHT nachträglich IDs (bewusste Entscheidung).

---

## Impact-Kategorien

| Impact | Definition | Sofortreaktion | Maßnahmen-Anspruch |
|---------|-----------|----------------|-------------------|
| **KRITISCH** | Verursacht signifikanten Rework oder Qualitätsverlust; darf unter keinen Umständen wiederholt werden | **Andon-Cord:** Arbeit sofort stoppen, Ursache analysieren, Gegenmaßnahme definieren – erst dann weitermachen | Poka-yoke **Pflicht** – schwächere Maßnahmen reichen nicht |
| **HOCH** | Verzögert die Arbeit spürbar (Stunden Fehlsuche) **oder** gefährdet Qualität/Korrektheit (False-Green das echte Regression maskiert, Datenintegrität, falsche User-Entscheidung) | In derselben Session: Eintrag in `lessons_learned.md` + `countermeasures.md` | Poka-yoke anstreben wenn verhältnismäßig; sonst expliziter Schritt in Guideline oder Skill |
| **MITTEL** | Spürbare, aber begrenzte Prozess-/Qualitätsreibung mit engem Blast-Radius (vermeidbare Nacharbeit, mehrrundige Korrektur) | Eintrag in `lessons_learned.md` | Poka-yoke anstreben wenn einfach umsetzbar; sonst Eintrag in `principles.md` wenn wiederholt |
| **GERING** | Rein stilistisch/präferenzbedingt/kosmetisch – **keine** Qualitäts- oder Prozessfolge | Eintrag in `lessons_learned.md` | Keine Maßnahme nötig |

**Impact richtig bemessen (drei häufige Fehler):**
- **Schaden, nicht Neuheit:** Impact misst den potenziellen Schaden – **nicht**, ob bereits ein Prinzip/eine Gegenmaßnahme existiert. „Schon abgedeckt" ist **kein** Grund für GERING.
- **Klasse, nicht Einzelfall:** Bemessen wird die Problem-**Klasse**, falls sie **unbemerkt** bliebe – nicht der zufällig abgefangene Einzelfall (LLs werden ohnehin auf Klassen-Ebene formuliert).
- **„Schnell bemerkt" ist kein Impact-Kriterium:** Ein still-grüner/maskierter Fehler ist gerade *nicht* schnell bemerkt; „bemerkt" ≠ „geringer Schaden".

---

## Bereichs-Kategorien

Entscheidungskriterium: **Wo liegt der Fix?**

| Kategorie | Beschreibung | Beispiele |
|-----------|-------------|---------|
| **PROZESS** | Fix liegt im Workflow, in einem Skill-Schritt oder in der Session-Struktur | TDD-Verstoß, Skill-Schritt übersprungen, Evaluation+Implementierung kombiniert |
| **AGENT** | Fix liegt in der Art wie Sub-Agenten instruiert werden | Reviewer mit Iterations-Vorwissen, unklarer Prompt, falscher Kontext an Agent |
| **QUALITÄT** | Fix liegt im Code oder in der Test-Qualität (kein Prozess-Muster) | Primitive Typen statt Domain-Typen (isolierter Fall), fehlender Test |
| **TOOLING** | Fix liegt in Build, Infrastruktur, IDE oder Konfiguration | WSL/npm-Problem, CI-Konfiguration, Build-Pipeline |

> Wenn ein QUALITÄT-Problem wiederholt auftritt → Ursache ist meist PROZESS (Skill/Hook fehlt).

---

## Kontext-Tags

Beschreibt *was* konkret betroffen war – feiner als die Kategorie.

| Tag | Bedeutung |
|-----|-----------|
| `TDD` | Test-first-Disziplin, Red-Green-Refactor-Loop |
| `C#-Code` | C#-Implementierung, .NET-Guidelines |
| `TS-Code` | TypeScript/React-Implementierung, Frontend-Guidelines |
| `Bash/Permission` | Befehlsausführung & Permission-Hook (Allow-Liste, `--allow-once`, ad-hoc-Befehle) |
| `Mutation-Testing` | Stryker / QA-Gate (Score, Hashes, Coverage-Gate, Build-Lock für Mutation-Läufe) |
| `Testing` | Test-Infrastruktur & -Ausführung: Test↔Prod-Config-Parität, Test-Host/Provider (WebApplicationFactory, InMemory), E2E-Setup, Env-Propagation an gespawnte Test-Prozesse – abzugrenzen von `Mutation-Testing` (Score/Gate) und `TDD` (Red-Green-Loop) |
| `Hook/Script` | Selbstgebaute Projekt-Automatisierung (.claude-Hooks & -Scripts, Pfad-Matcher, Migrations-Scripts) |
| `Review` | Code- oder Dokument-Review-Prozess |
| `Agent-Prompt` | Formulierung & Mechanik von Sub-Agenten-Instruktionen |
| `Skill-Nutzung` | Anwendung oder Aufrufen von Skills (inkl. Kaizen-Prozess-Bookkeeping) |
| `Gherkin` | Feature-Files, Szenario-Formulierung |
| `Doku` | Guidelines, Docs, Entscheidungen pflegen |
| `Kommunikation` | Aussagen ggü. dem User – Verifikation vor Behauptung, Mechanismus-Präzision, Hypothesen-Framing |
| `Sonstiges` | Passt in keinen anderen Tag. **Staging-Area:** dünne/unklare Cluster (z.B. Build/Deps, Harness-Tool-Bedienung wie Edit/replace_all) hier parken – graduieren zu eigenem Tag, sobald ein Muster wächst |

**Pflege der Kontext-Tags:**
- Alle `Sonstiges`-Einträge werden in jeder Retro explizit gesichtet – Ziel: fehlende Tags ableiten
- Sehr häufige Tags (>30% aller Einträge) werden auf sinnvolle Aufteilung untersucht
- Neue oder geänderte Tags werden in dieser Datei dokumentiert

---

## Wann gehört etwas wohin?

| Ziel | Kriterium |
|------|-----------|
| `lessons_learned.md` | Jeder **konkrete schlechte Ausgang** (Symptom), immer |
| `observations.md` | Jede **vorausschauende** Beobachtung/Reibung, wie das System besser wäre (Optimierung). Beides wahr → beide Dateien, per `Bezug:` verlinkt |
| `principles.md` | Verhaltensregel die in jeder Session gilt; zu querschnittlich für eine Guideline/Skill |
| `countermeasures.md` | Jedes KRITISCH- oder HOCH-Finding sofort; MITTEL/GERING wenn Retro ein Muster aufdeckt |
| Guideline / Skill | Das Problem liegt an einem fehlenden oder falschen Schritt in einem konkreten Arbeitsablauf. Die Änderung ist direkt als Regel/Schritt in einem bestehenden Dokument formulierbar. (Meist wird zusätzlich ein `countermeasures.md`-Eintrag angelegt, der auf diese Änderung verweist.) |

**OBS-Antworten durch dasselbe CM-Eingangs-Gate:** Wird in der Retro eine OBS-Antwort beschlossen, läuft sie durch dasselbe CM-Eingangs-Gate wie ein LL-Finding:
- *Stehende, verifizierbare* Änderung (wiederkehrende Klasse, dauerhafte Leitplanke) → **CM** anlegen; das OBS schließt mit `Bezug: → CM-…` und Status `UMGESETZT`.
- *Einmal-Änderung ohne Tracking* → inline als `Maßnahme:` im OBS festgehalten, Status `UMGESETZT` (keine CM – sie wäre sofort obsolet).

**principles.md ⇄ countermeasures.md:** Ein Prinzip in `principles.md` ist die **Fließtext-Leitplanke** (wird jede Session geladen, keine Tags). Jedes Prinzip hat **zusätzlich** einen Tracking-Eintrag in `countermeasures.md` (Tupel Impact/Kategorie/Kontext + Status) – nur so bleibt es **evaluierbar** (BEWÄHRT/Rückfall) und wird von `retro_report.py` als „abgedeckt" erkannt. Die CM-Maßnahme verweist aufs Prinzip („Regel in principles.md dokumentiert"). BEWÄHRT-CMs bleiben in der Datei (Abschnitt „Bewährte Maßnahmen", Regressionserkennung). Konsequenz: Ein neu angelegtes Prinzip **immer** mit einem CM-Eintrag spiegeln – sonst ist es unsichtbar fürs Script und nicht bewertbar.

**CM-Eingangs-Gate (vor dem Anlegen einer Countermeasure):** Dieselbe Recurrence-Frage wie beim lessons-Eintrag, aber auf Maßnahmen-Ebene und vorgelagert (damit nicht Aufwand in eine Maßnahme fließt, die sofort obsolet wäre):

> „Liegt unter dem Finding eine **wiederkehrende Tätigkeits-Klasse**, die zwangsläufig Teil des normalen Arbeitsablaufs ist – oder war die Auslösung an eine **einmalige Umstellung gebunden, die grundsätzlich nicht wiederkehrt**?"

Keine verallgemeinerbare Klasse darunter → **keine CM** (sie wäre sofort obsolet, siehe Obsolet-Kriterien unten). Klasse vorhanden → CM auf **dieser** Klassen-Ebene formulieren, nicht auf der einmaligen konkreten Auslösung. Filtere nach Häufigkeit *nicht* (fast alles „kann schon wiederkehren") – entscheidend ist die strukturelle Wiederkehrbarkeit der Situation.

**Messwerkzeug bei CM-Definition (gilt für alle Maßnahmen):** Beim Festlegen einer Maßnahme zugleich bestimmen, **woran** ihre Wirksamkeit später beurteilt wird (sonst lässt sich BEWÄHRT/Rückfall nie belegen). Default-Kanal: lessons_learned + Session-Dateien – reicht für **selbst-berichtbare** Probleme. Adressiert die Maßnahme ein Verhalten, das der Agent **nicht** selbst als Problem loggt (z.B. Bash-Permission), muss schon jetzt eine **harte Datenquelle** benannt oder geschaffen werden (z.B. ein Log). Der Check ist leichtgewichtig: Default genügt meistens; nur die Lücke „nicht selbst-berichtet" erzwingt eine explizite Datenquelle.

---

## Retro-Trigger: Jenga-Score

Der Jenga-Score misst akkumulierten Problemdruck seit der letzten Retro.
Script `jenga_score.py` berechnet ihn aus der aktuellen `lessons_learned.md`.

**Start-Wert:** 100 Punkte

| Ereignis | Abzug |
|---------|-------|
| Session (immer) | -5 |
| KRITISCH-Finding | -25 |
| HOCH-Finding | -10 |
| MITTEL-Finding | -3 |
| GERING-Finding | -1 |

**Bei Jenga-Score ≤ 0:** Nächste Session beginnt mit einer Retro (Skill `kaizen`).

Scripts: `.claude/scripts/jenga_score.py` (nach jeder Session) und `.claude/scripts/retro_report.py` (zur Retro).
Nach einer Retro wird `lessons_learned.md` archiviert → Jenga-Score startet neu bei 100.

---

## Scripts

### jenga_score.py
Läuft nach jeder Session (im `closing-session`-Skill).
Input: `docs/kaizen/lessons_learned.md`
Output: Jenga-Score + Zähltabelle (Impact × Kategorie × Kontext)

### retro_report.py
Läuft zu Beginn jeder Retro (im `kaizen`-Skill).
Input: aktuelle `lessons_learned.md` + alle Archiv-Dateien in `docs/kaizen/archive/`
Output: Aggregation, Zeitreihen-Charts, Pattern-Kandidaten (Muster ≥2× im Fenster, gefiltert gegen `countermeasures.md`),
semantisches Clustering (ab 50 Einträgen), Trendanalyse je Kategorie.
Details: Kommentar-Header in `.claude/scripts/retro_report.py`.

---

## Archivierung (nach Retro)

Die aktuelle `lessons_learned.md` wird nach `docs/kaizen/archive/` verschoben.
Ablauf: Skill `kaizen`, Schritt 5.
Der Jenga-Score startet automatisch neu – `jenga_score.py` liest immer nur die aktuelle Datei.

---

## Umsetzung offener Maßnahmen

**Regel 1 – Sichtbarkeit:** Die **Countermeasure entsteht immer in der Retro** – sie ist der Tracking-Anker (Impact-Tupel + Status), ohne den `retro_report.py` weder Rückfall noch BEWÄHRT zählen kann. Die Frage ist nur, wo ihre **Umsetzung** wieder vorgelegt wird.

**Default: die Maßnahme in derselben Retro definieren.** Das Abwägen der Kandidaten für ein LL-Muster gehört laut Evaluierungs-Gate (Abschnitt „Gefahr & Kandidaten-Bewertung") ausdrücklich in die **CM-Wahl**, also hierher – nicht in den Drain. Ist sie definiert (konkreter nächster Schritt + überprüfbares Done-Kriterium), bekommt sie einen Punkt unter „Nächste Prioritäten" in `docs/AGENT_MEMORY.md`, als **Kurzzusammenfassung mit Verweis** auf `countermeasures.md` – keine Kopie, das Dokument wird bei jedem Session-Start vollständig injiziert.

**Ausnahme, begründungspflichtig:** Steht nicht die Umsetzung aus, sondern die **Antwort selbst** – es gibt mehrere ernsthafte Kandidaten, deren Abwägung eigene Recherche braucht –, bleibt die CM auf OFFEN und die Ausgestaltung geht als Eintrag in `docs/kaizen/observations.md` (mit `Bezug:` auf die CM) in den Drain. Der Grund ist im CM-Eintrag zu notieren; „ist noch nicht definiert" allein zählt nicht, sonst wird die Ausnahme zum bequemen Standardweg. **Preis dieser Route bewusst mitdenken:** Der Drain ist ratenbegrenzt und nach Impact × Häufigkeit priorisiert – ein Eintrag kann dort viele Sessions liegen. Für KRITISCH/HOCH-Findings, die laut „Wann gehört etwas wohin?" *sofort* eine Maßnahme verlangen, ist das in aller Regel zu langsam.

**Nicht** nach `AGENT_MEMORY.md` gehört eine unfertige Maßnahme: Die Datei hat außer der Injektion **keinen** Wiedervorlage-Mechanismus, ein Punkt ohne nächsten Schritt belastet dort nur die Prioritätenliste – das verwechselt Sichtbarkeit mit Wiedervorlage. (Diese Unterscheidung fehlte bis S116; die Regel stammt aus der Zeit vor dem kontinuierlichen Drain und kannte nur einen Ablageort.)

Falls inhaltlich zutreffend zusätzlich als technische Schuld (`docs/tech-debt.md`) oder offene Frage (`docs/open-questions.md`). Ablauf: `kaizen`-Skill, Schritt „Änderungen umsetzen".

**Regel 2 – Eskalation:** Eine Maßnahme die nach 2 Retros noch OFFEN ist, wird in der nächsten Retro als ESKALIERT präsentiert – im Skill-Schritt „Findings präsentieren & Freigabe einholen", Abschnitt F (gespeist aus dem Abschnitt „Eskalierte Maßnahmen" des `retro_report.py`-Outputs). Der User entscheidet dann: Umsetzung priorisieren oder bewusst verwerfen (Begründung in der Maßnahme notieren).

---

## BEWÄHRT-Kriterium für Countermeasures

Eine Maßnahme gilt als BEWÄHRT wenn:
- Die relevante Situation nach Einführung der Maßnahme mindestens 3× aufgetreten ist
- Kein Rückfall beobachtet wurde
- "Aufgetreten" = die Art der Arbeit, bei der das Problem hätte entstehen können, hat stattgefunden

Nachweis: Session-Dateien in `docs/history/sessions/` lesen und beurteilen, ob die relevante Arbeit stattfand.

> **Harte Daten bei nicht-selbstberichteten Verhaltensweisen:** Adressiert die Maßnahme ein Agenten-Verhalten, das der Agent **nicht selbst** als Problem in lessons_learned einträgt (z.B. Bash-Permission-Verstöße, abgelehnte Befehle), ist „keine neuen lessons_learned dazu" **kein** Beleg für BEWÄHRT (der Agent sieht es nicht als Problem). Stattdessen die primäre Datenquelle auswerten (z.B. `.claude/tmp/denied-commands.log`). Fehlt diese, ist **keine verlässliche/belastbare Aussage** möglich – dann den User fragen, ob ihm das Verhalten aufgefallen ist und wie mit dem Punkt weiter verfahren werden soll.

## Obsolet-Kriterien für Countermeasures

Ein Eintrag ist obsolet wenn:
- Das betroffene Tool oder die Technologie nicht mehr genutzt wird
- Der zugrundeliegende Prozess so fundamental umgebaut wurde, dass das Problem strukturell nicht mehr entstehen kann
- Es sich um eine einmalige Situation handelte, die grundsätzlich nicht wiederkehren kann

**Wohin mit VERWORFEN/OBSOLET-CMs:** Wie BEWÄHRT-Einträge **in `countermeasures.md` belassen** (Abschnitt „Verworfene / Obsolete Maßnahmen"), **nicht** in ein Archiv – damit die Verwerf-/Obsolet-Begründung beim Regressions-Scan auffindbar bleibt und der Eintrag bei Wiederauftreten zurück nach „Aktive Maßnahmen" kann. (Ein CM-Archiv existiert bewusst nicht; nur OBS und lessons_learned werden archiviert.)
