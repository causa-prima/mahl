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

Definitionen für Impact, Kategorien, Kontext-Tags, BEWÄHRT- und Obsolet-Kriterien: `docs/kaizen/process.md`

→ Task-System: `docs/process/task-system.md`

Lege zu Beginn folgende Task-Liste an:

→ TaskCreate "0. Noise-Review: lessons_learned + Archiv bereinigen"
→ TaskCreate "1. User-/Meta-Beobachtungen abfragen"
→ TaskCreate "2. retro_report.py ausführen"
→ TaskCreate "3. countermeasures.md reviewen"
→ TaskCreate "4. OBS-Retro-Berührung (verlinkt)"
→ TaskCreate "5. Findings präsentieren & Freigabe"
→ TaskCreate "6. Änderungen umsetzen"
→ TaskCreate "7. lessons_learned.md archivieren"
→ TaskCreate "8. Session-Abschluss anbieten"

---

## 0. Noise-Review: lessons_learned + Archiv bereinigen

→ TaskUpdate "0. Noise-Review: lessons_learned + Archiv bereinigen": in_progress

Lies `docs/kaizen/lessons_learned.md` und die **zuletzt archivierte Periode** (die jüngste `*.md`-Datei in `docs/kaizen/archive/`). Wende auf jeden Eintrag den Filter-Test aus `docs/kaizen/process.md` an:

**Test (alle drei Fragen müssen mit Ja beantwortet werden, damit der Eintrag bleibt):**
1. „Könnte ein Agent diesen Fehler wieder machen – auch wenn die Konfigurationsänderung schon vorhanden ist?"
2. „Kann die auslösende Situation grundsätzlich wiederkehren – bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter?"
3. „Beschreibt die *Regel* ein Agenten-Verhalten/-Urteil, das schiefgehen kann – oder eine **statische Tatsache**, die man einmal nachschlägt?" (statische Tatsache → Noise, gehört in Doku/Code-Kommentar). Begründung dieser Frage: `docs/kaizen/process.md`.

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

Falls keine Kandidaten gefunden: kurz melden ("Kein Noise gefunden – Preprocessing-CM wirkt.") und direkt mit Schritt 1 weitermachen.

→ TaskUpdate "0. Noise-Review: lessons_learned + Archiv bereinigen": completed | TaskUpdate "1. User-/Meta-Beobachtungen abfragen": in_progress

---

## 1. User-/Meta-Beobachtungen abfragen

→ TaskUpdate "1. User-/Meta-Beobachtungen abfragen": in_progress

Den User aktiv nach **zeitraum-/prozessweiten** Beobachtungen fragen, die **nicht an eine einzelne Session** hängen – also genau die Ebene, die der session-lokale `closing-session`-Prompt nicht erreicht:

> „Ist dir über die letzten Sessions hinweg etwas am Prozess/System aufgefallen, das besser sein könnte – eine wiederkehrende Reibung, ein Tooling-Wunsch, eine strukturelle Idee?"

