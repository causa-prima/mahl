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
TaskCreate: "6. AGENT_MEMORY.md aktualisieren"
```

1. Session intern reflektieren
→ TaskUpdate "1. Intern reflektieren": in_progress – **kein Output an User, kein Warten**:
   - Was lief gut?
   - Was war schwierig / hat nicht funktioniert – und warum?
   - Learnings für die nächste Session
   - Diese Punkte werden in Schritt 4 direkt in lessons_learned.md dokumentiert.

   Falls dies ein Phasen-Abschluss ist (z.B. SKELETON → MVP):
   - Alle bisherigen Lessons Learned durchsehen: Wiederkehrende Muster? Veraltete Einträge?
   - Großes Code-Review über das gesamte Phase-Delta starten (alle Review-Agenten)

2. Dokumentations-Änderungsbedarf prüfen – **einziger Schritt mit User-Interaktion**:
→ TaskUpdate "1. Intern reflektieren": completed | TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": in_progress
   Prüfen: Muss irgendein Dokument angepasst werden? (AGENT_MEMORY, GLOSSARY, CODING_GUIDELINEs, etc.)
   - Falls ja: Vorschläge konkret formulieren und dem User **JETZT** präsentieren mit der Frage,
     ob die Änderungen direkt umgesetzt werden sollen. **Warten auf User-Antwort.**
   - Falls nein: direkt mit Schritt 4 weitermachen.

3. Dokumentations-Änderungen umsetzen (falls User zugestimmt hat):
→ TaskUpdate "2. Dokumentations-Änderungsbedarf prüfen": completed
   - Erst jetzt die identifizierten Dokumente anpassen.
   - Danach weiter mit Schritt 4.

4. `docs/history/sessions/session_NNN.md` – neue Session-Datei anlegen
→ TaskUpdate "3. Session-Datei anlegen": in_progress
   Inhalt: Implementiertes, Probleme, Ergebnisse, offene Punkte
   **Die Session-Datei wird NACH den Doku-Änderungen erstellt**, damit sie den finalen Zustand widerspiegelt.

5. `docs/history/lessons_learned.md` – Session-Eintrag schreiben:
→ TaskUpdate "3. Session-Datei anlegen": completed | TaskUpdate "4. lessons_learned.md aktualisieren": in_progress
   - Was lief gut / schwierig / Learnings (aus Schritt 1)
   - Dokumentations-Änderungen: welche wurden umgesetzt (oder "keine")

6. `docs/history/sessions/INDEX.md` – neue Zeile ergänzen (1-Satz-Zusammenfassung)
→ TaskUpdate "4. lessons_learned.md aktualisieren": completed | TaskUpdate "5. INDEX.md aktualisieren": in_progress

7. `docs/AGENT_MEMORY.md` – vollständig aktualisieren:
→ TaskUpdate "5. INDEX.md aktualisieren": completed | TaskUpdate "6. AGENT_MEMORY.md aktualisieren": in_progress
   - Status-Tabelle
   - Nächste Prioritäten
   - Technische Schuld
   - Offene Fragen
   - "Letzter Stand"-Absatz neu schreiben
