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

**Trigger:** Der SessionStart-Hook schlägt jede Session einen Drain-Satz vor (un-vergessbar – Disziplin allein scheiterte). Orchestrator schlägt vor, User bestätigt/vertagt. Der Zustand ist **sichtbar** („N vorgeschlagen, Backlog bei M, gesund ≤ 8"), aber **ohne Strafscore** – OBS speisen Jenga nicht.

**Wie viele pro Session** (B = offenes `NEU`-Backlog): `clamp(round(0.4·B), 3, 7)`. Untergrenze 3 (matcht den Inflow ~3/Session), Obergrenze 7 (Session-Schutz bei Überlast), Gleichgewicht ~8. Zahlen aus dem realen Backlog kalibriert (S085–S095); später anpassbar. Steigt B über **12** (1,5× Gleichgewicht), markiert der Drain-Satz das Backlog sichtbar als *überfüllt* und mahnt, die Drain-Ausführung zu priorisieren (advisory, kein Strafscore).

**Lanes des Drain-Satzes:**
- **Wert-Lane:** Top nach Impact × Häufigkeit (Hauptbudget).
- **Alters-Lane:** das **älteste** `NEU`-Item (1 Slot), gezwungen zur Entscheidung → Anti-Starvation (reine Prioritäts-Ordnung verhungert das Tail sonst dauerhaft). Alter = aktuelle Session − Erfassungs-Session (aus der OBS-ID). Max. Verweildauer ≈ B Sessions.
- **Wiedervorlage-Lane:** fällige geparkte Items (s. „Drei Ausgänge"), garantiert und außerhalb des Rate-Budgets.

**Same-Artefakt-Kolokation:** Berührt ein anderes offenes OBS dieselbe Datei (Skript/Hook *oder* Skill/Doc), Mitnahme erwägen – spart Kontext-Laden, vermeidet Konflikt-Fixes über Sessions, bündelt teure Doc-QA.

**Drei Ausgänge je Item:** umsetzen / **verwerfen** (mit Grund → Archiv) / **aufschieben** → `IN BEOBACHTUNG bis S<NNN>` (mit Grund + **Pflicht-Wiedervorlage**: ab dieser Session kommt das Item automatisch zurück in den Drain). Geparkte Items fallen bis dahin aus dem Pool; zum Termin injiziert `obs-drain.py` sie als fällige Wiedervorlage. Fehlt das `bis S<NNN>`, gilt das Item **sofort** als fällig (+ Warnung) – so kann ein geparktes Item nie still liegenbleiben. Für event-basierte Reaktivierung („wieder aktiv wenn X") zusätzlich eine Re-Trigger-Notiz; der Termin bleibt der verlässliche Backstop.

**Bias-Auslöschung (Relevanz wird zweimal beurteilt):** heiß bei der Erfassung (Bias *für* Aufnahme), kalt bei der Behandlung (Bias *zur* Abwertung) – entgegengesetzt, daher kalibrierter zusammen. Damit die kalte Abwertung nichts Wertvolles killt, wendet der Drain (Skill `draining-observations`, Schritt 5) den **Kalt-Abwertungs-Prüfsatz** an.

**Durchführung:** Skill `draining-observations` (guardrailed Discovery + Entscheidung).

**Aufgelöste Einträge** (Status `UMGESETZT` oder `VERWORFEN`) → nach `docs/kaizen/archive/observations_archive.md` verschieben, damit die Live-`observations.md` scannbar bleibt. Das übernimmt **mechanisch** `python3 .claude/scripts/obs-archive.py` (kein Hand-Cut/Paste); solange es aussteht, listet der Drain-Satz sie als **Hygiene-Reminder**.

### Rolle in der Retro

Die Retro behandelt OBS nicht (das macht der Drain), berührt sie aber an einer Stelle:
- **Verlinkte OBS als LL-Input:** Beim Root-Causing eines LLs die per `Bezug: LL-…` daran hängenden OBS als **Design-Input** mitdenken (Zwei-Brillen-Quer-Bewegung). Die Suche ist **ID-gezielt** (`Bezug: LL-<diese-ID>`), daher auch im Archiv (`docs/kaizen/archive/observations_archive.md`) eindeutig – kein Relevanz-Scan über alle Einträge, nur die Treffer auf genau dieses LL.

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
| **HOCH** | Verzögert die Arbeit spürbar oder gefährdet Qualität | In derselben Session: Eintrag in `lessons_learned.md` + `countermeasures.md` | Poka-yoke anstreben wenn verhältnismäßig; sonst expliziter Schritt in Guideline oder Skill |
| **MITTEL** | Kleine Prozessabweichung, schnell bemerkt | Eintrag in `lessons_learned.md` | Poka-yoke anstreben wenn einfach umsetzbar; sonst Eintrag in `principles.md` wenn wiederholt |
| **GERING** | Stilistisch oder präferenzbedingt | Eintrag in `lessons_learned.md` | Keine Maßnahme nötig |

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

**Regel 1 – Sichtbarkeit:** Jede neue OFFEN-Maßnahme wird in derselben Retro-Session unter „Nächste Prioritäten" in `docs/AGENT_MEMORY.md` eingetragen. Falls inhaltlich zutreffend auch als technische Schuld (`docs/tech-debt.md`) oder offene Frage (`docs/open-questions.md`). Ablauf: Schritt 4 des `kaizen`-Skills.

**Regel 2 – Eskalation:** Eine Maßnahme die nach 2 Retros noch OFFEN ist, wird in der nächsten Retro (Schritt 3, Abschnitt F) als ESKALIERT präsentiert. Der User entscheidet dann: Umsetzung priorisieren oder bewusst verwerfen (Begründung in der Maßnahme notieren).

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
