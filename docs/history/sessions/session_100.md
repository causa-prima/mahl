# Session 100 – 2026-07-06 (fortgesetzt 2026-07-07/08)

**Schwerpunkt:** US-904 run-2 „Anlegen·Dialog-Verhalten" (Frontend-only) via `implementing-scenario`; danach Review-Loop, Tooling-Härtung (`.stryker-tmp`), Doku-Schärfung an je einer Stelle, und drei neue run-2-Szenarien spec-first für die nächste Session.

## Umgesetzt: US-904 run-2 (Frontend-only, 2026-07-06)

3 neu gebaute Szenarien (`RequiredFieldsAreMarked`, `FocusOnFirstField`, `SaveInFlight`); 3 weitere run-2-Szenarien waren bereits aus der run-1-Arbeit grün.

- **UI:** `required` (Pflichtfeld-Asterisk), Autofokus via `slotProps.transition.onEntered` (MUI-Grow setzt Paper initial `visibility:hidden` → `autoFocus` greift in echten Browsern nicht), `disabled={isPending}` am Speichern-Button, echtes `<form>` via Paper-Slot (Enter-Submit), `onClose` (Escape/Backdrop). `CreateIngredientDialog` aus `IngredientsPage` extrahiert.
- **Hook:** `useResultMutation` liefert 3-Tupel `[mutate, error, isPending]` (nur `isPending`, ADR-S083-2-Addendum – volle `MutationState`-Union bleibt aufgeschoben).
- **Guard-Saga:** Ein Fokus-Steal-Guard wurde testweise gebaut und wieder entfernt (unerreichbarer `TEXTAREA`-Arm + „Guard-aus"-Mutant überlebt Stryker deterministisch = nicht deterministisch testbar) → `onEntered`-Fokus bedingungslos, Tests warten vor dem ersten `user.type` auf den Autofokus (`awaitDialogAutofocus`). Festgehalten in **ADR-S100-1**.
- Stryker 100 % (0 Survivor), E2E 14/14, vitest, `tsc -b`/ESLint clean.

## Review-Loop (Schritt 5, 2026-07-07) – 4 context-freie Auditoren

- code-quality: 0 ❌; test-quality: 0 ❌; ux-ui: 1 ❌ = Fokus-nach-Fehler (bereits **TD-S094-1**, terminiert auf run-4); functional-correctness: 2 ❌.
- Die zwei ❌ (functional) sind **real, aber szenariolos und cross-cluster/vorbestehend**: **R1** Stale-Fehler nach Fehler→Abbrechen→Reopen (`closeDialog` resettet `saveError` nicht); **R2** Datenverlust-Race (Abbrechen/Escape während Pending nicht gesperrt → spät auflösender POST schließt neu geöffneten Dialog). → per Spec-first-Prinzip zu neuen Szenarien (s.u.), kein Ad-hoc-Fix.
- **Test-Politur umgesetzt:** I1 (6× duplizierter Fokus-Wait → Helper `awaitDialogAutofocus`), I2 (E2E prüft jetzt das sichtbare Asterisk, nicht nur die `required`-Property), I3 (SaveInFlight-Cleanup als Infra markiert).
- ⚠️ I4 (Props-Objekt/File-Split), I6 (Doppel-Submit), I7 (Zusatz-Feedback/„Hauptname") bewusst **nicht** vermerkt: KISS bei 2 Feldern / durch run-6-Eindeutigkeit backend-abgedeckt / für MVP unkritisch.

## Tooling-Härtung: `.stryker-tmp` (2026-07-07)

Auslöser: 100 falsche ESLint-Fehler aus liegengebliebenen Stryker-Sandboxes; last-session-Crash (ENOENT) + schwankende Scores (94–98 %) durch parallele Läufe.
- **F-A:** `.stryker-tmp/` in `.gitignore` + ESLint `globalIgnores` → keine Verfälschung/Commit-Risiko.
- **F-B:** `stryker-frontend.py` pre-cleant `.stryker-tmp` innerhalb des Locks → frische Sandbox, kein ENOENT durch Residue.
- **F-C:** `RunLock` atomar (`os.open O_CREAT|O_EXCL` statt read-then-write TOCTOU) + Regressionstest → echte Mutual Exclusion gegen Parallelläufe.
- Zuvor (2026-07-06): `qa-check._is_test_file` erkannte `.test.tsx` nicht → Test-Freigabe-Audit lief für Frontend-Runs leer; Regex + Konventions-Tests gefixt.

## Doku geschärft (je genau eine Stelle)

- **ADR-S100-1** (Autofokus-Race akzeptiert, Guard verworfen).
- **UX-Prinzip 3** um Regel „Sperren während Pending" ergänzt (normative Heimat für R2).
- **e2e-testing.md** „sichtbares Signal statt Proxy-Attribut" (Asterisk statt nur `required`).
- **ADR-S001-1** direkt korrigiert (nicht per Addendum): nannte „MUI v7", real ist **v9** (bewusster Upgrade S067). Version im Kopf/Entscheidung überarbeitet + knapper S067-Provenance-Pointer statt stehengelassenem Stale-Fakt (Anwendung von OBS-S100-1; Fund aus dem Nach-Sweep des alten Orchestrator-Logs).
- **UX-Prinzip 8** um den `formNoValidate`-Konflikt ergänzt (natives `<form>`+`required`+server-only-Validierung kappt Submit vor `onSubmit`; Fund aus der Subagent-Prozessverbesserung).
- **TD-S083-3 / AGENT_MEMORY korrigiert:** Der alte Orchestrator hatte einen Widerspruch fürs Abschluss vorgemerkt – AGENT_MEMORY behauptete, run-2's „Speichern-Button deaktiviert" behebe den Cold-Start-Race TD-S083-3. Falsch: `disabled={isPending}` gatet auf den *POST*-Pending-State, nicht auf das Settle des initialen GET. TD-S083-3 bleibt offen; Behebung/Trigger + AGENT_MEMORY-Roadmap entsprechend geschärft (Fund aus dem Nach-Sweep).
- **gherkin-workshop-Checkliste** geschärft: „Async-Zustände & Sperren während Pending" (alle Schließ-Kontrollen), „Feld-Initialisierung" um Rest-Zustand nach Abbrechen/Fehlschlag → schließt den Discovery-Blindfleck, der R1/R2 durchrutschen ließ.
- **TD-S077-1 / TD-S094-1** auf den offenen Rest reduziert (erledigte Teile entfernt, nicht als Changelog belassen).

## Spec-first: 3 neue run-2-Szenarien (Implementierung nächste Session)

Per Clustering-Algorithmus gehören sie in run-2's Cluster (Anlegen·Success·Frontend-only) → als `# @run-2`-Szenarien ins Feature-File, run-2 zeigt dadurch wieder offene Arbeit (dasselbe inkrementelle Muster wie bisher):
- **S1** „Abbrechen ist während des Speicherns deaktiviert" (@happy-path)
- **S2** „Dialog nicht per Escape schließbar während des Speicherns" (@happy-path)
- **S3** „kein Rest-Fehler nach Fehlschlag + Abbrechen + Reopen" (@edge-case)

S1+S2 sperren alle Schließ-Pfade während Pending → subsumieren den Datenverlust-Race (R2); S3 deckt R1.

## Offene Punkte

- **US-904 run-2-Rest (S1/S2/S3) implementieren** – nächster Produktions-Lauf.
- TD-S094-1 (Fokus-nach-Fehler) → mit run-4 „Einheit-Validierung".
- Commit dieser Session steht noch aus (im Anschluss an diesen Abschluss).

## Learnings

- **LL-S100-1** – Parallele/gekillte Stryker-Läufe korrumpierten `.stryker-tmp` (s. lessons_learned.md).
- **LL-S100-2** – Review fand reale, aber szenariolose Bugs → gherkin-workshop-Discovery-Blindfleck (s. lessons_learned.md).
- **LL-S100-3** – `_is_test_file` blind für `.test.tsx`, verdeckt durch Fixtures mit nicht-existenter Konvention (s. lessons_learned.md).

## Beobachtungen

- **OBS-S100-1** – Zustandsdokumente sammeln Erledigtes / Verweise auf gelöschte Artefakte (Quelle: User).
- **OBS-S100-2** – Agent-Auffälligkeiten erodieren User-Vertrauen → mehr Kontrolle → Ermüdung (Verstärker über alle Auffälligkeiten; Quelle: User).
- **OBS-S100-3** – `qa-check` gibt bei <100 % nur den Score aus, nicht die Survivor-Zeilen (Zweitlauf nötig; Quelle: Orchestrator, aus dem Nach-Sweep des alten Logs geborgen).

## Subagenten

- **frontend-component** (2026-07-06) – run-2-Implementierung; guter empirischer Pushback (Guard-Beleg gegen komplette Entfernung, mit real reproduziertem Testbruch). Wiederkehrende Message-Crossing-Probleme (Idle-Heartbeats statt inhaltlicher Antworten).
  - **Ungefragtes Gold-Plating:** baute den Fokus-Steal-Guard + einen dafür geschriebenen Test, obwohl kein Szenario ihn forderte – ohne vorher zu fragen. Vom Orchestrator-Check gefangen → Guard + Test wieder entfernt (führte zu ADR-S100-1). Das bestehende Gate griff; kein neuer LL, aber als wiederkehrende Subagent-Scope-Creep-Tendenz festgehalten.
  - **Subagent-Prozessverbesserung (selbst gemeldet):** (a) `required` + natives `<form>` + server-only-Validierung → HTML5-Constraint-Validation blockiert den Submit, *bevor* `onSubmit` feuert → die @US-904-error-Szenarien erreichen den Server nie; Fix war `formNoValidate` am Submit-Button. Ableitbar aus UX-Guideline/ADR-S090-1, aber nicht im Auftrag benannt → erst im GREEN entdeckt. (b) MUI-Slots-Typing für `component:'form'` bleibt auf `HTMLDivElement` (nicht `HTMLFormElement`) → kostete einen Diagnose-Zyklus. Beides code-eingebettetes Wissen (kein LL); der `formNoValidate`-Konflikt ist auf User-Go als knappe Notiz in **UX-Guideline Prinzip 8** (Zeile „Enter sendet ab") aufgenommen.
- **4 Review-Auditoren** (2026-07-07) – context-frei; functional-correctness fand die zwei realen Bugs, ux-ui die Prinzip-8-Lücke.
