---
name: kaizen
description: >
  Wird ausgelöst wenn der Jenga-Score ≤ 0 ist (Trigger-Text in AGENT_MEMORY.md unter "Nächste
  Prioritäten": "Retro fällig (Jenga-Score ≤ 0)") oder wenn der User "Retro", "Kaizen",
  "Rückschau" oder "Retrospektive" anfordert. Analysiert lessons_learned.md, deckt Muster auf,
  bewertet und aktualisiert Countermeasures, archiviert lessons_learned.md.
user-invocable: true
---

# Kaizen-Retro

Definitionen für Schwere, Kategorien, Kontext-Tags, BEWÄHRT- und Obsolet-Kriterien: `docs/kaizen/PROCESS.md`

→ Task-System: `docs/TASK_SYSTEM.md`

Lege zu Beginn folgende Task-Liste an:

→ TaskCreate "0. Noise-Review: lessons_learned + Archiv bereinigen"
→ TaskCreate "1. retro_report.py ausführen"
→ TaskCreate "2. countermeasures.md reviewen"
→ TaskCreate "3. Findings präsentieren & Freigabe"
→ TaskCreate "4. Änderungen umsetzen"
→ TaskCreate "5. lessons_learned.md archivieren"
→ TaskCreate "6. AGENT_MEMORY.md aufräumen"

---

## 0. Noise-Review: lessons_learned + Archiv bereinigen

→ TaskUpdate "0. Noise-Review: lessons_learned + Archiv bereinigen": in_progress

Lies `docs/kaizen/lessons_learned.md` und alle `*.md`-Dateien in `docs/kaizen/archive/`. Wende auf jeden Eintrag den Filter-Test aus `docs/kaizen/PROCESS.md` an:

**Test:** „Könnte ein Agent diesen Fehler wieder machen – auch wenn die Konfigurationsänderung schon vorhanden ist?"

Noise-Kandidaten sind Einträge die:
- Ein Infrastruktur- oder Setup-Problem beschreiben das durch eine Konfigurationsänderung dauerhaft behoben ist
- Reine Fakten über Tool-Verhalten dokumentieren ohne Konsequenz für künftiges Agenten-Verhalten

Präsentiere Kandidaten als Tabelle:

```
| Datei | Session | Eintrag (Kurztitel) | Begründung |
|-------|---------|---------------------|------------|
```

**Warte auf User-Freigabe** bevor gelöscht wird. Nur freigegebene Einträge entfernen.

Falls keine Kandidaten gefunden: kurz melden ("Kein Noise gefunden – Preprocessing-CM wirkt.") und direkt mit Schritt 1 weitermachen.

→ TaskUpdate "0. Noise-Review: lessons_learned + Archiv bereinigen": completed | TaskUpdate "1. retro_report.py ausführen": in_progress

---

## 1. retro_report.py ausführen

→ TaskUpdate "1. retro_report.py ausführen": in_progress

```bash
python3 .claude/scripts/retro_report.py
```

Standardpfade: `docs/kaizen/lessons_learned.md`, `docs/kaizen/archive/`, `docs/kaizen/countermeasures.md`. Für abweichende Pfade: `--current`, `--archive`, `--cm` als Named-Arguments übergeben.

Falls `docs/kaizen/archive/` leer ist:
- Wenn `docs/kaizen/countermeasures.md` AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass das Archiv tatsächlich leer ist (Archiv-Dateien könnten verschoben oder versehentlich gelöscht worden sein). Erst nach Bestätigung mit Schritt 2 weitermachen.
- Wenn `countermeasures.md` ebenfalls keine AKTIV/OFFEN-Einträge enthält: User bestätigen lassen dass dies tatsächlich die erste Retro ist (auch CMs könnten versehentlich fehlen). Nach Bestätigung: Erster Lauf – kein historischer Vergleich möglich, Script liefert nur aktuelle Statistik. In Schritt 3 darauf hinweisen.

Das Script gibt einen beschrifteten Abschnitt "Pattern-Kandidaten" aus – diese sind bereits gefiltert (≥2× im Fenster (= Sessions seit der letzten Retro, ab "Neue Sessions ab: NNN"), nicht durch eine bestehende Countermeasure (egal ob OFFEN, AKTIV, IN UMSETZUNG oder BEWÄHRT) abgedeckt). Der Anker "Neue Sessions ab: NNN" (ebenfalls im Script-Output) gibt die erste Session an, die seit der letzten Retro hinzugekommen ist. Leite aus diesen Pattern-Kandidaten konkrete Maßnahmenvorschläge ab. Diese Vorschläge sind der Input für Abschnitt A in Schritt 3.

Ergebnis intern festhalten für Schritt 3.

---

## 2. countermeasures.md reviewen

→ TaskUpdate "1. retro_report.py ausführen": completed | TaskUpdate "2. countermeasures.md reviewen": in_progress

Lies `docs/kaizen/countermeasures.md`. Für jeden AKTIV/OFFEN-Eintrag:

**Anwendbarkeit prüfen:** Lies zunächst `docs/history/sessions/INDEX.md` und identifiziere anhand der Kurzfassungen welche Sessions ab "Neue Sessions ab: NNN" (laut Script-Output) die relevante Arbeit enthielten. Lies dann die vollständigen Session-Dateien dieser gefilterten Sessions um zu beurteilen ob das Problem aufgetreten ist (Nachweis für BEWÄHRT / Rückfall). Falls eine Session-Datei fehlt: Fehler melden – nicht als "nicht beobachtbar" werten (fehlende Datei = Datenverlust oder Prozessbruch, keine valide Aussage möglich).

Faustregel je Kontext-Tag (für Filterung via INDEX.md):
- `TDD` / `C#-Code` / `TS-Code`: beobachtbar wenn neuer Produktions- oder Testcode geschrieben wurde
- `Agent-Prompt` / `Review`: beobachtbar wenn ein Sub-Agent beauftragt wurde
- `Skill-Nutzung`: beobachtbar wenn ein Skill aufgerufen wurde
- `Session-Struktur`: beobachtbar wenn eine Session mit Planung/Abschluss stattfand
- Sonstige: Zweifel → Session-Datei trotzdem lesen

Falls keine Session die relevante Arbeit enthielt: Maßnahme hat keine neue Evidenz gesammelt – Status unverändert.

**BEWÄHRT?** Kriterium: Die relevante Situation ist nach Einführung mind. 3× aufgetreten ohne Rückfall.

**Überarbeiten?** Gibt es Rückfälle in der aktuellen `lessons_learned.md`? Falls ja:
Maßnahme war unzureichend – verschärfen (bei KRITISCH: Poka-yoke Pflicht, bei anderen: Poka-yoke
anstreben wenn verhältnismäßig).
Bei einem Rückfall auf eine KRITISCH-Maßnahme: In Schritt 3 als **KRITISCH-Rückfall** explizit markieren und Poka-yoke-Pflicht in der Empfehlung hervorheben.

**BEWÄHRT-Einträge auf Regressionen prüfen:** Gibt es ein neues Finding in `lessons_learned.md`,
das inhaltlich zu einem BEWÄHRT-Eintrag passt? Falls ja → zurück auf AKTIV.

**Obsolet?** Ein Eintrag ist obsolet wenn das betroffene Tool/Prozess nicht mehr existiert,
das Problem strukturell unmöglich geworden ist, oder es eine einmalige Situation war.

Ergebnis intern festhalten für Schritt 3.

---

## 3. Findings präsentieren & Freigabe einholen

→ TaskUpdate "2. countermeasures.md reviewen": completed | TaskUpdate "3. Findings präsentieren & Freigabe": in_progress

Präsentiere dem User folgende strukturierte Übersicht und **warte auf Freigabe** bevor Änderungen umgesetzt werden. Freigabe kann teilweise erteilt oder abgelehnt werden – nur explizit freigegebene Punkte umsetzen:

```
## A) Neue/aktualisierte Maßnahmen (aus Schritt 1)
| Problem | Wohin | Vorschlag |
|---------|-------|-----------|
| ...     | countermeasures.md / principles.md / Guideline | ... |

## B) Neue Prinzipien (aus Schritt 1)
(Nur wenn querschnittlich – sonst besser in Guideline/Skill)
- ...

## C) Status-Änderungen bestehender Maßnahmen (aus Schritt 2)
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
```

Abschnitte die leer sind weglassen.

---

## 4. Änderungen umsetzen

→ TaskUpdate "3. Findings präsentieren & Freigabe": completed | TaskUpdate "4. Änderungen umsetzen": in_progress

Nur freigegebene Änderungen, in dieser Reihenfolge (Abhängigkeiten beachten: countermeasures.md verweist auf Ziele die bereits existieren müssen):
1. `docs/kaizen/principles.md` aktualisieren
2. Guidelines / Skills anpassen – Entscheidungshilfe: `docs/kaizen/PROCESS.md`, Abschnitt "Wann gehört etwas wohin?"
   Bei echter Überschneidung: mit User absprechen
3. `docs/kaizen/countermeasures.md` aktualisieren (Verweise auf principles.md oder Guideline-Änderungen aus Schritt 1+2 ergänzen)
4. `docs/kaizen/PROCESS.md` aktualisieren falls neue Kontext-Tags vereinbart
5. `docs/AGENT_MEMORY.md` unter „Nächste Prioritäten": Für jeden neuen OFFEN-Eintrag einen Punkt ergänzen (Kurzbeschreibung, Verweis auf countermeasures.md). Falls zutreffend auch als Technische Schuld oder Offene Frage eintragen.

---

## 5. lessons_learned.md archivieren

→ TaskUpdate "4. Änderungen umsetzen": completed | TaskUpdate "5. lessons_learned.md archivieren": in_progress

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

## 6. AGENT_MEMORY.md aufräumen

→ TaskUpdate "5. lessons_learned.md archivieren": completed | TaskUpdate "6. AGENT_MEMORY.md aufräumen": in_progress

Falls in `docs/AGENT_MEMORY.md` unter "Nächste Prioritäten" ein Eintrag steht der den Text `"Retro fällig (Jenga-Score ≤ 0)"` enthält → diesen Eintrag entfernen.

→ TaskUpdate "6. AGENT_MEMORY.md aufräumen": completed
