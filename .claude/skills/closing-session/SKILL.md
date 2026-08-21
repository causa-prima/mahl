---
name: closing-session
description: >
  Session ordentlich abschließen: lessons_learned, Session-Datei anlegen, INDEX aktualisieren,
  AGENT_MEMORY aktualisieren. Verwende diesen Skill wenn die aktuelle Arbeits-Session
  beendet werden soll.
user-invocable: true
---

# Session abschließen

1. Session intern reflektieren – **kein Output an User, kein Warten**:
   - Was war schwierig / hat nicht funktioniert – und warum?
   - Gab es KRITISCH-Findings? (Wurden bereits per Andon-Cord behandelt – hier nur festhalten)
   - Welche Erkenntnisse gehören in `principles.md` oder `countermeasures.md`?
   - **Verbesserungs-/Design-Beobachtung fürs Backlog (`docs/kaizen/observations.md`)?** – Agenten tragen
     proaktiv bei: eine vorausschauende Notiz, wie das System besser wäre (kein konkreter schlechter Ausgang nötig).
   Diese Punkte werden in Schritt 4 dokumentiert (Beobachtungen → `observations.md`, Format §`observations.md`).

2. Dokumentations-Änderungsbedarf prüfen + Beobachtungs-Prompt – **einziger Schritt mit User-Interaktion**:
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
   - **Beim Erfassen Ziel/Problem korrekt benennen** (nicht eine vermutete Lösung): die zum Verständnis nötigen Details sind *jetzt* präsent, beim späteren Drain oft nicht mehr ableitbar. Bei echter Unklarheit kurz rückfragen statt zu raten – eine falsch erfasste Beobachtung verleitet den Drain zu plausiblen, aber falschen Kandidaten.
   - **Lief unmittelbar zuvor `implementing-scenario` Schritt 6.1** (Szenario → direkter Abschluss): Die offenen Punkte wurden dort schon mit dem User surfacet + triagiert. Dann die als „vermerken" entschiedenen LL/OBS **hier** schreiben (gebündelt) und den obigen Prompt nur **ergänzend** stellen (was 6.1 nicht abdeckte) – nicht dieselbe Frage voll wiederholen.

   - Falls Doku-Vorschläge oder Beobachtungen vorliegen: konkret formulieren und dem User **JETZT** präsentieren. **Warten auf Antwort.**
   - Falls nichts anzupassen / keine Beobachtung: direkt mit Schritt 4 weitermachen.

3. Dokumentations-Änderungen umsetzen (falls User zugestimmt hat):
   - Dokumente anpassen, dann weiter mit Schritt 4.
   - **Neue Beobachtungen** (aus dem Beobachtungs-Prompt) → **per Script erfassen**, nicht per Edit:
     ```
     python3 .claude/scripts/obs.py list-offen        # erst die offenen Titel ansehen – für --zusammen-erledigen
     python3 .claude/scripts/obs.py add --titel "…" --quelle User --impact MITTEL \
         --haeufigkeit dauerhaft --kategorie PROZESS --kontext Doku --beobachtung "…" \
         --zusammen-erledigen keiner
     ```
     Das vergibt die ID, hängt den Eintrag an und setzt das Entscheidungsfeld auf den einzigen bei
     der Erfassung zulässigen Wert – ein Eintrag kann so nicht in der Form entstehen, die
     `check-obs-capture.py` blocken müsste. Nebeneffekt: Die Datei muss dafür nicht gelesen werden.
     **`--zusammen-erledigen` ist Pflicht** und verlangt eine echte Prüfung: Nennt einen offenen
     Eintrag nur, wenn er sich **in einem Zug miterledigen** ließe: Bearbeite ich den neuen,
     liegt jener dann ohnehin offen vor mir und kostet deutlich weniger? Typisch bei denselben
     Artefakten. Nicht bei bloß ähnlichem Thema, nicht bei einer Vorfrage. Sonst `keiner`.
     **Impact/Häufigkeit ehrlich wählen** – sie entscheiden nicht nur die Reihenfolge, sondern ob
     der Drain überhaupt eine Session beansprucht. `GERING` zählt 0 („keine Folge", nicht „wenig")
     und wird nie einzeln behandelt: Hochstufen aus Höflichkeit kauft dem Projekt eine Session ab,
     Abstufen aus Bequemlichkeit versenkt den Eintrag.
     KEINE Lösung jetzt umsetzen, wenn sie aufgeschoben/nicht-trivial ist – die Retro evaluiert
     (Evaluierungs-Gate).

4. `docs/history/sessions/session_NNN.md` – neue Session-Datei anlegen
   Inhalt = **was in dieser Session passierte** (Historie): Implementiertes, Entscheidungen, Probleme, Review-/Subagent-Beobachtungen.
   **Scope-Disziplin:** (a) KEIN vorwärtsgerichteter Zustand (offene Punkte / nächster Lauf) – der lebt in `AGENT_MEMORY` „Nächste Prioritäten" (auto-geladen) + ist via `next_run.py` ableitbar; in read-only Historie wäre er sofort stale. (b) Learnings/Beobachtungen nur als knappe ID + Ein-Satz + Verweis auf die kanonische Quelle (`lessons_learned.md`/`observations.md`), kein nacherzählter Inhalt (Drift-Schutz, Single Source of Truth).
   Wird NACH Doku-Änderungen erstellt (damit finaler Zustand widergespiegelt wird).

