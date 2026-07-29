# Session 110 – 2026-07-29

**Phase:** SKELETON
**Schwerpunkt:** US-904 run-9 „Löschen·Pending" (Frontend-only, Singleton) – ein Szenario, plus Behebung von TD-S108-3.

---

## Implementiert

**Szenario:** „Löschen-Button ist während des Löschens deaktiviert" (`@US-904-happy-path`).

`useDeleteIngredientWithUndo` führt einen neuen State `deletingId: string | null`, den
`requestDelete` synchron vor dem Mutation-Aufruf setzt und der `onSuccess`-Callback des DELETE
wieder auf `null` zurücksetzt. `IngredientList` erhält ihn als Prop; der Löschen-`IconButton`
trägt `disabled={ingredient.id === deletingId}`.

Bewusst **zeilenbezogen** statt global gesperrt. Neben dem Wortlaut des Szenarios („der
Löschen-Button für ,Mehl'") gab es dafür einen zwingenden Grund: der run-8-Test
`US904_EdgeCase_TwoDeletes_UndoRestoresOnlyTheLatest` klickt „Mehl löschen" und danach
„Zucker löschen", potenziell während der erste DELETE noch offen ist – globales Sperren hätte ihn
gebrochen.

`useResultMutation` blieb unverändert: `isPending` existierte bereits seit run-2 (ADR-S083-2
Addendum) und musste nicht erweitert werden. Der Reset läuft trotzdem über einen eigenen State
statt über `isPending`, weil `deleted` nach Abschluss noch ~6 s für den Undo-Toast gesetzt bleibt
und damit kein brauchbares Pending-Signal ist.

## Technische Schuld

- **TD-S108-3 behoben** – der Given-Teil der drei Löschen-Component-Tests wanderte in
  `renderWithDeletableMehl()`. Der Klick (When) blieb bewusst inline: der erste Test hat zwischen
  Given und When eine Vorbedingungs-Assertion, die den bereits gerenderten DOM braucht und sich
  deshalb nicht um den Helper herum anordnen lässt. Damit weicht die Umsetzung vom Wortlaut des
  TD-Eintrags („Given+When-Setup") ab – die reale Duplikation (MSW-Handler, Render, Warten) ist
  vollständig beseitigt.
- **TD-S110-1 neu** – `deletingId`-Lebenszyklus deckt nur den Erfolgspfad des Einzel-Löschens ab
  (kein Reset im Fehler- und im Restore-Pfad, Skalar statt Menge).
- **TD-S108-2 ergänzt** um einen zweiten, früheren Fokusverlust-Trigger: der Button verliert den
  Fokus schon beim `disabled`-Werden, nicht erst beim Unmount.
- **TD-S108-1** verweist jetzt auf TD-S110-1; **TD-S108-4**s Trigger-Verweis auf run-9 war nach
  diesem Lauf stale und wurde korrigiert.

## Unterbrechung durch WSL-Absturz

Mitten im inneren Loop beendete ein WSL-Absturz Orchestrator und Schicht-Subagent gleichzeitig.
Nach dem Neustart lagen fertiger Produktionscode und der durchgeführte Refactor im Working Tree,
aber kein Verifikations-Hash und keine Aussage über offene Schritte. Die Rekonstruktion gelang,
weil der Test-Freigabe-Anker als git-Blob (`git hash-object -w`) außerhalb des Agentenkontexts
persistiert war: der Refactor-Diff ließ sich nachträglich mechanisch dagegen auditieren und
erwies sich als reine Setup-Verschiebung ohne Assertion-Änderung. Verifikation (Stryker,
Testläufe, `qa-check.py`) übernahm danach der Orchestrator selbst – ein im Skill nicht
beschriebener Weg (→ `OBS-S110-2`).

## Review

Vier Auditoren, eine Runde, **0 ❌**. Sechs ⚠️ konsolidiert; eines davon (Vorbedingungs-Assertion)
wurde nach User-Entscheid umgesetzt, die übrigen als technische Schuld erfasst oder bewusst
verworfen (kein Ladeindikator – konsistent mit run-2, kein Szenario fordert einen).

Zwei Agenten-Begründungen hielten der Prüfung nicht stand und wurden korrigiert statt übernommen:

- `functional-correctness-auditor` schloss, die `deletingId`-Nebenwirkung bliebe „nach dem
  TD-S108-1-Fix vermutlich bestehen". Tatsächlich schließt der dort dokumentierte Fix das
  Zeitfenster vollständig, weil „Rückgängig" dann erst klickbar ist, wenn `deletingId` bereits
  `null` ist – TD-S108-1 sagt das selbst.
- `ux-ui-auditor` empfahl, `deletingId` sofort auf ein `Set` umzustellen. Abgelehnt: das erzeugt
  einen von keinem Szenario ausgeübten Zweig → Stryker-Survivor → Suppression außerhalb des
  treibenden Szenarios, genau die Konstellation, die ADR-S083-2 vermeidet.

Ein Auditor-Befund wurde vor der Übernahme empirisch geprüft (Mutant eingesetzt, Fehlerort
beobachtet) und bestätigte sich – siehe `LL-S110-1`.

## Learnings & Beobachtungen

- `LL-S110-1` – Test-Batch mit unter dem Mutanten vakuöser Hauptassertion freigegeben.
  → `docs/kaizen/lessons_learned.md`
- `OBS-S110-1` – „Done"-Erkennung eines Laufs hängt am Test-Kommentar statt am grünen Test.
  → `docs/kaizen/observations.md`
- `OBS-S110-2` – `implementing-scenario` Schritt 4 hat keinen Weg, wenn der Schicht-Subagent nicht
  zurückkehrt. → `docs/kaizen/observations.md`

## Qualität

Stryker Frontend 100,0 % (77 valide Mutanten), 30 Component-Tests grün, 34 E2E-Tests grün,
ESLint 0 Errors (2 vorbestehende `max-lines-per-function`-Warnings, von diesem Lauf nicht
verursacht – beide betroffenen Funktionen haben keine zusätzliche Zeile bekommen).
