---
name: implementing-scenario
description: >
  6-Schritt-Workflow zum Implementieren eines einzelnen Gherkin-Szenarios mit vollständigem
  Double-Loop TDD-Zyklus (E2E → Unit/Integration → Autor-Review → Review-Agenten → Learnings).
  Verwende diesen Skill immer wenn ein einzelnes @US-NNN-Szenario end-to-end implementiert
  werden soll – von Architektur-Check über TDD bis Dokumentation. Voraussetzung: das Szenario
  muss bereits via gherkin-workshop freigegeben sein. Typische Trigger: „implementiere Szenario X",
  „fang mit dem ersten Szenario an", „nächstes Szenario", „happy-path implementieren",
  oder direkter Aufruf via /implementing-scenario. Dieser Skill deckt genau EIN Szenario pro
  Durchlauf ab – für das nächste Szenario neu aufrufen.
user-invocable: true
---

# Szenario implementieren

Implementiere Szenario $ARGUMENTS

GRUNDSATZ: Die Regeln in dieser Dokumentation sind starke Guidelines, keine absoluten Gesetze.
Gibt es sehr gute Gründe abzuweichen: sofort kommunizieren und auf Bestätigung warten.

Aufruf: `/implementing-scenario @US-NNN-tag "Szenario-Titel"`
Beispiel: `/implementing-scenario @US-904-happy-path "Neue Zutat anlegen"`

Lege nach kurzer Analyse folgende Task-Liste an (Regeln: `docs/TASK_SYSTEM.md`):
```
TaskCreate: "Schritt 0: Architektur-Check"
TaskCreate: "Schritt 1–3: TDD-Zyklus (Double-Loop)"
TaskCreate: "Schritt 4: Autor-Review"
TaskCreate: "Schritt 5: Review-Agenten"
TaskCreate: "Schritt 6: Learnings & Dokumentation"
```

Lies vor dem Start:
- Akzeptanzkriterien: `docs/USER_STORIES.md`
- Patterns & Design-Philosophie: `docs/ARCHITECTURE.md` (inkl. Sektion 0)
- Aktuelle Phasen-Spec: Entnehme `docs/AGENT_MEMORY.md` welche Phase aktiv ist,
  dann lies `docs/SKELETON_SPEC.md` oder `docs/MVP_SPEC.md` (API + DB)

── SCHRITT 0: ARCHITEKTUR-CHECK ─────────────────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": in_progress

Beantworte diese Fragen schriftlich, bevor der erste Test geschrieben wird.
Der Schritt ist wichtig, weil nachträgliche Architekturentscheidungen teuer sind –
einmal Code da, ist die Versuchung groß, die Entscheidung an den Code anzupassen statt umgekehrt.

1. **Gherkin-Szenario (ATDD-Gate):** Ist das Szenario `$ARGUMENTS` in `features/` vorhanden?
   - Öffne das zugehörige Feature-File und suche nach Tag + Titel.
   - Nicht vorhanden? → STOP. Erst `gherkin-workshop` für die User Story ausführen,
     dann zurückkommen. Ohne freigegebenes Gherkin-Szenario fehlt die objektive
     Fertigstellungsbedingung – der Code kann nicht als "Done" gelten.
   - Vorhanden: Notiere Given/When/Then vollständig – das ist die exakte Spec für diesen Durchlauf.
   - Verweis auf Konventionen: `docs/E2E_TESTING.md`

2. **YAGNI/KISS-Scope:** Was ist das Minimal-Notwendige für genau dieses Szenario?
   Was wäre Gold-Plating (= kein Test dafür existiert, kein Akzeptanzkriterium fordert es)?
   Notiere explizit: *"Folgendes implementiere ich NICHT: ..."*

3. **Domain-Typen & Architektur:** Brauche ich neue Domain-Typen?
   - Struktur: `readonly record struct` für Value Objects, `abstract record` für Sum-Types?
   - Error-States: Wie typisiert? (`OneOf<T, Error<string>>`, kein `T?` in Domain-Properties)
   - Alle neuen Typ-Deklarationen in `Server/` sind `internal` (kein `public` ohne Begründung)
   - Neuer Infrastruktur-Code (DbContext, DbTypes) gehört in `Infrastructure/`, nicht in `Server/`

4. **Entscheide:** Berührt das Szenario eine bestehende Entscheidung in `docs/history/decisions.md`?
   Falls ja, gilt sie noch? Falls neue Architekturentscheidung nötig: User fragen, bevor Code
   geschrieben wird. Selbst entschiedenes in `docs/history/decisions.md` dokumentieren.

Schriftliche Antwort auf alle vier Punkte.
Dieser Schritt ist reine Analyse – noch kein Produktionscode schreiben. Domain-Typen und
Implementierungsdetails entstehen im TDD-Zyklus, wenn Tests sie erzwingen.

── SCHRITT 1–3: TDD-ZYKLUS (DOUBLE-LOOP) ───────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": completed | TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": in_progress

Ziel: genau das Szenario aus $ARGUMENTS vollständig grün bekommen – nicht mehr, nicht weniger.
Vollständige Double-Loop-Anleitung (äußerer/innerer Loop, RED→GREEN→REFACTOR je Schicht):
`docs/TDD_PROCESS.md` (Sektion "Outside-In ATDD / Double-Loop TDD")

### Äußerer Loop – E2E-Test (Playwright)

Schreibe zuerst den Playwright-Test für das Szenario (Given/When/Then 1:1 umgesetzt).
Führe den Test aus und zeige die Fehlermeldung – das beweist, dass der Test echtes Verhalten
misst und noch nicht durch bestehende Implementierung zufällig grün werden kann.
Dieser Test bleibt rot, bis alle inneren Loops abgeschlossen sind – das ist gewollt.