5. `docs/kaizen/lessons_learned.md` – Einträge schreiben:

   **Per Script schreiben**, nicht per Edit – das vergibt die ID, findet den Session-Abschnitt (oder legt ihn an) und erzeugt die parse-kritische Bullet-Form, die `jenga_score.py` und `retro_report.py` lesen:
   ```
   python3 .claude/scripts/lessons.py add --impact HOCH --kategorie PROZESS --kontext Doku \
       --titel "…" --quelle User --was "…" --warum "…" --regel "…" --cm-bezug CM-S116-1
   ```
   Bestehende Einträge nachlesen: `python3 .claude/scripts/lessons.py get LL-SNNN-N`.

   **`--cm-bezug` ist für KRITISCH und HOCH Pflicht**, bei MITTEL/GERING optional – gibt es dort
   einen Bezug, gern eintragen; sonst weglassen. Zulässig ist eine in `countermeasures.md`
   existierende CM-ID oder `neu`, falls keine bestehende Maßnahme passt. Der Anschluss entsteht
   damit hier, solange der Kontext frisch ist; die Retro überträgt ihn.

   Eintrag-Format + Erfassungs-Test + Beispiel: **Header von `docs/kaizen/lessons_learned.md`**. Impact/Kategorie-Definitionen + Reaktionsregeln: `docs/kaizen/process.md`

   **Andon-Cord:** KRITISCH-Findings wurden bereits behandelt – trotzdem dokumentieren.

   **IDs für neue Einträge:** Jeder neue Eintrag bekommt eine ID `LL-S<NNN>-<n>`,
   platziert **HINTER den Tags**: `- **[HOCH] [PROZESS] [TDD] LL-S<NNN>-<n> – Kurztitel**` (vor `[` würde
   sie die Script-Regexes brechen).

   **Nur konkrete schlechte Ausgänge hierher.** Vorausschauende Beobachtungen gehören nach
   `docs/kaizen/observations.md` (billiger Erfassungs-Test: „vorausschauende Notiz, wie das System besser
   wäre?" → observations; „konkreter schlechter Ausgang aufgetreten?" → hier; beides → beide, per `Bezug:`).

   **Nach dem Schreiben prüfen:**
   - Gehört ein Eintrag in `docs/kaizen/principles.md`?
   - Gehört ein KRITISCH/HOCH-Eintrag in `docs/kaizen/countermeasures.md`?

   "Keine Learnings" nur mit expliziter Begründung akzeptabel.

6. `docs/history/sessions/index.md` – neue Zeile ergänzen
   Format: `| <Nr> | <Datum> | <Phase> | <Kurzfassung> |`. **Kurzfassung = ein Satz, *was* sich geändert hat – kein „warum"/Begründung** (das gehört in die Session-Datei); auf ADR-/Session-IDs verweisen statt Prosa. Soft-Ziel ~150, **harter Cap 300 Zeichen** – ein PreToolUse-Hook (`check-index-length.py`) blockiert zu lange neue Einträge automatisch. Für den vollen Report (inkl. grandfatherter Altbestände):
   ```bash
   python3 .claude/scripts/check-index-length.py
   ```

7. Projekt-Status aktualisieren:
   - **`docs/AGENT_MEMORY.md` schlank halten** – wird bei jedem Session-Start voll injiziert (jede Zeile kostet Token). Leitfrage: „Welche Info braucht JEDER Agent beim Start, um den Projektstatus einzuordnen?" Nur: **Phase**, **Aktuelle Story**, **Nächste Prioritäten**.
     - **Nächsten Lauf nicht von Hand pflegen:** Der Platzhalter `{{NEXT_RUN}}` in der Prioritätenliste wird beim Session-Start automatisch zum nächsten offenen Lauf aufgelöst (`next_run.py`; Mechanik: ADR-S041-7) – stehen lassen.
     - **Lauf außer der Reihe** (Priorität überschreibt die Feature-Reihenfolge, z.B. error vor sortiert): als Anstrich **über** den Platzhalter setzen, nach Umsetzung entfernen.
     - **Vorzieh-/Prioritäts-Items eng + begründet:** Jedes Item eng fassen und mit **sichtbarem Grund + Done-Zustand** notieren (`<enge Aktion> — Grund: … — Done: <woran als fertig erkennbar>`), sonst wird ein längst erledigter Grund inertial weitergeschleppt und niemand erkennt Bestandteile/Fertigstellung.
   - **Ausgelagert (nicht in AGENT_MEMORY, eigene Datei pflegen):** Technische Schuld → `docs/tech-debt.md`; offene Fragen/geparkte Diskussionen → `docs/open-questions.md`. Beide haben eigene Eintrag-Formate (Header der jeweiligen Datei).
   - **Bei Phasen-Abschluss (z.B. SKELETON → MVP):** Als erste Zeile unter "Nächste Prioritäten" eintragen:
     ```
     **Phasen-Review ausstehend:** Skill `review-code` über gesamtes Phase-Delta starten.
     ```
