---
name: closing-session
description: >
  Session ordentlich abschließen: lessons_learned, Session-Datei anlegen, INDEX aktualisieren,
  AGENT_MEMORY aktualisieren. Verwende diesen Skill wenn die aktuelle Arbeits-Session
  beendet werden soll.
user-invocable: true
---

# Session abschließen

Lege zu Beginn folgende Task-Liste an:
```
TaskCreate: "1. Intern reflektieren"
TaskCreate: "2. Dokumentations-Änderungsbedarf prüfen"
TaskCreate: "3. Session-Datei anlegen"
TaskCreate: "4. lessons_learned.md aktualisieren"
TaskCreate: "5. index.md aktualisieren"
TaskCreate: "6. Jenga-Score berechnen"
TaskCreate: "7. AGENT_MEMORY.md aktualisieren"
```

1. Session intern reflektieren
→ TaskUpdate "1. Intern reflektieren": in_progress – **kein Output an User, kein Warten**:
   - Was war schwierig / hat nicht funktioniert – und warum?
   - Gab es KRITISCH-Findings? (Wurden bereits per Andon-Cord behandelt – hier nur festhalten)
   - Welche Erkenntnisse gehören in `principles.md` oder `countermeasures.md`?
   - **Verbesserungs-/Design-Beobachtung fürs Backlog (`docs/kaizen/observations.md`)?** – Agenten tragen
     proaktiv bei: eine vorausschauende Notiz, wie das System besser wäre (kein konkreter schlechter Ausgang nötig).
   Diese Punkte werden in Schritt 4 dokumentiert (Beobachtungen → `observations.md`, Format §`observations.md`).

