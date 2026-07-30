# Session 111 – 2026-07-29/30

**Phase:** SKELETON
**Schwerpunkt:** US-904 run-11 „Reaktivierung" (Full-Stack, 5 Szenarien) inkl. Review-Nachbesserung.

Die Session wurde am 29.07. um 16:41 vom Session-Limit unterbrochen, während beide
Nachbesserungs-Subagenten liefen, und am 30.07. fortgesetzt und abgeschlossen.

---

## Implementiert

**Fünf Szenarien** (`@US-904-edge-case` ×3, `@US-904-happy-path`, `@US-904-error`): Anlegen einer
Zutat, deren Name auf eine soft-deleted Zeile trifft, reaktiviert diese transparent – mit
Übernahme der neu eingegebenen Einheit und Schreibweise; dazu die beiden Parallelfälle
(fremder Restore mit denselben bzw. mit abweichenden Daten).

**Backend.** `POST /{id}/restore` bekam einen Pflicht-Body `{ name, defaultUnit }` und antwortet
mit `200` + DTO statt `204` (ADR-S111-1, überholt ADR-S108-2). Über die Antwort entscheidet ein
**exakt-ordinaler Wertevergleich**, nicht der Zeilenzustand: identische Werte → `200` ohne
Schreibvorgang, abweichende → `409 ingredient_already_active` mit dem gespeicherten Stand im Body.
Die POST-Konfliktverzweigung läuft über einen Lookup **nach** der Unique-Violation statt über
einen Vorab-Check (ADR-S111-2). `CreateIngredientDto` wurde zu `IngredientValuesDto` umbenannt –
derselbe DTO trägt jetzt beide Schreibpfade.

**Frontend.** `createIngredient` liefert im Ok-Pfad zwei unterscheidbare Erfolgsfälle (`Saved`,
`ReactivationConflict`); der Konflikt ist bewusst **kein** `Err`, weil der Vorgang fachlich
gelingt – die Zutat existiert danach. Der Dialog schließt daher wie im Erfolgsfall, und eine
eigene Snackbar nennt den tatsächlich gespeicherten Stand (ADR-S111-3). `useResultMutation`s
`onSuccess` reicht dafür seit diesem Lauf den Erfolgswert durch (Addendum zu ADR-S083-2).

## Review und Nachbesserung

Vier Auditoren, eine Runde, **0 ❌ Must-Fix**, 13 ⚠️ konsolidiert. Nach User-Entscheid wurden
**alle** umgesetzt, verteilt auf zwei Schicht-Subagenten (F1–F6 Frontend, B1–B4 Backend).

Zwei Auditor-Positionen kollidierten direkt: Der `code-quality-auditor` wollte die
`autoHideDuration` beider Toasts in eine gemeinsame Konstante ziehen, der `ux-ui-auditor` wollte
sie gerade entkoppeln. Entschieden wurde für die Entkopplung (6 s / 10 s) – die ursprünglich in
ADR-S111-3 festgelegte Gleichheit war ein Konsistenz-Default ohne Blick auf die Textlänge; die
Konflikt-Meldung ist rund zehnmal so lang, und MUIs Pause-bei-Hover greift auf Touch nicht. Dass
die Dauern **absichtlich** verschieden sind, steht seither in der ADR, damit es niemand
„aufräumt".

Fachlich am folgenreichsten war `FC-11-1`: Der Undo-Toast einer vorangegangenen Löschung überlebte
die Reaktivierung derselben Zeile und behauptete weiter „gelöscht" – ein Klick auf „Rückgängig"
lief in den 409-Zweig, den der Client als Erfolg wertet, und verpuffte ohne jede Rückmeldung. Vor
run-11 konnte der Toast gar nicht veralten, weil eine soft-deleted Zeile nur durch den Undo selbst
zurückkam.

Der `DbUpdateConcurrencyException`-Zweig im Restore trägt bewusst **keinen** Test, sondern eine
begründete Stryker-Suppression (Muster ADR-S041-9): Der Endpoint nimmt kein If-Match, lesendes
SELECT und schreibendes UPDATE liegen im selben Request, ein echter Race wäre interleaving-
abhängig und damit flaky.

## Unterbrechung durch das Session-Limit

Das Limit beendete Orchestrator und **beide** Fix-Subagenten. Der Backend-Agent war fertig und
vollständig grün, kam aber nicht mehr zum Absenden seines Reports; der Frontend-Agent stand im
laufenden `qa-check`. Der fortsetzende Orchestrator hat beide Verifikationen selbst nachgefahren
und dabei einen Code-Kommentar gefunden, der auf ein nie geschriebenes ADR-Addendum verwies
(→ `LL-S111-1`, `OBS-S110-2`). Die freigegebenen Test-Dateien ließen sich mechanisch prüfen: beide
git-Blob-Hashes waren unverändert, nach der Freigabe wurde also keine Assertion mehr angefasst.

## Technische Schuld

- **TD-S090-3** – DTO-Name nachgezogen (`IngredientValuesDto`); Reichweite verdoppelt, weil der
  DTO jetzt von zwei Endpoints gebunden wird.
- **TD-S108-1(b)** – teilweise überholt: Der Restore wertet den `409` aus, `404`/`422` gehen
  weiterhin als Erfolg durch; seit run-11 kann der Endpoint überhaupt erst `422` antworten.
- **TD-S108-4** – um den zweiten Toast (10 s) erweitert, Trigger neu gefasst (→ `LL-S111-2`).
- **TD-S110-1** – neuer Punkt (d): kein Pending-Guard am „Rückgängig"-Button; im Review bewusst
  nicht mitbehoben, weil eine Button-Sperre ein eigenes Gherkin-Szenario braucht.

## Learnings & Beobachtungen

- `LL-S111-1` – Doku-Pflicht ausschließlich über den Subagenten-Return transportiert, Return fiel
  aus. → `docs/kaizen/lessons_learned.md`
- `LL-S111-2` – Rein reaktiver tech-debt-Trigger griff nicht, obwohl das Auslöse-Ereignis eintrat.
  → `docs/kaizen/lessons_learned.md`
- `LL-S111-3` – Assertions gegen einen Survivor geschrieben, den keine Komponenten-Assertion töten
  kann. → `docs/kaizen/lessons_learned.md`
- `OBS-S111-1` – `gherkin-workshop` fand die Konflikt-Variante eines Nebenläufigkeits-Szenarios
  nicht. → `docs/kaizen/observations.md`
- `OBS-S111-2` – ADR-Übergabe an Schicht-Subagenten skaliert nicht mehr mit der Zahl der ADRs.
  → `docs/kaizen/observations.md`
- `OBS-S111-3` – Stryker-Wrapper meldet Survivors ohne Block-Ende und ohne Coverage-Angabe.
  → `docs/kaizen/observations.md`
- `OBS-S111-4` – Bash-Hook blockt erlaubte Befehle, sobald sie verkettet, umgeleitet oder als
  Heredoc formuliert sind. → `docs/kaizen/observations.md`
- `OBS-S110-2` um den zweiten Vorfall ergänzt; `OBS-S085-3` um die Messlücke für Klasse 3.

## Qualität

Stryker Backend 100,0 % (84 valide Mutanten, eine begründete Suppression), Stryker Frontend
100,0 % (97 valide Mutanten), 39 E2E-Tests grün, ESLint 0 Errors, Typecheck sauber. Beide
Verifikations-Hashes vom Orchestrator selbst erzeugt (`e51dff8f03671036` Backend,
`3a7c6a04c3be397b` Frontend).
