---
name: kaizen
description: >
  Wird ausgelöst wenn der Jenga-Score ≤ 0 ist (der Trigger "Retro fällig (Jenga-Score ≤ 0)"
  wird am Session-Start automatisch injiziert) oder wenn der User "Retro", "Kaizen",
  "Rückschau" oder "Retrospektive" anfordert. Analysiert lessons_learned.md, deckt Muster auf,
  bewertet und aktualisiert Countermeasures, archiviert lessons_learned.md.
user-invocable: true
---

# Kaizen-Retro

Definitionen für [Impact](../../../docs/kaizen/process.md#KPR-impact-kategorien), [Kategorien](../../../docs/kaizen/process.md#KPR-bereichs-kategorien), [Kontext-Tags](../../../docs/kaizen/process.md#KPR-kontext-tags), [BEWÄHRT](../../../docs/kaizen/process.md#KPR-bewaehrt)- und [Obsolet-Kriterien](../../../docs/kaizen/process.md#KPR-obsolet)

**Ablauf** – in dieser Reihenfolge abarbeiten:

1. [Noise-Review](#KZN-noise-review) – lessons_learned + Archiv bereinigen
2. [User-/Meta-Beobachtungen abfragen](#KZN-user-beobachtungen)
3. [Retro-Report](#KZN-retro-report) – `retro_report.py` ausführen
4. [CM-Review](#KZN-countermeasures-review) – countermeasures.md reviewen
5. [OBS-Retro-Berührung](#KZN-obs-beruehrung)
6. [Findings präsentieren](#KZN-findings-praesentieren) – **einziger Schritt mit Freigabe-Wartepunkt**
7. [Änderungen umsetzen](#KZN-aenderungen-umsetzen)
8. [Archivieren](#KZN-archivieren) – lessons_learned.md
9. [Session-Abschluss anbieten](#KZN-session-abschluss)

---

<a id="KZN-noise-review"></a>
## Noise-Review: lessons_learned + Archiv bereinigen

Lies `docs/kaizen/lessons_learned.md` und die **zuletzt archivierte Periode** (die jüngste `*.md`-Datei in `docs/kaizen/archive/`). Wende auf jeden Eintrag den [Filter-Test](../../../docs/kaizen/process.md#KPR-was-gehoert-rein) an:

**Test (alle Fragen müssen mit Ja beantwortet werden, damit der Eintrag bleibt):**
1. „Könnte ein Agent diesen Fehler wieder machen – auch wenn die Konfigurationsänderung schon vorhanden ist?"
2. „Kann die auslösende Situation grundsätzlich wiederkehren – bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter?"
3. „Beschreibt die *Regel* ein Agenten-Verhalten/-Urteil, das schiefgehen kann – oder eine **statische Tatsache**, die man einmal nachschlägt?" (statische Tatsache → Noise, gehört in Doku/Code-Kommentar). Begründung dieser Frage: [„Was gehört in lessons_learned?"](../../../docs/kaizen/process.md#KPR-was-gehoert-rein).

Noise-Kandidaten sind Einträge die:
- Ein Infrastruktur- oder Setup-Problem beschreiben das durch eine Konfigurationsänderung dauerhaft behoben ist
- Reine Fakten über Tool-Verhalten dokumentieren ohne Konsequenz für künftiges Agenten-Verhalten
- Eine **einmalige Situation** beschreiben, die grundsätzlich nicht wiederkehren kann und unter der **keine wiederkehrende Tätigkeits-Klasse** liegt (liegt eine Klasse darunter → kein Noise, der Eintrag bleibt)

Präsentiere Kandidaten als Tabelle:

```
| Datei | Session | Eintrag (Kurztitel) | Begründung |
|-------|---------|---------------------|------------|
```

**Warte auf User-Freigabe** bevor gelöscht wird. Nur freigegebene Einträge entfernen.

Falls keine Kandidaten gefunden: kurz melden ("Kein Noise gefunden – Preprocessing-CM wirkt.") und direkt mit [User-/Meta-Beobachtungen abfragen](#KZN-user-beobachtungen) weitermachen.

**Impact-Sanity-Check (gleicher Durchgang, nur aktuelle Periode):** Prüfe zusätzlich jeden Eintrag der **aktuellen** Periode gegen die `process.md`-Impact-Definition – Jenga-Score und Pattern-Cluster ([Retro-Report](#KZN-retro-report)) sind impact-gewichtet, ein Fehl-Rating verzerrt sie. Achte gezielt auf die drei häufigen Fehler (s. `process.md`, „Impact richtig bemessen"): **Neuheit ≠ Impact** („schon durch ein Prinzip abgedeckt" ist kein GERING-Grund), **Klasse ≠ Einzelfall** (bemessen wird die Problem-Klasse falls unbemerkt, nicht der zufällig abgefangene Fall), **„schnell bemerkt" ist kein Kriterium**. Präsentiere grobe Fehl-Ratings (v.a. GERING/HOCH-Grenzfälle) als Tabelle (Eintrag | Ist | Vorschlag | Grund) und korrigiere **nur nach User-Freigabe**, **vor** [Retro-Report](#KZN-retro-report). Bei mehreren unsicheren Grenzfällen optional auf einen **blinden Multi-Rater-Durchgang** eskalieren: mehrere Subagenten raten ein tag-entferntes Sample unabhängig neu; hohe Inter-Rater-Übereinstimmung + systematische Abweichung vom Ist = echtes Fehl-Rating (nicht bloß subjektive Streuung).

---

<a id="KZN-user-beobachtungen"></a>
## User-/Meta-Beobachtungen abfragen

Den User aktiv nach **zeitraum-/prozessweiten** Beobachtungen fragen, die **nicht an eine einzelne Session** hängen – also genau die Ebene, die der session-lokale `closing-session`-Prompt nicht erreicht:

> „Ist dir über die letzten Sessions hinweg etwas am Prozess/System aufgefallen, das besser sein könnte – eine wiederkehrende Reibung, ein Tooling-Wunsch, eine strukturelle Idee?"

Jeden Punkt per **Erfassungs-Test** ([„Zwei Brillen"](../../../docs/kaizen/process.md#KPR-zwei-brillen)) einsortieren – **Erfassung jetzt, Bewertung nicht hier**: OBS werden im Drain (`draining-observations`) behandelt, LL ab [Retro-Report](#KZN-retro-report) in der Muster-Analyse.
- **Vorausschauende Optimierung/Reibung** → **OBS** in `docs/kaizen/observations.md` (`Status: NEU`, `Quelle: User`).
- **Konkretes Problem aus der abzuschließenden Periode** → LL-Eintrag (mit ID + Erfassungs-Test) in die **aktuelle** `docs/kaizen/lessons_learned.md`, **jetzt** (vor [Retro-Report](#KZN-retro-report)) – dann nimmt `retro_report.py` es in die Muster-Analyse auf und es wird mit der Periode archiviert.
- **Problem, das während der Retro selbst passiert** → gehört zu dieser Session → beim `closing-session` dieser Session loggen, nicht hier.

Der Noise-Filter (die [Erfassungs-Fragen](../../../docs/kaizen/process.md#KPR-was-gehoert-rein)) gilt für ALLE Einträge. Keine Lösung jetzt umsetzen.

**Dieselbe Routing-Regel gilt für alles, was in den Analyse-Schritten ([Retro-Report](#KZN-retro-report), [CM-Review](#KZN-countermeasures-review), [OBS-Berührung](#KZN-obs-beruehrung)) *festgestellt* wird** (nicht nur für hier Abgefragtes) – einsortieren nach demselben Erfassungs-Test.

---

<a id="KZN-retro-report"></a>
## retro_report.py ausführen

```bash
python3 -m prozesscode.retro_report
```

Standardpfade: `docs/kaizen/lessons_learned.md`, `docs/kaizen/archive/`, `docs/kaizen/countermeasures.md`. Für abweichende Pfade: `--current`, `--archive`, `--cm` als Named-Arguments übergeben.

Falls `docs/kaizen/archive/` leer ist:
- Wenn `docs/kaizen/countermeasures.md` AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass das Archiv tatsächlich leer ist (Archiv-Dateien könnten verschoben oder versehentlich gelöscht worden sein). Erst nach Bestätigung mit dem [CM-Review](#KZN-countermeasures-review) weitermachen.
- Wenn `countermeasures.md` ebenfalls keine AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass dies tatsächlich die erste Retro ist (auch CMs könnten versehentlich fehlen). Nach Bestätigung: Erster Lauf – kein historischer Vergleich möglich, Script liefert nur aktuelle Statistik. In [Findings präsentieren](#KZN-findings-praesentieren) darauf hinweisen.

Das Script gibt einen beschrifteten Abschnitt "Pattern-Kandidaten" aus – Tag-Tripel (Impact/Kategorie/Kontext), die ≥2× im **Pattern-Fenster** auftreten und nicht durch eine bestehende Countermeasure (OFFEN/AKTIV/IN UMSETZUNG/BEWÄHRT) abgedeckt sind. Das **Pattern-Fenster** = aktuelle Periode + die letzten 3 Archiv-Perioden. Perioden sind die Spannen zwischen Retros, durch den Jenga-Score begrenzt – also **unterschiedlich lang** (die „Sessions gesamt"-Zahl im Header ist nur der aktuelle Wert, keine feste Fenstergröße).

**Drei Dinge beim Lesen der Kandidaten:**
- **Grobe Erstfilterung:** Das Tripel ist nur ein grober Proxy für „dasselbe Problem", und der CM-Abgleich ist impact-exakt. Jeden NEU-Kandidaten **manuell gegen `countermeasures.md` UND `principles.md`** gegenprüfen – ein anders getaggtes oder höher eingestuftes CM kann denselben Sachverhalt meinen (Prinzipien sind als CM-Schatten getrackt – [„principles.md ⇄ countermeasures.md"](../../../docs/kaizen/process.md#KPR-wohin)).
- **Priorisierung:** Der Anker „Neue Sessions ab: NNN" markiert die erste Session der aktuellen Periode. Muster mit mindestens einem Mitglied aus der aktuellen Periode priorisieren – reine Alt-Archiv-Muster lagen bereits früheren Retros vor.
- **Einzel-Einträge lesen:** Cluster sind Tag-Kombinationen, keine semantischen Gruppen – vor jedem Vorschlag die konkreten Einträge prüfen.

Leite aus den verbleibenden Kandidaten konkrete Maßnahmenvorschläge ab (CM-Eingangs-Gate beachten, s.u.). Diese Vorschläge sind der Input für Abschnitt A in [Findings präsentieren](#KZN-findings-praesentieren).

**CM-Eingangs-Gate:** Bevor ein Pattern-Kandidat zu einem Maßnahmenvorschlag wird, das CM-Eingangs-Gate aus [„Wann gehört etwas wohin?"](../../../docs/kaizen/process.md#KPR-wohin) anwenden: liegt eine wiederkehrende Tätigkeits-Klasse darunter, oder war es eine einmalige Umstellung? Einmal-Situation ohne verallgemeinerbare Klasse → keine CM. Klasse vorhanden → Vorschlag auf Klassen-Ebene formulieren.

Ergebnis intern festhalten für [Findings präsentieren](#KZN-findings-praesentieren).

---

<a id="KZN-guard-stats"></a>
## Guard-Auslösungen sichten

```bash
python3 -m prozesscode.guard-stats
```

**Warum in der Retro.** Der Ausfall eines Guards löst per Definition nichts aus – die Frage
„hat er je gefeuert?" ist der einzige Zugang dazu ([Begründung](../../../docs/guidelines/coding-guideline-python.md#CGP-guard-protokoll)).
Sie gehört hierher, weil die Retro der Ort der **Bestandssichtung** ist und der Abstand
zwischen zwei Retros genug Auslösungen sammelt.

**Wie der Befund zu lesen ist – drei Fälle, drei verschiedene Schlüsse:**

- **Nie gefeuert, aber der Report meldet dünne Datenlage** → kein Befund. Die Zahl sagt dann
  etwas über das Alter des Protokolls, nicht über den Guard.
- **Nie gefeuert bei ausreichender Datenlage** → der Guard ist *entweder* kaputt *oder*
  überflüssig, und von außen sind beide nicht zu unterscheiden. Also prüfen, nicht annehmen:
  ihn einmal absichtlich brechen und sehen, ob er anspringt (die Gegenprobe aus
  [`principles.md`](../../../docs/kaizen/principles.md#KPI-kommunikation)). Springt er an, ist
  er überflüssig geworden – das ist eine OBS, keine stille Löschung.
- **Im Protokoll, aber nicht mehr definiert** → ein umbenannter oder entfernter Guard.
  Aufräumen, damit die Zählung zuordenbar bleibt.

Der Bash-Hook führt sein eigenes Protokoll (`tool-usage.py`) und ist hier **nicht** enthalten.

Ergebnis intern festhalten für [Findings präsentieren](#KZN-findings-praesentieren).

---

<a id="KZN-coverage"></a>
## Testabdeckung des Prozess-Codes sichten

```bash
python3 -m prozesscode.coverage-run
```

**Metrik, kein Gate** ([Begründung](../../../docs/guidelines/coding-guideline-python.md#CGP-was-nicht-gilt)).
Gesucht wird **kein Zielwert**, sondern die Stelle, an der offensichtlich Tests fehlen.

**Beim Lesen zwei Gruppen trennen**, sonst wirkt die Zahl dramatischer als sie ist:

- **Dünne CLI-Fassade über getestetem Kern** – `obs.py`, `td.py`, `tracker.py` und die
  Wrapper-Scripts stehen bei 0 %, ihre Kernmodule (`obs_entry`, `td_entry`, `tracker_entry`)
  aber bei 86–99 %. Kein Befund.
- **Logik und Guards mit Lücken** – das ist der Befund. In S128 etwa `qa-check.py` (36 %),
  `check-anchors.py` (40 %), `check-code-quality-nonblocking.py` (32 %).

Ein Guard mit Lücken gehört zusammen mit [Guard-Auslösungen](#KZN-guard-stats) gelesen: Wenig
Abdeckung *und* keine Auslösung ist ein deutlich stärkeres Signal als jedes für sich.

Ergebnis intern festhalten für [Findings präsentieren](#KZN-findings-praesentieren).

---

<a id="KZN-countermeasures-review"></a>
## countermeasures.md reviewen

**Zuerst die CM-Bezüge der Periode einlösen** – diese Retro ist der letzte Moment dafür,
danach sind die Einträge archiviert:

```bash
grep "^  CM-Bezug:" docs/kaizen/lessons_learned.md | sort | uniq -c
```

- `CM-Bezug: <CM-ID>` → **Nachtrag** an dieser Maßnahme (Instanz/Rückfall dort vermerken).
  Ohne ihn zählt `retro_report.py` den Rückfall nicht (CM-S078-2).
- `CM-Bezug: neu` → Maßnahme **anlegen** (durch das CM-Eingangs-Gate, s. [Retro-Report](#KZN-retro-report)).

Erst danach der Review der bestehenden Einträge.

Lies `docs/kaizen/countermeasures.md`. **Kein Eintrag – CM, LL oder OBS – wird dem User nur per ID
vorgelegt**: Kurztitel und ein paar erklärende Sätze gehören dazu
([`principles.md`, Kommunikation](../../../docs/kaizen/principles.md#KPI-kommunikation)).
Für jeden AKTIV/OFFEN-Eintrag:

**Anwendbarkeit prüfen:** Die Session-Historie steht in den Commit-Nachrichten. Jede abgeschlossene Session endet mit einem Commit, der den Trailer `Session-Ende: <NNN>` trägt; Zwischen-Commits stehen davor, bis zur vorigen Marke. Verschaffe dir mit `git log --format='%(trailers:key=Session-Ende,valueonly=true)%x09%s'` eine Liste aus Session-Nummer und Betreff und identifiziere daran, welche Sessions ab "Neue Sessions ab: NNN" (laut Script-Output) die relevante Arbeit enthielten. Lies dann deren vollständige Nachricht (`git log --format='%B' <commit>`, bei Bedarf `--stat` für die berührten Dateien), um zu beurteilen ob das Problem aufgetreten ist (Nachweis für BEWÄHRT / Rückfall). Falls zu einer Session gar kein Commit existiert: Fehler melden – nicht als "nicht beobachtbar" werten (fehlender Commit = Datenverlust oder Prozessbruch, keine valide Aussage möglich).

Faustregel je Kontext-Tag (für die Vorfilterung anhand der Betreffzeilen):
- `TDD` / `C#-Code` / `TS-Code`: beobachtbar wenn neuer Produktions- oder Testcode geschrieben wurde
- `Agent-Prompt` / `Review`: beobachtbar wenn ein Sub-Agent beauftragt wurde
- `Skill-Nutzung`: beobachtbar wenn ein Skill aufgerufen wurde
- `Bash/Permission` / `Mutation-Testing` / `Hook/Script`: beobachtbar wenn Befehle/Permission-Hook, Mutation-Testing oder .claude-Hooks/Scripts berührt wurden
- Sonstige: Zweifel → Commit-Nachricht trotzdem lesen

Falls keine Session die relevante Arbeit enthielt: Maßnahme hat keine neue Evidenz gesammelt – Status unverändert.

**Harte Daten statt Selbstbericht:** Adressiert die Maßnahme ein Verhalten, das ein Agent **nicht** selbst als Problem loggt (z.B. Bash-Permission-Verstöße), ist „keine neuen lessons_learned dazu" ein Trugschluss – werte die primäre Datenquelle aus (z.B. `.claude/tmp/denied-commands.log`). Fehlt sie: User fragen statt raten. Details: [BEWÄHRT-Kriterium](../../../docs/kaizen/process.md#KPR-bewaehrt).

**BEWÄHRT?** Kriterium: Die relevante Situation ist nach Einführung mind. 3× aufgetreten ohne Rückfall.

**Überarbeiten?** Gibt es Rückfälle in der aktuellen `lessons_learned.md`? Falls ja:
Maßnahme war unzureichend – verschärfen (bei KRITISCH: Poka-yoke Pflicht, bei anderen: Poka-yoke
anstreben wenn verhältnismäßig).
Bei einem Rückfall auf eine KRITISCH-Maßnahme: In [Findings präsentieren](#KZN-findings-praesentieren) als **KRITISCH-Rückfall** explizit markieren und Poka-yoke-Pflicht in der Empfehlung hervorheben.

**BEWÄHRT-Einträge auf Regressionen prüfen:** Gibt es ein neues Finding in `lessons_learned.md`,
das inhaltlich zu einem BEWÄHRT-Eintrag passt? Falls ja → zurück auf AKTIV.

**Obsolet?** Ein Eintrag ist obsolet wenn das betroffene Tool/Prozess nicht mehr existiert,
das Problem strukturell unmöglich geworden ist, oder es eine einmalige Situation war.

Ergebnis intern festhalten für [Findings präsentieren](#KZN-findings-praesentieren).

---

<a id="KZN-obs-beruehrung"></a>
## OBS-Retro-Berührung (verlinkt)

Das **Voll-Grooming passiert nicht hier**, sondern via Drain (Skill `draining-observations`); geparkte OBS holt ihre Pflicht-Wiedervorlage selbst zurück. Die Retro berührt OBS nur an einer Stelle (Mechanismus & Begründung: [„Rolle in der Retro"](../../../docs/kaizen/process.md#KPR-rolle-retro)):

- **Verlinkte OBS als LL-Input:** Beim Root-Causing eines LLs die per `Bezug: LL-<diese-ID>` verlinkten OBS als Design-Input mitdenken; umgekehrt hinter einem LL-Muster ggf. ein neues OBS anlegen (per `Bezug:` verlinkt). Vorgehen + ID-Suche (auch im Archiv): [„Rolle in der Retro"](../../../docs/kaizen/process.md#KPR-rolle-retro).

Ergebnis intern festhalten für [Findings präsentieren](#KZN-findings-praesentieren) (Backlog-Block in der Findings-Übersicht).

---

<a id="KZN-findings-praesentieren"></a>
## Findings präsentieren & Freigabe einholen

Präsentiere dem User folgende strukturierte Übersicht und **warte auf Freigabe** bevor Änderungen umgesetzt werden. Freigabe kann teilweise erteilt oder abgelehnt werden – nur explizit freigegebene Punkte umsetzen.

**Pro Finding vier Facetten explizit machen** (in Tabellen als Spalten/Unterzeilen, in Fließtext als benannte Punkte): **Problem** (was ist nicht ideal), **Warum jetzt** (wodurch ausgelöst / warum jetzt Thema), **Vorschlag** (empfohlener Kandidat), **Alternativen** (verworfene Kandidaten + warum verworfen). Ohne diese vier ist für den User nicht erkennbar, was zur Wahl steht.

```
## Neue/aktualisierte Maßnahmen (aus dem Retro-Report)
| Problem | Warum jetzt | Wohin | Vorschlag | Alternativen (verworfen) |
|---------|-------------|-------|-----------|--------------------------|
| ...     | ...         | countermeasures.md / principles.md / Guideline | ... | ... |

## Neue Prinzipien (aus dem Retro-Report)
(Nur wenn querschnittlich – sonst besser in Guideline/Skill)
- ...

## Status-Änderungen bestehender Maßnahmen (aus dem CM-Review)
| Eintrag | Aktuell | Vorgeschlagen | Begründung |
|---------|---------|---------------|------------|

## Empfehlungen für Kontext-Tags (Sonstiges-Einträge)
- ...

## Empfehlungen für Guidelines/Skills
- ...

## Eskalierte Maßnahmen (aus dem Retro-Report)
(Nur wenn der Report ESKALIERT-Einträge ausweist)
| Eintrag | OFFEN seit | Entscheidung |
|---------|-----------|--------------|
| ...     | S...      | Priorisieren oder verwerfen? |

## Beobachtungs-Backlog (aus der OBS-Retro-Berührung)
Hinter einem LL-Muster neu angelegte OBS, mit ihrem LL-Bezug. Entscheidungen, Status-Änderungen
und Archivierung fallen im Drain, nicht in der Retro – hier steht nur, was neu entstanden ist.
| OBS | Titel | LL-Bezug |
|-----|-------|----------|
| ... | ...   | ...      |
```

**Leere Abschnitte nicht still weglassen** – jeden Abschnitt (A–G) nennen und in einem Satz sagen, was er enthalten hätte und warum er leer ist (z.B. „B) Neue Prinzipien: keine – kein querschnittliches Muster in dieser Periode."). Sonst ist intransparent, ob ein Abschnitt geprüft-und-leer oder vergessen wurde.

---

<a id="KZN-aenderungen-umsetzen"></a>
## Änderungen umsetzen

Nur freigegebene Änderungen, in dieser Reihenfolge (Abhängigkeiten beachten: countermeasures.md verweist auf Ziele die bereits existieren müssen):
1. `docs/kaizen/principles.md` aktualisieren
2. Guidelines / Skills anpassen – Entscheidungshilfe: [„Wann gehört etwas wohin?"](../../../docs/kaizen/process.md#KPR-wohin)
   Bei echter Überschneidung: mit User absprechen
3. `docs/kaizen/countermeasures.md` aktualisieren (Verweise auf principles.md oder Guideline-Änderungen aus den vorangegangenen Schritten ergänzen)
4. [Kontext-Tags](../../../docs/kaizen/process.md#KPR-kontext-tags) in `docs/kaizen/process.md` aktualisieren falls neue vereinbart
5. `docs/kaizen/observations.md`: die in der [OBS-Retro-Berührung](#KZN-obs-beruehrung) hinter einem LL-Muster neu angelegten OBS schreiben (per `Bezug:` verlinkt). **Status-Änderungen und das Archivieren aufgelöster Einträge macht der Drain** (`draining-observations` → `obs-archive.py`), nicht die Retro – sie trifft keine OBS-Entscheidungen.
6. Neue OFFEN-Einträge sichtbar machen – **nach der Weiche in [„Umsetzung offener Maßnahmen"](../../../docs/kaizen/process.md#KPR-offene-massnahmen), Sichtbarkeit**, nicht pauschal nach AGENT_MEMORY: Ist die Maßnahme **definiert** (konkreter nächster Schritt + Done-Kriterium) → Punkt unter „Nächste Prioritäten" in `docs/AGENT_MEMORY.md`, als Kurzzusammenfassung mit Verweis auf `countermeasures.md`. Steht dagegen die **Antwort selbst** noch aus (mehrere ernsthafte Kandidaten) → CM bleibt OFFEN, Ausgestaltung als `observations.md`-Eintrag mit `Bezug:` in den Drain, Grund im CM-Eintrag notieren. Falls zutreffend zusätzlich als technische Schuld (`docs/tech-debt.md`) oder offene Frage (`docs/open-questions.md`) eintragen.

---

<a id="KZN-archivieren"></a>
## lessons_learned.md archivieren

1. Prüfe ob mindestens ein Session-Header (Format: `## Session NNN – YYYY-MM-DD`) in `docs/kaizen/lessons_learned.md` vorhanden ist.
   Falls nicht: Archivierung überspringen, User informieren ("Keine Sessions in lessons_learned.md – Archivierung nicht nötig.").
2. **Kleinste und größte** Session-Nummer aller Header ablesen → X und Y (`grep -n "^## Session " docs/kaizen/lessons_learned.md`). Nicht erster/letzter Header – die Einträge stehen in Erfassungs-, nicht in Session-Reihenfolge.
3. Datei verschieben (nicht kopieren):
   ```bash
   mv docs/kaizen/lessons_learned.md docs/kaizen/archive/session_<X>_to_<Y>.md
   # <X> = erste Session-Nummer, <Y> = letzte Session-Nummer aus den Headers
   ```
4. Neue `docs/kaizen/lessons_learned.md` aus Template anlegen (Vorbedingung: Template muss unter `.claude/skills/kaizen/references/lessons_learned_template.md` liegen – falls nicht: User informieren):
   ```bash
   cp .claude/skills/kaizen/references/lessons_learned_template.md docs/kaizen/lessons_learned.md
   ```

---

<a id="KZN-session-abschluss"></a>
## Session-Abschluss anbieten

Die Retro ist durch – `lessons_learned.md` ist archiviert, der Jenga-Score resettet, der Trigger erscheint am nächsten Session-Start nicht mehr (kein manuelles Entfernen nötig). Dem User die **Wahl** anbieten:

- **Session abschließen** (empfohlen): Skill `closing-session` starten – pflegt AGENT_MEMORY voll und legt die Session-Datei an.
- **Weiterarbeiten:** Retro abgeschlossen, Session-Abschluss später via `closing-session`.
- **Etwas anderes** – nach User-Wunsch.
