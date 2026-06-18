---
name: review-code
description: >
  Code-Review nach einer Implementierung: Selbstcheck via docs/process/review-checklist.md,
  dann spezialisierte Review-Agenten spawnen und Findings als strukturierte Liste
  zurückgeben. Wird von implementing-scenario Schritt 5 direkt ausgeführt (kein
  Subagent-Wrapper). Kann auch standalone auf beliebigem Code angewendet werden.
user-invocable: true
---

# Skill: review-code

## Eingabe

- Scope + Szenario-Tag (oder freier Scope bei standalone-Aufruf)
- Geänderte Dateien (Pfade oder git-diff-Auszug)
- **Stryker-Suppression-Report:** neue Suppressionen aus dem REFACTOR-Schritt
  (Format: Datei:Zeile – Begründung), oder leer wenn keine neuen Suppressionen

Fehlende Eingaben bei standalone-Aufruf: Scope → User nach Beschreibung der Änderung fragen.
Geänderte Dateien → `git diff` (staged + unstaged) als Standard verwenden.

---

## Ablauf

Lege zu Beginn eine Task-Liste an, sofern der Skill standalone aufgerufen wird. Bei Einbettung in einen anderen Skill (z.B. aus implementing-scenario heraus) keine neue Task-Liste anlegen und keine TaskUpdate-Aufrufe für interne Schritte – der Aufrufer verwaltet die Task-Liste. Stattdessen: kurze Status-Zeile pro Schritt ausgeben (z.B. „→ Schritt 1 (Selbstcheck): abgeschlossen").

```
TaskCreate: "1. Selbstcheck (docs/process/review-checklist.md)"
TaskCreate: "2. Suppression-Report bewerten"
TaskCreate: "3. Review-Agenten spawnen"
TaskCreate: "4. Findings zusammenführen"
```

### 1. Selbstcheck (docs/process/review-checklist.md)
→ TaskUpdate "1. Selbstcheck (docs/process/review-checklist.md)": in_progress

Gehe `docs/process/review-checklist.md` systematisch Punkt für Punkt durch:
- Architecture Layer (internal-Typen, kein InternalsVisibleTo, Ports-only-Tests)
- Allgemeine Prinzipien (KISS, Naming)
- Domain Modeling
- Komplexität & Refactoring
- Tests
- Test-Audit (US-Tag im Testnamen, Traceability, kein Gold-Plating)

Für jedes Finding: Schweregrad ❌/⚠️/✅ + Guideline-Referenz (Datei + Sektion) notieren.
Findings werden gesammelt – nicht sofort selbst behoben.

### 2. Suppression-Report bewerten
→ TaskUpdate "1. Selbstcheck (docs/process/review-checklist.md)": completed | TaskUpdate "2. Suppression-Report bewerten": in_progress

Jeden Eintrag im übergebenen Stryker-Suppression-Report einzeln prüfen. Referenz:
`docs/process/tdd-process.md` Sektion „Stryker-Survivor behandeln".

Für jeden Eintrag: Beweist die Begründung echte Äquivalenz oder Nichttestbarkeit –
oder klingt sie nur plausibel? (`docs/kaizen/principles.md`: semantische Korrektheit
prüfen, nicht blind übernehmen.) Schwache oder fehlende Begründung → ❌ Finding.

Kein Suppression-Report übergeben oder leer → Schritt überspringen.

### 3. Review-Agenten spawnen
→ TaskUpdate "2. Suppression-Report bewerten": completed | TaskUpdate "3. Review-Agenten spawnen": in_progress

⚠️ **Context-Freiheit:** Jeden Agenten ohne Iterations-Vorwissen spawnen – weder frühere
Findings noch als false positive bekannte Punkte im Prompt. Filtering geschieht im
Anschluss. Begründung: Vorwissen dämpft die Kritikbereitschaft strukturell – der Reviewer
denkt „wurde ja schon reviewt". Unabhängige Urteile, dann zentral filtern.

Scope bestimmt welche Agenten nötig sind:

| Was wurde geändert? | Agenten |
|--------------------|---------|
| Änderung ohne Verhaltensänderung (z. B. Rename, Refactoring ohne Logik-Änderung) | `code-quality-auditor` |
| Neue Funktionalität / Verhaltensänderung | `code-quality-auditor` + `functional-correctness-auditor` + `test-quality-auditor` |
| + API-Grenze, User-Input oder Auth berührt | + `security-auditor` |
| + Frontend-Komponenten geändert | + `ux-ui-auditor` |
| Nur Tests geändert (kein Produktionscode) | `test-quality-auditor` |
| Nur Suppressionen hinzugefügt | Schritt 2 deckt das ab – kein Agent-Spawn nötig |
| Nur Dokumentation / Kommentare geändert | `code-quality-auditor` |

Jeden Agenten via Agent-Tool mit `subagent_type: "<name>"` spawnen (z.B. `subagent_type: "code-quality-auditor"`) – die Namen entsprechen der Tabelle (es sind registrierte Agenten in `.claude/agents/`, read-only).

**Modellwahl vor Spawn (OBS-S085-8):** Auditoren laufen per Default auf `model: sonnet` (Frontmatter). Den `model`-Parameter des Agent-Tools nur dann setzen, wenn die Änderung erhöhte Tiefe verlangt (z.B. subtile Nebenläufigkeit, nicht-triviale Sicherheits-Edge-Cases) → gezielt `opus` für den betroffenen Auditor; Routine-Reviews bleiben auf `sonnet`. Vor jedem Spawn kurz prüfen: reicht der Default?

Alle zutreffenden Agenten parallel spawnen – sie reviewen denselben Diff und haben keine gegenseitigen Abhängigkeiten. Bei Unsicherheit über den Scope: `git diff` selbst auswerten; bei genuiner Ambiguität User fragen.

Agent-Prompts enthalten (je Agent):
- Geänderte Dateien / git diff
- Anforderung: jedes Finding nennt Schweregrad (❌/⚠️), Guideline-Referenz
  (konkrete Datei + Sektion) und Begründung (nicht nur Guideline zitieren)
- Hinweis: Projekt-Guidelines (`docs/guidelines/coding-guideline-*.md`) haben Vorrang vor
  agenten-eigenen Checklisten

### 4. Findings zusammenführen
→ TaskUpdate "3. Review-Agenten spawnen": completed | TaskUpdate "4. Findings zusammenführen": in_progress

Alle Findings aus Selbstcheck + Suppression-Bewertung + Agenten zusammenführen. Für jedes Finding prüfen:
ist die Begründung semantisch korrekt – „Es ist implementierbar" ≠ „Es ist das richtige
Verhalten"? Insbesondere Performance-Tradeoff-Argumente und stille Fallbacks kritisch hinterfragen.

Ein Finding gilt als false positive wenn die zitierte Guideline im konkreten Code-Kontext nicht
greift (z.B. agenten-eigene Checkliste widerspricht Projektguideline) oder wenn die Begründung
durch den Code-Kontext widerlegbar ist. False positives aus dem Report herausnehmen und kurz begründen.

**Ausgabe (strukturierte Liste für den Orchestrator):**

```
❌ Must Fix:
- [Quelle: Selbstcheck|Agent] [Datei:Zeile] [Guideline: <Pfad>, <Sektion>] <Beschreibung>

⚠️ Improvements:
- [Quelle: Selbstcheck|Agent] [Datei:Zeile] [Guideline: <Pfad>, <Sektion>] <Beschreibung>

Suppression-Bewertung:
- [Datei:Zeile] → valide | ❌ Begründung unzureichend: <Warum>

✅ Keine weiteren Findings
```

→ TaskUpdate "4. Findings zusammenführen": completed
