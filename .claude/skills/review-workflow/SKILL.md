---
name: review-workflow
description: >
  Auditiert das Workflow-/Prozess-DESIGN des Projekts und verbessert es iterativ, bis keine groben
  Schnitzer mehr bleiben. Abgrenzung: Doku-Qualität → review-docs; Produktionscode → review-code.
  Spawnt pro Runde einen frischen workflow-auditor (Frische-Augen-Prinzip). Nur manuell aufrufen via
  /review-workflow oder expliziter Erwähnung („Workflow-Review", „Prozess-Audit", „taugt mein Workflow noch?")
  – nicht auto-triggern.
user-invocable: true
---

# Workflow-Review (Audit + Verbesserungs-Loop)

Auditiere das Prozess-/Workflow-**Design** und verbessere es Runde für Runde, bis keine groben
Schnitzer (❌ / HOCH-Impact) mehr bestehen.

Was dieser Skill NICHT prüft – wenn das gefragt ist, den passenden Skill nehmen:
- **Doku-Qualität** (Progressive Disclosure, Konsistenz, Verständlichkeit der Texte) → `review-docs`
- **Produktionscode** → `review-code`

## Warum ein Loop mit frischen Agenten?

Ein Workflow-Audit, das du selbst im Haupt-Thread machst, hat keine frischen Augen – du hast die
Dateien womöglich gerade selbst geschrieben und bist betriebsblind. Deshalb delegierst du die
eigentliche Analyse jede Runde an einen **neuen** `workflow-auditor` in isoliertem Kontext.

Entscheidend: Der Agent bekommt **kein Wissen über frühere Runden** – weder frühere Befunde noch was
bereits „gefixt" wurde. Sonst denkt er „wurde ja schon reviewt" und wird milder (Grund: `docs/kaizen/principles.md`).
Du (Haupt-Thread) hältst den Verlauf; jeder Agent startet bei null.

## Ablauf

Task-Liste anlegen (`docs/process/task-system.md`):
```
TaskCreate: "Workflow-Audit (Loop bis 0 grobe Schnitzer)"
```
Pro Runde eine Status-Zeile ausgeben: „→ Runde N: M grobe Schnitzer".

### Pro Runde

**1. Frischen Auditor spawnen.** Agent-Tool mit `subagent_type: "workflow-auditor"`, ohne Kontext aus
früheren Runden, **kein** `run_in_background` (sonst werden Berechtigungsanfragen des Agenten abgelehnt).
Der Agent liest die Workflow-Dateien selbst und kennt seine Prüf-Dimensionen – seine Definition in
`.claude/agents/workflow-auditor.md` ist die Quelle, hier nicht duplizieren. Rückgabe: Bewertung pro
Dimension (✅/⚠️/❌), priorisierte Vorschläge, Gesamtfazit.

**2. Befunde nach Impact sortiert dem User zeigen.** Scanbare Tabelle, ein Befund pro Zeile, sortiert
HOCH → MITTEL → NIEDRIG:

```
| # | Impact | Problem (1–2 kurze Sätze) | Wo? |
|---|--------|---------------------------|-----|
```

Impact-Maßstab:
- **HOCH** (= grober Schnitzer): führt wahrscheinlich zu falschem Agentenverhalten, ignoriertem Kontext
  oder einem Prozess-Single-Point-of-Failure.
- **MITTEL**: verschlechtert Qualität/Effizienz merklich, aber kein direkter Fehler.
- **NIEDRIG**: kosmetisch / nice-to-have.

**3. Grobe Schnitzer = ❌ / HOCH.**
- Keine mehr → **Loop beenden** (Schritt 6). Verbleibende ⚠️/MITTEL/NIEDRIG dem User zur optionalen
  Behebung vorlegen.
- Sonst → Schritt 4.

**4. Befunde interaktiv abarbeiten.** Pro Befund (oder sinnvoll gruppierten Satz am selben Ort):
- Titel + zitierte Stelle zeigen.
- Bei klarem Fix: konkrete Empfehlung. Bei Abwägung: 2–3 Optionen mit kurzer Begründung.
- Auf die Entscheidung des Users warten, dann umsetzen (Dateien editieren).
- Ist unklar, ob die Lösung mit den Guidelines vereinbar ist, oder ist das Zielbild des Users nicht
  klar → **`grill-me` aufrufen, bevor** du änderst. Lieber einmal zu viel fragen als in die falsche
  Richtung ändern.

**5. Nächste Runde.** Zurück zu Schritt 1: ein neuer frischer Auditor verifiziert unvoreingenommen, ob
die Fixes greifen und ob verbleibende oder neu entstandene grobe Schnitzer existieren.

**6. Abschluss.** Kurzes Fazit: welche groben Schnitzer behoben wurden, was bewusst offen bleibt.

### Terminierung
- 0 grobe Schnitzer in einer Runde → fertig.
- **Sicherheitskappe:** Nach 5 Runden ohne saubere Runde → STOP. Dem User erklären, welche Befunde
  hartnäckig sind und warum, und fragen, wie weiter verfahren werden soll. Hartnäckigkeit ist selbst
  ein Signal – meist steckt eine tiefere Designfrage dahinter, die eine bewusste Entscheidung braucht.