2. Dokumentations-Änderungsbedarf prüfen + Beobachtungs-Prompt – **einziger Schritt mit User-Interaktion**:
→ TaskUpdate "1. Intern reflektieren": completed | TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": in_progress
   Prüfen: Muss irgendein Dokument angepasst werden? (AGENT_MEMORY, GLOSSARY, CODING_GUIDELINEs, etc.)
   - Falls in dieser Session eine neue Guideline eingeführt oder wesentlich erweitert wurde: prüfen
     welche Skills sie referenzieren sollen, und ob bestehende Feature-Files einen Retrofit-Workshop brauchen.

   **Leichter Beobachtungs-Prompt (immer stellen, kombiniert mit obigem):** Den User aktiv fragen:
   > „Ist dir diese Session etwas aufgefallen – ein **konkreter schlechter Ausgang** (→ `lessons_learned.md`)
   > oder eine **vorausschauende Idee/Reibung** (→ `observations.md`)? Beides möglich."

   Erfasstes in die jeweils richtige Datei schreiben – Erfassungs-Tests (`docs/kaizen/process.md`,
   Abschnitt „Zwei Brillen"): konkreter schlechter Ausgang → `lessons_learned.md` (Schritt 5); vorausschauende
   Beobachtung → `observations.md` (Format §`observations.md`, Status NEU, `Quelle: User`). Beides wahr → beide,
   per `Bezug:` verlinkt. Noise-Filter gilt für ALLE Einträge.

   - Falls Doku-Vorschläge oder Beobachtungen vorliegen: konkret formulieren und dem User **JETZT** präsentieren. **Warten auf Antwort.**
   - Falls nichts anzupassen / keine Beobachtung: direkt mit Schritt 4 weitermachen.

3. Dokumentations-Änderungen umsetzen (falls User zugestimmt hat):
→ TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": completed
   - Dokumente anpassen, dann weiter mit Schritt 4.
   - **Neue Beobachtungen** (aus dem Beobachtungs-Prompt) → `docs/kaizen/observations.md` schreiben
     (Format im Header dieser Datei, Status NEU; bei user-gemeldet `Quelle: User`). KEINE Lösung jetzt
     umsetzen, wenn sie aufgeschoben/nicht-trivial ist – die Retro evaluiert (Evaluierungs-Gate).

4. `docs/history/sessions/session_NNN.md` – neue Session-Datei anlegen
→ TaskUpdate "3. Session-Datei anlegen": in_progress
   Inhalt: Implementiertes, Probleme, Ergebnisse, offene Punkte
   Wird NACH Doku-Änderungen erstellt (damit finaler Zustand widergespiegelt wird).

5. `docs/kaizen/lessons_learned.md` – Einträge schreiben:
→ TaskUpdate "3. Session-Datei anlegen": completed | TaskUpdate "4. lessons_learned.md aktualisieren": in_progress

   Eintrag-Format + Erfassungs-Test + Beispiel: **Header von `docs/kaizen/lessons_learned.md`** (steht beim Schreiben direkt vor dir – kein separates Einlesen nötig). Schwere/Kategorie-Definitionen + Reaktionsregeln: `docs/kaizen/process.md`

   **Andon-Cord:** KRITISCH-Findings wurden bereits behandelt – trotzdem dokumentieren.

   **IDs & Quelle für neue Einträge:** Jeder neue Eintrag bekommt eine ID `LL-S<NNN>-<n>`,
   platziert **HINTER den Tags**: `- **[HOCH] [PROZESS] [TDD] LL-S<NNN>-<n> – Kurztitel**` (vor `[` würde
   sie die Script-Regexes brechen). User-gemeldete Einträge zusätzlich mit optionaler Zeile `Quelle: User`.

   **Nur konkrete schlechte Ausgänge hierher.** Vorausschauende Beobachtungen gehören nach
   `docs/kaizen/observations.md` (billiger Erfassungs-Test: „vorausschauende Notiz, wie das System besser
   wäre?" → observations; „konkreter schlechter Ausgang aufgetreten?" → hier; beides → beide, per `Bezug:`).

   **Nach dem Schreiben prüfen:**
   - Gehört ein Eintrag in `docs/kaizen/principles.md`?
   - Gehört ein KRITISCH/HOCH-Eintrag in `docs/kaizen/countermeasures.md`?

   "Keine Learnings" nur mit expliziter Begründung akzeptabel.

6. `docs/history/sessions/index.md` – neue Zeile ergänzen
→ TaskUpdate "4. lessons_learned.md aktualisieren": completed | TaskUpdate "5. index.md aktualisieren": in_progress
   Format: `| <Nr> | <Datum> | <Phase> | <Kurzfassung> |`. **Kurzfassung = ein Satz, *was* sich geändert hat – kein „warum"/Begründung** (das gehört in die Session-Datei); auf ADR-/Session-IDs verweisen statt Prosa. Soft-Ziel ~150, **harter Cap 300 Zeichen** – ein PreToolUse-Hook (`check-index-length.py`) blockiert zu lange neue Einträge automatisch. Für den vollen Report (inkl. grandfatherter Altbestände):
   ```bash
   python3 .claude/scripts/check-index-length.py
   ```

7. Jenga-Score berechnen:
→ TaskUpdate "5. index.md aktualisieren": completed | TaskUpdate "6. Jenga-Score berechnen": in_progress
   - Script ausführen: `python3 .claude/scripts/jenga_score.py`
   - Jenga-Score intern festhalten für Schritt 8.

8. Projekt-Status aktualisieren:
→ TaskUpdate "6. Jenga-Score berechnen": completed | TaskUpdate "7. AGENT_MEMORY.md aktualisieren": in_progress
   - **`docs/AGENT_MEMORY.md` schlank halten** – wird bei jedem Session-Start voll injiziert (jede Zeile kostet Token). Leitfrage: „Welche Info braucht JEDER Agent beim Start, um den Projektstatus einzuordnen?" Nur: **Phase**, **Aktuelle Story**, **Nächste Prioritäten**.
     - **Nächstes Szenario nicht von Hand pflegen:** Der Platzhalter `{{NEXT_SCENARIO}}` in der Prioritätenliste wird beim Session-Start automatisch zum nächsten unimplementierten Szenario aufgelöst (`next_scenario.py`; Mechanik: ADR-S041-7) – stehen lassen.
     - **Szenario außer der Reihe** (Priorität überschreibt die Feature-Reihenfolge, z.B. error vor sortiert): als Anstrich **über** den Platzhalter setzen, nach Umsetzung entfernen.
   - **Ausgelagert (nicht in AGENT_MEMORY, eigene Datei pflegen):** Technische Schuld → `docs/tech-debt.md`; offene Fragen/geparkte Diskussionen → `docs/open-questions.md`. Beide haben eigene Eintrag-Formate (Header der jeweiligen Datei).
   - **Bei Phasen-Abschluss (z.B. SKELETON → MVP):** Als erste Zeile unter "Nächste Prioritäten" eintragen:
     ```
     **Phasen-Review ausstehend:** Skill `review-code` über gesamtes Phase-Delta starten.
     ```
   - **Bei Jenga-Score ≤ 0:** Unter "Nächste Prioritäten" als erste Zeile eintragen (exakter Text):
     ```
     **Retro fällig (Jenga-Score ≤ 0):** Nächste Session mit Skill `kaizen` beginnen.
     ```
   - Score **nicht** in AGENT_MEMORY schreiben (außer bei ≤ 0 als Trigger-Zeile oben).
→ TaskUpdate "7. AGENT_MEMORY.md aktualisieren": completed

Score dem User mitteilen (nach TaskUpdate).
