---
name: implementing-feature
description: >
  6-Schritt-Workflow zum Implementieren einer User Story. Verwende diesen Skill
  wenn der User eine User Story, ein Feature oder einen Backend-Endpoint implementieren
  möchte und den vollständigen Zyklus (TDD → Review → Learnings) durchlaufen soll.
user-invocable: true
---

# Feature implementieren

Implementiere User Story $ARGUMENTS

GRUNDSATZ: Die Regeln in dieser Dokumentation sind starke Guidelines, keine absoluten Gesetze.
Gibt es sehr gute Gründe abzuweichen: sofort kommunizieren und auf Bestätigung warten.

Lege nach kurzer Analyse folgende Task-Liste an (Namenskonvention beachten):
```
TaskCreate: "1. Architektur-Check"
TaskCreate: "2. TDD-Zyklus"
TaskCreate: "3. Autor-Review"
TaskCreate: "4. Review-Agenten"
TaskCreate: "5. Learnings & Dokumentation"
```

Lies vor dem Start:
- Akzeptanzkriterien: `docs/USER_STORIES.md`
- Patterns & Design-Philosophie: `docs/ARCHITECTURE.md` (inkl. Sektion 0)
- **Allgemeine Prinzipien (PFLICHT, immer zuerst):** `docs/CODING_GUIDELINE_GENERAL.md`
- Coding-Richtlinie (PFLICHT – GENAU EINE, nicht beide):
    C#-Code → `docs/CODING_GUIDELINE_CSHARP.md`
      Endpoint oder Validierungskette → zusätzlich `docs/CSharp-ROP.md`
      Neuer Domain-Typ mit Zustandsvarianten → zusätzlich `docs/CSharp-SumTypes.md`
    TypeScript/React → `docs/CODING_GUIDELINE_TYPESCRIPT.md`
- Aktuelle Phasen-Spec: Entnehme `docs/AGENT_MEMORY.md` welche Phase aktiv ist,
  dann lies `docs/SKELETON_SPEC.md` oder `docs/MVP_SPEC.md` (API + DB)

── SCHRITT 0: ARCHITEKTUR-CHECK ─────────────────────────────────────────────
→ TaskUpdate "1. Architektur-Check": in_progress

Beantworte diese Fragen SCHRIFTLICH, bevor der erste Test geschrieben wird:

1. **Gherkin-Szenario (ATDD-Gate):** Welches Gherkin-Szenario in `features/` treibt diese Story?
   - Szenario-Tag identifizieren (z.B. `@US-NNN`). Verweis: `docs/E2E_TESTING.md`
   - **Kein Szenario vorhanden?** → STOP. Szenario zuerst schreiben (oder mit User klären).
   - Reihenfolge: Gherkin (rot) → Frontend-E2E-Test (rot) → Backend-Test (rot) → Code (grün)
   - Kein Backend- oder E2E-Test ohne darüberliegendes Gherkin-Szenario

2. **YAGNI/KISS-Scope:** Was ist das Minimal-Notwendige für die Story-Anforderungen?
   Was wäre Gold-Plating (= kein Test dafür existiert, kein Akzeptanzkriterium fordert es)?
   Notiere explizit: *"Folgendes implementiere ich NICHT: ..."*

3. **Domain-Typen & Architektur:** Brauche ich neue Domain-Typen?
   - Struktur: `readonly record struct` für Value Objects, `abstract record` für Sum-Types?
   - Error-States: Wie typisiert? (`OneOf<T, Error<string>>`, kein `T?` in Domain-Properties)
   - Alle neuen Typ-Deklarationen in `Server/` sind `internal` (kein `public` ohne Begründung)
   - Neuer Infrastruktur-Code (DbContext, DbTypes) gehört in `Infrastructure/`, nicht in `Server/`

