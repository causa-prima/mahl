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
TaskCreate: "5. INDEX.md aktualisieren"
TaskCreate: "6. Jenga-Score berechnen"
TaskCreate: "7. AGENT_MEMORY.md aktualisieren"
```

1. Session intern reflektieren
→ TaskUpdate "1. Intern reflektieren": in_progress – **kein Output an User, kein Warten**:
   - Was war schwierig / hat nicht funktioniert – und warum?
   - Gab es KRITISCH-Findings? (Wurden bereits per Andon-Cord behandelt – hier nur festhalten)
   - Welche Erkenntnisse gehören in `principles.md` oder `countermeasures.md`?
   Diese Punkte werden in Schritt 4 dokumentiert.

2. Dokumentations-Änderungsbedarf prüfen – **einziger Schritt mit User-Interaktion**:
→ TaskUpdate "1. Intern reflektieren": completed | TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": in_progress
   Prüfen: Muss irgendein Dokument angepasst werden? (AGENT_MEMORY, GLOSSARY, CODING_GUIDELINEs, etc.)
   - Falls in dieser Session eine neue Guideline eingeführt oder wesentlich erweitert wurde: prüfen
     welche Skills sie referenzieren sollen, und ob bestehende Feature-Files einen Retrofit-Workshop brauchen.
   - Falls ja: Vorschläge konkret formulieren und dem User **JETZT** präsentieren. **Warten auf Antwort.**
   - Falls nein: direkt mit Schritt 4 weitermachen.

3. Dokumentations-Änderungen umsetzen (falls User zugestimmt hat):
→ TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": completed
   - Dokumente anpassen, dann weiter mit Schritt 4.

4. `docs/history/sessions/session_NNN.md` – neue Session-Datei anlegen
→ TaskUpdate "3. Session-Datei anlegen": in_progress
   Inhalt: Implementiertes, Probleme, Ergebnisse, offene Punkte
   Wird NACH Doku-Änderungen erstellt (damit finaler Zustand widergespiegelt wird).

5. `docs/kaizen/lessons_learned.md` – Einträge schreiben:
→ TaskUpdate "3. Session-Datei anlegen": completed | TaskUpdate "4. lessons_learned.md aktualisieren": in_progress

   Format und Schwere/Kategorie-Definitionen: `docs/kaizen/PROCESS.md`

   **Andon-Cord:** KRITISCH-Findings wurden bereits behandelt – trotzdem dokumentieren.

   **Nach dem Schreiben prüfen:**
   - Gehört ein Eintrag in `docs/kaizen/principles.md`?
   - Gehört ein KRITISCH/HOCH-Eintrag in `docs/kaizen/countermeasures.md`?

   "Keine Learnings" nur mit expliziter Begründung akzeptabel.

6. `docs/history/sessions/INDEX.md` – neue Zeile ergänzen (1-Satz-Zusammenfassung)
→ TaskUpdate "4. lessons_learned.md aktualisieren": completed | TaskUpdate "5. INDEX.md aktualisieren": in_progress

7. Jenga-Score berechnen:
→ TaskUpdate "5. INDEX.md aktualisieren": completed | TaskUpdate "6. Jenga-Score berechnen": in_progress
   - Script ausführen: `python3 .claude/scripts/jenga_score.py`
   - Jenga-Score intern festhalten für Schritt 8.

8. `docs/AGENT_MEMORY.md` – vollständig aktualisieren:
→ TaskUpdate "6. Jenga-Score berechnen": completed | TaskUpdate "7. AGENT_MEMORY.md aktualisieren": in_progress
   - Phase-Zeile, Nächste Prioritäten, Technische Schuld, Offene Fragen
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