Jeden Punkt per **Erfassungs-Test** (`process.md`, „Zwei Brillen") einsortieren – Erfassung jetzt, Bewertung in Schritt 4:
- **Vorausschauende Optimierung/Reibung** → **OBS** in `docs/kaizen/observations.md` (`Status: NEU`, `Quelle: User`).
- **Konkretes Problem aus der abzuschließenden Periode** → LL-Eintrag (mit ID + Erfassungs-Test) in die **aktuelle** `docs/kaizen/lessons_learned.md`, **jetzt** (vor Schritt 2) – dann nimmt `retro_report.py` es in die Muster-Analyse auf und es wird mit der Periode archiviert.
- **Problem, das während der Retro selbst passiert** → gehört zu dieser Session → beim `closing-session` dieser Session loggen, nicht hier.

Der Noise-Filter (die 3 Fragen aus `process.md`) gilt für ALLE Einträge. Keine Lösung jetzt umsetzen.

**Dieselbe Routing-Regel gilt für alles, was in Schritt 2–4 *festgestellt* wird** (nicht nur für hier Abgefragtes) – einsortieren nach demselben Erfassungs-Test.

→ TaskUpdate "1. User-/Meta-Beobachtungen abfragen": completed | TaskUpdate "2. retro_report.py ausführen": in_progress

---

## 2. retro_report.py ausführen

→ TaskUpdate "2. retro_report.py ausführen": in_progress

```bash
python3 .claude/scripts/retro_report.py
```

Standardpfade: `docs/kaizen/lessons_learned.md`, `docs/kaizen/archive/`, `docs/kaizen/countermeasures.md`. Für abweichende Pfade: `--current`, `--archive`, `--cm` als Named-Arguments übergeben.

Falls `docs/kaizen/archive/` leer ist:
- Wenn `docs/kaizen/countermeasures.md` AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass das Archiv tatsächlich leer ist (Archiv-Dateien könnten verschoben oder versehentlich gelöscht worden sein). Erst nach Bestätigung mit Schritt 3 weitermachen.
- Wenn `countermeasures.md` ebenfalls keine AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass dies tatsächlich die erste Retro ist (auch CMs könnten versehentlich fehlen). Nach Bestätigung: Erster Lauf – kein historischer Vergleich möglich, Script liefert nur aktuelle Statistik. In Schritt 5 darauf hinweisen.

Das Script gibt einen beschrifteten Abschnitt "Pattern-Kandidaten" aus – Tag-Tripel (Impact/Kategorie/Kontext), die ≥2× im **Pattern-Fenster** auftreten und nicht durch eine bestehende Countermeasure (OFFEN/AKTIV/IN UMSETZUNG/BEWÄHRT) abgedeckt sind. Das **Pattern-Fenster** = aktuelle Periode + die letzten 3 Archiv-Perioden. Perioden sind die Spannen zwischen Retros, durch den Jenga-Score begrenzt – also **unterschiedlich lang** (die „Sessions gesamt"-Zahl im Header ist nur der aktuelle Wert, keine feste Fenstergröße).

**Drei Dinge beim Lesen der Kandidaten:**
- **Grobe Erstfilterung:** Das Tripel ist nur ein grober Proxy für „dasselbe Problem", und der CM-Abgleich ist impact-exakt. Jeden NEU-Kandidaten **manuell gegen `countermeasures.md` UND `principles.md`** gegenprüfen – ein anders getaggtes oder höher eingestuftes CM kann denselben Sachverhalt meinen (Prinzipien sind als CM-Schatten getrackt, s. `process.md`).
- **Priorisierung:** Der Anker „Neue Sessions ab: NNN" markiert die erste Session der aktuellen Periode. Muster mit mindestens einem Mitglied aus der aktuellen Periode priorisieren – reine Alt-Archiv-Muster lagen bereits früheren Retros vor.
- **Einzel-Einträge lesen:** Cluster sind Tag-Kombinationen, keine semantischen Gruppen – vor jedem Vorschlag die konkreten Einträge prüfen.

Leite aus den verbleibenden Kandidaten konkrete Maßnahmenvorschläge ab (CM-Eingangs-Gate beachten, s.u.). Diese Vorschläge sind der Input für Abschnitt A in Schritt 5.

**CM-Eingangs-Gate:** Bevor ein Pattern-Kandidat zu einem Maßnahmenvorschlag wird, das CM-Eingangs-Gate aus `docs/kaizen/process.md` (Abschnitt „Wann gehört etwas wohin?") anwenden: liegt eine wiederkehrende Tätigkeits-Klasse darunter, oder war es eine einmalige Umstellung? Einmal-Situation ohne verallgemeinerbare Klasse → keine CM. Klasse vorhanden → Vorschlag auf Klassen-Ebene formulieren.

Ergebnis intern festhalten für Schritt 5.

---

## 3. countermeasures.md reviewen

→ TaskUpdate "2. retro_report.py ausführen": completed | TaskUpdate "3. countermeasures.md reviewen": in_progress

Lies `docs/kaizen/countermeasures.md`. Für jeden AKTIV/OFFEN-Eintrag:

**Anwendbarkeit prüfen:** Lies zunächst `docs/history/sessions/index.md` und identifiziere anhand der Kurzfassungen welche Sessions ab "Neue Sessions ab: NNN" (laut Script-Output) die relevante Arbeit enthielten. Lies dann die vollständigen Session-Dateien dieser gefilterten Sessions um zu beurteilen ob das Problem aufgetreten ist (Nachweis für BEWÄHRT / Rückfall). Falls eine Session-Datei fehlt: Fehler melden – nicht als "nicht beobachtbar" werten (fehlende Datei = Datenverlust oder Prozessbruch, keine valide Aussage möglich).

Faustregel je Kontext-Tag (für Filterung via index.md):
- `TDD` / `C#-Code` / `TS-Code`: beobachtbar wenn neuer Produktions- oder Testcode geschrieben wurde
- `Agent-Prompt` / `Review`: beobachtbar wenn ein Sub-Agent beauftragt wurde
- `Skill-Nutzung`: beobachtbar wenn ein Skill aufgerufen wurde
- `Bash/Permission` / `Mutation-Testing` / `Hook/Script`: beobachtbar wenn Befehle/Permission-Hook, Mutation-Testing oder .claude-Hooks/Scripts berührt wurden
- Sonstige: Zweifel → Session-Datei trotzdem lesen

Falls keine Session die relevante Arbeit enthielt: Maßnahme hat keine neue Evidenz gesammelt – Status unverändert.

**Harte Daten statt Selbstbericht:** Adressiert die Maßnahme ein Verhalten, das ein Agent **nicht** selbst als Problem loggt (z.B. Bash-Permission-Verstöße), ist „keine neuen lessons_learned dazu" ein Trugschluss – werte die primäre Datenquelle aus (z.B. `.claude/tmp/denied-commands.log`). Fehlt sie: User fragen statt raten. Details: `docs/kaizen/process.md` (BEWÄHRT-Kriterium).

**BEWÄHRT?** Kriterium: Die relevante Situation ist nach Einführung mind. 3× aufgetreten ohne Rückfall.

**Überarbeiten?** Gibt es Rückfälle in der aktuellen `lessons_learned.md`? Falls ja:
Maßnahme war unzureichend – verschärfen (bei KRITISCH: Poka-yoke Pflicht, bei anderen: Poka-yoke
anstreben wenn verhältnismäßig).
Bei einem Rückfall auf eine KRITISCH-Maßnahme: In Schritt 5 als **KRITISCH-Rückfall** explizit markieren und Poka-yoke-Pflicht in der Empfehlung hervorheben.

**BEWÄHRT-Einträge auf Regressionen prüfen:** Gibt es ein neues Finding in `lessons_learned.md`,
das inhaltlich zu einem BEWÄHRT-Eintrag passt? Falls ja → zurück auf AKTIV.

**Obsolet?** Ein Eintrag ist obsolet wenn das betroffene Tool/Prozess nicht mehr existiert,
das Problem strukturell unmöglich geworden ist, oder es eine einmalige Situation war.

Ergebnis intern festhalten für Schritt 5.

---

## 4. OBS-Retro-Berührung (verlinkt)

→ TaskUpdate "3. countermeasures.md reviewen": completed | TaskUpdate "4. OBS-Retro-Berührung (verlinkt)": in_progress

Das **Voll-Grooming passiert nicht hier**, sondern via Drain (Skill `draining-observations`); geparkte OBS holt ihre Pflicht-Wiedervorlage selbst zurück. Die Retro berührt OBS nur an einer Stelle (Mechanismus & Begründung: `docs/kaizen/process.md`, Abschnitt „Rolle in der Retro"):

- **Verlinkte OBS als LL-Input:** Beim Root-Causing eines LLs die per `Bezug: LL-<diese-ID>` verlinkten OBS als Design-Input mitdenken; umgekehrt hinter einem LL-Muster ggf. ein neues OBS anlegen (per `Bezug:` verlinkt). Vorgehen + ID-Suche (auch im Archiv): s. process.md.

Ergebnis intern festhalten für Schritt 5 (Backlog-Block in der Findings-Übersicht).

→ TaskUpdate "4. OBS-Retro-Berührung (verlinkt)": completed | TaskUpdate "5. Findings präsentieren & Freigabe": in_progress

---

## 5. Findings präsentieren & Freigabe einholen

→ TaskUpdate "5. Findings präsentieren & Freigabe": in_progress

Präsentiere dem User folgende strukturierte Übersicht und **warte auf Freigabe** bevor Änderungen umgesetzt werden. Freigabe kann teilweise erteilt oder abgelehnt werden – nur explizit freigegebene Punkte umsetzen.

**Pro Finding vier Facetten explizit machen** (in Tabellen als Spalten/Unterzeilen, in Fließtext als benannte Punkte): **Problem** (was ist nicht ideal), **Warum jetzt** (wodurch ausgelöst / warum jetzt Thema), **Vorschlag** (empfohlener Kandidat), **Alternativen** (verworfene Kandidaten + warum verworfen). Ohne diese vier ist für den User nicht erkennbar, was zur Wahl steht.

```
## A) Neue/aktualisierte Maßnahmen (aus Schritt 2)
| Problem | Warum jetzt | Wohin | Vorschlag | Alternativen (verworfen) |
|---------|-------------|-------|-----------|--------------------------|
| ...     | ...         | countermeasures.md / principles.md / Guideline | ... | ... |

## B) Neue Prinzipien (aus Schritt 2)
(Nur wenn querschnittlich – sonst besser in Guideline/Skill)
- ...

## C) Status-Änderungen bestehender Maßnahmen (aus Schritt 3)
| Eintrag | Aktuell | Vorgeschlagen | Begründung |
|---------|---------|---------------|------------|

## D) Empfehlungen für Kontext-Tags (Sonstiges-Einträge)
- ...

## E) Empfehlungen für Guidelines/Skills
- ...

## F) Eskalierte Maßnahmen (aus Script-Output Abschnitt 9)
(Nur wenn Abschnitt 9 des Scripts ESKALIERT-Einträge enthält)
| Eintrag | OFFEN seit | Entscheidung |
|---------|-----------|--------------|
| ...     | S...      | Priorisieren oder verwerfen? |

## G) Beobachtungs-Backlog (aus Schritt 4)
Neue/aktualisierte OBS, getroffene Entscheidungen, Eskalationen, verschobene (aufgelöste) Einträge.
| OBS | Titel | Status (neu) | Entscheidung/Maßnahme |
|-----|-------|--------------|------------------------|
| ... | ...   | ...          | ...                    |
```

**Leere Abschnitte nicht still weglassen** – jeden Abschnitt (A–G) nennen und in einem Satz sagen, was er enthalten hätte und warum er leer ist (z.B. „B) Neue Prinzipien: keine – kein querschnittliches Muster in dieser Periode."). Sonst ist intransparent, ob ein Abschnitt geprüft-und-leer oder vergessen wurde.

---

## 6. Änderungen umsetzen

→ TaskUpdate "5. Findings präsentieren & Freigabe": completed | TaskUpdate "6. Änderungen umsetzen": in_progress

Nur freigegebene Änderungen, in dieser Reihenfolge (Abhängigkeiten beachten: countermeasures.md verweist auf Ziele die bereits existieren müssen):
1. `docs/kaizen/principles.md` aktualisieren
2. Guidelines / Skills anpassen – Entscheidungshilfe: `docs/kaizen/process.md`, Abschnitt "Wann gehört etwas wohin?"
   Bei echter Überschneidung: mit User absprechen
3. `docs/kaizen/countermeasures.md` aktualisieren (Verweise auf principles.md oder Guideline-Änderungen aus Schritt 1+2 ergänzen)
4. `docs/kaizen/process.md` aktualisieren falls neue Kontext-Tags vereinbart
5. `docs/kaizen/observations.md` + `docs/kaizen/archive/observations_archive.md`: freigegebene OBS-Status/Entscheidungen aus Schritt 4 schreiben; aufgelöste Einträge (UMGESETZT/VERWORFEN) ins Archiv verschieben.
6. `docs/AGENT_MEMORY.md` unter „Nächste Prioritäten": Für jeden neuen OFFEN-Eintrag einen Punkt ergänzen (Kurzbeschreibung, Verweis auf countermeasures.md). Falls zutreffend auch als technische Schuld (`docs/tech-debt.md`) oder offene Frage (`docs/open-questions.md`) eintragen.

---

## 7. lessons_learned.md archivieren

→ TaskUpdate "6. Änderungen umsetzen": completed | TaskUpdate "7. lessons_learned.md archivieren": in_progress

1. Prüfe ob mindestens ein Session-Header (Format: `## Session NNN – YYYY-MM-DD`) in `docs/kaizen/lessons_learned.md` vorhanden ist.
   Falls nicht: Archivierung überspringen, User informieren ("Keine Sessions in lessons_learned.md – Archivierung nicht nötig.").
2. Ersten und letzten Session-Header ablesen → X und Y bestimmen.
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

## 8. Session-Abschluss anbieten

→ TaskUpdate "7. lessons_learned.md archivieren": completed | TaskUpdate "8. Session-Abschluss anbieten": in_progress

Die Retro ist durch – `lessons_learned.md` ist archiviert, der Jenga-Score resettet, der Trigger erscheint am nächsten Session-Start nicht mehr (kein manuelles Entfernen nötig). Dem User die **Wahl** anbieten:

- **A) Session abschließen** (empfohlen): Skill `closing-session` starten – pflegt AGENT_MEMORY voll und legt die Session-Datei an.
- **B) Weiterarbeiten:** Retro abgeschlossen, Session-Abschluss später via `closing-session`.
- **C) Etwas anderes** – nach User-Wunsch.

→ TaskUpdate "8. Session-Abschluss anbieten": completed
