# Session 101 – 2026-07-10

**Phase:** SKELETON
**Story:** US-904 (Zutaten) – run-2 „Anlegen·Dialog-Verhalten" abgeschlossen

## Implementiert

### US-904 run-2-Rest (S1–S3) + Backdrop-Szenario
run-2 war seit S100 teilweise erledigt (6/9 Szenarien). Diese Session schließt den Rest ab und ergänzt ein spec-first-Szenario:

- **S1 „Abbrechen ist während des Speicherns deaktiviert"** – `disabled={isPending}` am Abbrechen-Button.
- **S2 „Der Dialog lässt sich während des Speicherns nicht per Escape schließen"** – neuer `handleClose`-Guard (`if (isPending) return; onClose()`) am Dialog-`onClose` (deckt Escape **und** Backdrop).
- **S3 „Nach fehlgeschlagenem Speichern und Abbrechen fehlerfrei"** (Bug R1) – `useResultMutation` um `reset()` erweitert (4-Tupel `[mutate, error, isPending, reset]`); beim Schließen via `handleCancel` aufgerufen → Fehlerzustand wird zurückgesetzt.
- **Backdrop-Szenario (neu, spec-first retroaktiv):** „Der Dialog lässt sich während des Speicherns nicht per Backdrop-Klick schließen" – das Verhalten existierte bereits emergent (gleicher `handleClose`-Guard); explizit spezifiziert (Gherkin + E2E + Component-Test) auf User-Entscheidung, für Konsistenz mit den Geschwister-Schließ-Pfaden.

Ergebnis: run-2 vollständig (10 Szenarien), Vitest 23/23, Playwright 18/18, Stryker 100 %.

### Review-Verbesserungen (R1–R6, nach 0-Must-Fix-Review)
- **R1** Test-Duplikation (Rule-of-Three) aufgelöst: Helper `renderWithPendingSave()` (Component) + `submitWithDelayedPost(page)` (E2E).
- **R2** Settle-Fenster als benannte Konstante `DIALOG_EXIT_SETTLE_MS` (mit Bezug zur MUI-Exit-Transition).
- **R3** E2E-Escape-Test: `toBeDisabled`-Sync vor Escape ergänzt (Parität zum Component-Test).
- **R4** Abbrechen-Button über `handleClose` verdrahtet (ein Guard-Punkt, `disabled` bleibt zusätzlich).
- **R5** benannter `handleCancel` statt anonymer Inline-Arrow.
- **R6** ADR-Kommentarblock in `useResultMutation` auf Verweis eingedampft.

### Prozess-/Config-Fixes
- **P1 (LSP-Zugang):** LSP war nur dem Orchestrator zugeteilt, NICHT den Layer-Implementern/Auditoren → die LSP-Validierungs-OBS (OBS-S085-4) sammelte Evidenz gegen Agenten ohne LSP. Fix: `LSP` in die `tools` von frontend-/backend-layer-implementer + code-quality-/functional-correctness-/test-quality-/ux-ui-/security-auditor (workflow-auditor bewusst nicht – auditiert Prozess, nicht Code). OBS-S085-4 entsprechend aktualisiert.
- **P3 (max-lines für Tests):** `max-lines` in `Client/eslint.config.js` für `*.{test,spec}.{ts,tsx}` deaktiviert (Erweiterung von OBS-S085-7 auf die Datei-Ebene) – Testdateien wachsen strukturell linear mit der Szenario-Zahl; `complexity`/`max-depth` bleiben aktiv.
- **gherkin-workshop-Policy:** State-Transition-Referenz (`agent-b-state-transition.md`) um eine Pending-Zustand-Regel ergänzt: bei Dialog+Pending jede Schließ-/Kontextwechsel-Affordance (Button, Escape, Backdrop) + Fehler-Reset als eigene Prüfdimension abdecken → verhindert die Reviewer-abhängige Lücke, durch die die Backdrop-Sperre bisher unspezifiziert emergent war.

## Probleme / Erkenntnisse

- **Vakuöse Negativ-Tests (LL-S101-1, CM-S101-1):** Zwei Tests waren zunächst vakuös grün – E2E-Escape (Fokus fiel auf `<body>` statt ins Modal) und Component-Backdrop (`fireEvent.click` ohne `mousedown` → MUIs zweistufige Backdrop-Erkennung greift nicht). Gefangen durch RED-first (Escape) bzw. den **Faithfulness-Check** (Backdrop: Guard temporär entfernt → beide Tests rot → wiederhergestellt). Regel in `coding-guideline-typescript.md` §6 + CM-S101-1.
- **Flaky unter Stryker-Last (OBS-S101-1):** `ReopenDialogAfterCancel` lief unter Stryker-Systemlast in einen 5000-ms-Timeout, isoliert grün – kann einen Übergabe-Hash fälschlich scheitern lassen.
- **Orchestrator pollt arbeitende Subagenten (OBS-S101-2, Quelle: User):** mehrfach Status erfragt, während der Subagent noch lief; vermutlich mehrdeutige `idle_notification`-Semantik im Team-Tooling.

## Offene Punkte

- **TD-S101-1:** `useResultMutation`-4-Tupel → Objekt-Rückgabe (mit nächstem großen Hook-Schritt / voller MutationState-Union, ADR-S083-2).
- **R10 (verworfen):** `aria-live`-Pending-Feedback für Screenreader – über Guideline-Minimum, nicht erfasst.
- **Soft-Warning:** `max-lines-per-function` `IngredientsPage` 51/50 – beobachten; Fix = `IngredientList` extrahieren, wenn die Komponente weiter wächst.

## Nächster Lauf
run-3 „Anlegen·Name-Validierung" (Full-Stack) – siehe AGENT_MEMORY.