4. **Entscheide:** Berührt die Story eine bestehende Entscheidung in `docs/history/decisions.md`?
   Falls ja, gilt sie noch? Falls neue Architekturentscheidung nötig: **User fragen, bevor Code
   geschrieben wird.** Selbst entschiedenes in `docs/history/decisions.md` dokumentieren.

PFLICHT-OUTPUT: Schriftliche Antwort auf alle vier Punkte.

── SCHRITT 1–3: TDD-ZYKLUS ─────────────────────────────────────────────────
→ TaskUpdate "1. Architektur-Check": completed | TaskUpdate "2. TDD-Zyklus": in_progress

→ Führe TDD-Zyklus nach `docs/TDD_PROCESS.md` aus (RED → GREEN → REFACTOR).

Wiederhole den Zyklus für jedes Verhalten der Story. Erst wenn ALLE Verhaltensweisen
abgedeckt sind, weiter zu Schritt 4.

Nach Schritt 3: Aktualisiere `docs/AGENT_MEMORY.md`:
  aktive_story: US-XXX | schritt: 3/6 – REFACTOR | naechster: 4/6 – AUTOR-REVIEW

── SCHRITT 4: AUTOR-REVIEW ──────────────────────────────────────────────────
→ TaskUpdate "2. TDD-Zyklus": completed | TaskUpdate "3. Autor-Review": in_progress

Gehe `docs/REVIEW_CHECKLIST.md` vollständig durch.
PFLICHT-OUTPUT: Checkliste mit ✅/⚠️/❌ pro Punkt.
Fixe alle Findings sofort. Erst dann weiter.

── SCHRITT 5: REVIEW-AGENTEN ────────────────────────────────────────────────
→ TaskUpdate "3. Autor-Review": completed | TaskUpdate "4. Review-Agenten": in_progress

→ Führe den `review-code` Skill aus.

ABBRUCHBEDINGUNG: Falls nach 3 vollständigen Runden noch ❌-Findings bestehen,
die nicht ohne Architektur-Entscheidung lösbar sind:
  → Finding + Kontext dokumentieren
  → User fragen, wie weiter vorgegangen werden soll

── SCHRITT 6: LEARNINGS & DOKUMENTATION ─────────────────────────────────────
→ TaskUpdate "4. Review-Agenten": completed | TaskUpdate "5. Learnings & Dokumentation": in_progress

HARTES GATE – das Feature gilt als NICHT FERTIG bis dieser Schritt abgeschlossen ist.

PFLICHT: Eintrag in `docs/history/lessons_learned.md` (Format beachten).
Pflichtfelder:
  - Was war schwierig / hat nicht funktioniert – und warum?
  - Learnings für die nächste Session
  - Dokumentations-Änderungsvorschläge (jeden Punkt explizit beantworten)
"Keine Learnings" ist nur mit expliziter, schriftlicher Begründung akzeptabel.

PFLICHT: Dokumentations-Check – prüfe explizit für jede Datei:
  `docs/ARCHITECTURE.md`      Muss etwas ergänzt/korrigiert werden?
  `docs/GLOSSARY.md`          Neues Konzept? Begriffsdefinition unscharf?
  `docs/REVIEW_CHECKLIST.md`  Fehlender Prüfpunkt aufgefallen?
  `docs/NFR.md`               Definition of Done unvollständig?
  Phasen-Spec (SKELETON/MVP)  Schema oder API-Beschreibung veraltet?

Falls ja, unterscheide nach Typ:
  - Korrektur (Tippfehler, toter Link, veralteter Pfad): direkt korrigieren.
  - Strukturelle Änderung (neues Pattern, geänderte Policy):
    Vorschlag formulieren und User zur Genehmigung vorlegen. NICHT eigenständig anpassen.

Aktualisiere `docs/AGENT_MEMORY.md` (Status, technische Schuld, offene Fragen).
Erstelle Commit: "US-XXX: [kurze Beschreibung]"

Das Feature ist erst "Done" wenn alle 6 Schritte vollständig abgeschlossen sind.