### Innerer Loop – Schicht für Schicht (outside-in)

Für jede Implementierungsschicht, die das Szenario berührt, einen vollständigen RED→GREEN→REFACTOR-Zyklus durchführen:
1. Lies die relevante Coding-Guideline für diese Schicht – da ein Szenario mehrere Schichten
   berühren kann, passiert das je Schicht neu:
   `docs/CODING_GUIDELINE_GENERAL.md` gilt immer (sprachunabhängige Grundprinzipien)
   C# → `docs/CODING_GUIDELINE_CSHARP.md` (Endpoint/Validierung: + `CSharp-ROP.md`; neuer Sum-Type: + `CSharp-SumTypes.md`)
   TypeScript/React → `docs/CODING_GUIDELINE_TYPESCRIPT.md`
2. Test schreiben (auf der passenden Ebene: Unit / Integration)
3. Test ausführen, Fehlermeldung zeigen (beweist: roter Test fordert echtes Verhalten)
4. Minimale Implementierung ("fake it till you make it" – hardcodierte Rückgabewerte sind erlaubt)
5. Alle Tests ausführen, Ergebnis zeigen (alle grün, nichts kaputt)
6. Refactor
7. Weiter mit nächster Schicht

**Schicht-Reihenfolge (outside-in):**
- Backend-Szenarien: API-Endpoint → Domain-Typen/Validierung → Service/Repository
- Frontend-Szenarien: React-Komponente → Service-Integration → API-Mock/Contract
- Full-Stack-Szenarien: E2E → Frontend (oben) → Backend (oben)

### E2E-Loop schließen

Wenn alle inneren Loops abgeschlossen sind: Playwright E2E-Test erneut ausführen und Ergebnis zeigen.
Wenn noch rot: fehlende Verbindung identifizieren (Routing? API-Integration? Komponente?)
und den entsprechenden inneren Loop nochmal durchlaufen.

Aktualisiere `docs/AGENT_MEMORY.md` (Abschnitt "Aktueller Stand" → Feld "Letzter Stand"):
  Szenario in Arbeit: $ARGUMENTS | Schritt: 3/6 – REFACTOR abgeschlossen | Nächstes: 4/6 – Autor-Review

── SCHRITT 4: AUTOR-REVIEW ──────────────────────────────────────────────────
→ TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": completed | TaskUpdate "Schritt 4: Autor-Review": in_progress

Gehe `docs/REVIEW_CHECKLIST.md` vollständig durch.
Dokumentiere das Ergebnis mit ✅/⚠️/❌ pro Punkt – sichtbare Lücken jetzt sind billiger
als dieselben Findings durch einen externen Reviewer später.
Fixe alle Findings sofort. Erst dann weiter.

── SCHRITT 5: REVIEW-AGENTEN ────────────────────────────────────────────────
→ TaskUpdate "Schritt 4: Autor-Review": completed | TaskUpdate "Schritt 5: Review-Agenten": in_progress

Führe den `review-code` Skill aus.

Schritt ist abgeschlossen wenn:
- Alle ❌-Findings aus review-code sind behoben, oder
- Verbleibende Findings wurden mit Begründung dokumentiert und dem User zur Entscheidung vorgelegt

Falls nach 3 vollständigen Runden noch ❌-Findings bestehen, die ohne Architektur-Entscheidung
nicht lösbar sind: Finding + Kontext dokumentieren, User fragen wie weiter vorgegangen werden soll.

── SCHRITT 6: LEARNINGS & DOKUMENTATION ─────────────────────────────────────
→ TaskUpdate "Schritt 5: Review-Agenten": completed | TaskUpdate "Schritt 6: Learnings & Dokumentation": in_progress

Learnings, die hier nicht festgehalten werden, tauchen in der nächsten Session als vermeidbare
Fehler wieder auf. Das Szenario gilt erst nach Abschluss dieses Schritts als Done.

Eintrag in `docs/kaizen/lessons_learned.md` (Format: `docs/kaizen/PROCESS.md`).
Pflichtfelder:
  - Was war schwierig / hat nicht funktioniert – und warum?
  - Learnings für die nächste Session
  - Dokumentations-Änderungsvorschläge (jeden Punkt explizit beantworten)
Gibt es wirklich keine Learnings, schreibe das explizit mit Begründung auf.

Dokumentations-Check – prüfe explizit für jede Datei:
  `docs/ARCHITECTURE.md`      Muss etwas ergänzt/korrigiert werden?
  `docs/GLOSSARY.md`          Neues Konzept? Begriffsdefinition unscharf?
  `docs/REVIEW_CHECKLIST.md`  Fehlender Prüfpunkt aufgefallen?
  `docs/NFR.md`               Definition of Done unvollständig?
  Phasen-Spec (SKELETON/MVP)  Schema oder API-Beschreibung veraltet?

Falls ja, unterscheide nach Typ:
  - Korrektur (Tippfehler, toter Link, veralteter Pfad): direkt korrigieren.
  - Strukturelle Änderung (neues Pattern, geänderte Policy):
    Vorschlag formulieren und User zur Genehmigung vorlegen. Nicht eigenständig anpassen.

Aktualisiere `docs/AGENT_MEMORY.md` (Abschnitt "Aktueller Stand" → Feld "Letzter Stand"):
  - Szenario $ARGUMENTS als abgeschlossen markieren
  - Nächstes Szenario aus dem Feature-File benennen (nächster Aufruf: `/implementing-scenario ...`)
  - Technische Schuld und offene Fragen aktualisieren

Erstelle einen neuen Commit (kein Amend): `"US-XXX: [Szenario-Titel]"`

Das Szenario ist Done. Nächstes Szenario = neuer `/implementing-scenario`-Aufruf.
