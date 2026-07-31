# Session 112 – 2026-07-31

**Phase:** SKELETON · **Story:** US-904 (alle Läufe implementiert)

Kein Produktionscode-Feature. Schwerpunkt war der vollständige Durchgang durch `docs/tech-debt.md`, aufgeteilt in fünf thematische Batches. Der Durchgang deckte deutlich mehr auf als geplant – ein Drittel der Session ging in Folgeentscheidungen, die aus einzelnen Einträgen entstanden.

---

## Tech-Debt-Durchgang

Alle 19 Ursprungs-Einträge bearbeitet. Jeder wurde am Code verifiziert statt aus der Beschreibung übernommen.

- **Gelöscht:** TD-S090-1 – die geforderte collect-all-Validierung war vollständig implementiert (`IngredientsEndpoints.ToDomain`).
- **Teil-Erledigtes herausgeschrieben:** TD-S083-4 (beide Max-Längen im Code), TD-S083-1 (POST-Pfad), sowie sämtliche Delta-Erzählungen („teilweise überholt durch run-11" u. ä.) – `tech-debt.md` ist ein Zustandsdokument.
- **Neu:** TD-S112-1 (Konfigurations-Parität E2E↔Produktion), TD-S112-2 (Observability ohne Umsetzung).
- **Sachliche Korrekturen:** TD-S089-1 zeigte auf einen MTP-Stack, den es nicht mehr gibt (aufgelöst ist 1.9.1, nicht 2.x). TD-S090-2 beschrieb einen Ort, aus dem der Code längst weggewandert war, und berief sich auf eine Guideline-Pflicht, die nur für Komponenten gilt. TD-S083-1 überschätzte die Wirkung (ein Fehler-Body wird geparst, aber nicht gecacht).
- **Alle Phantom-Trigger beseitigt:** Auslöser wie „eigene UX-Foundation-Aufgabe", „erste Härtungs-Aufgabe", „mit run-4" oder „eigenes Mini-Szenario" sind ersetzt; jeder Eintrag hat jetzt eine Bedingung, die eintreten kann, oder ist über `AGENT_MEMORY` terminiert.

Der Auftrag „feature-spezifisch oder allgemein?" ergab: **alle** Einträge sind allgemein. Feature-spezifisch war allein die Herkunft.

## Entscheidungen (ADR-S112-1 bis -5)

- **ADR-S112-1** – `UseExceptionHandler` wird unbedingt registriert; damit hat der Fehlerpfad keinen Umgebungs-Zweig mehr und E2E übt denselben Pfad aus wie Produktion.
- **ADR-S112-2** – E2E erbt die Produktions-Konfiguration; Umgebungsnamen werden beim Start gegen eine Allow-Liste geprüft, die zugleich die Umgebungs-Aufzählung im Test speist.
- **ADR-S112-3** – E2E fälscht keine Backend-Antworten; Fehlerzustände werden real ausgelöst (Fault-Endpoint, out-of-band scharfgestellt).
- **ADR-S112-4** – Domänenregeln setzt das Backend durch, Frontend-Brands sind nominal; Ausnahme für Bereiche, die Zustandsänderungen ohne erreichbares Backend annehmen.
- **ADR-S112-5** – Querschnitts-Verhalten wird durch geteilte Implementierung garantiert, nicht durch wiederholte Szenarien; vier Schichten plus Migrationsreihenfolge.

Bei ADR-S112-5 wurde die Quellenlage geprüft: *Shared Examples* (rspec.info) und *architectural fitness function* (Thoughtworks Radar) sind belegt; die Verwendung von Page Objects zur seitenübergreifenden Testwiederverwendung steht **nicht** bei Fowler und ist eine Ableitung dieses Projekts; die Bezeichnung „Contract Test" wurde verworfen, weil Fowler damit etwas anderes meint.

## Guideline- und Prozess-Änderungen

- `coding-guideline-typescript.md`: §2 korrigiert (nominale Brands statt validierender Factory – das alte Beispiel hätte in Regel-Duplikation geführt), §4c neu (Validierung, mit Ausnahme für offline-schreibfähige Bereiche).
- `nfr.md`: Security-Anforderung „Fehlerantworten ohne technische Details" (ab MVP) und neue Observability-Sektion.
- `e2e-testing.md`: Sektion „E2E-Treue: Konfiguration & Mocking".
- `review-code`-Skill: Scope-Prüfung je Finding – trivial → sofort, sonst Phasenfrage. Auslöser war die Erkenntnis, dass eine aus einem Finding gebaute Pending-Sperre vier neue Schuld-Punkte erzeugt hatte.
- `features/interaction.feature` neu angelegt (querschnittliches Interaktionsverhalten, drei Szenarien, post-MVP).

## Code

- `react-router` 7.18.2 → 8.3.0 (Advisory-Behebung lag außerhalb `^7`, also Major-Bump). Kein Code-Change nötig; Build, 40 Vitest- und 39 Playwright-Tests grün.
- `Server/Program.cs`: Kommentar an der Stelle des fehlenden Exception-Handlers, mit an der MS-Doku verifiziertem Framework-Verhalten.

## Requirements-Korrekturen

`docs/stories/szenario_9_datenpflege.md` – US-904 hatte Tags unter den SKELETON-Akzeptanzkriterien, obwohl `skeleton-spec.md` sie nie enthielt und nichts davon implementiert ist. Stufen neu geordnet: SKELETON (Anlegen/Auflisten/Löschen), MVP (Bearbeiten + Modifier), V1 (Tags). Die MVP-Zuordnung der Modifier ist durch US-301 gedeckt, die „Modifizierer-Trennschärfe" als eigenes Akzeptanzkriterium führt.

## Gefundene Doku-Defekte

- `adr.md`: Ein `**Begründung:**`-Absatz von ADR-S067-1 stand seit Commit `f1ff899` (S083) mitten in ADR-S083-2 – beim Einfügen der neuen ADR war der Anker danebengegangen und hatte den bestehenden Eintrag samt Trenner aufgespalten. Wieder zusammengeführt.
- Inhaltsverzeichnisse: `e2e-testing.md` und die TypeScript-Guideline listeten neu geschriebene Abschnitte nicht (§4b fehlte schon länger); die §2-Zeile beschrieb nach der Guideline-Änderung noch den alten Stand. Ergänzt bzw. korrigiert.

## Learnings & Beobachtungen

- **LL-S112-1** – Der in Batch A diagnostizierte Trigger-Defekt wurde in Batch B selbst reproduziert. → `lessons_learned.md`
- **LL-S112-2** – Dreimal eine Struktur geändert, ohne vorher deren dokumentierte Regeln zu lesen. → `lessons_learned.md`
- **OBS-S112-1 bis -8** – Feld mit zwei Bedeutungen, wirkungsloses Prioritätsfeld, kein Weg für Infra-Arbeit ohne Szenario, Lint-Wrapper rot bei null Errors, Allow-Liste ohne Dependency-Bump, Regelverletzungen als aufschiebbare Schuld geführt, nicht prüfbare Prosa-Verweise, lösungsfreie OBS-Erfassung teurer als ihr Ziel. → `observations.md`
- **OBS-S108-2 und OBS-S106-2 erweitert** – die Workshop-Checkliste scheitert nicht am Inhalt, sondern an ihrem Geltungsbereich („die ein Formular oder einen Dialog hat"); und es fehlt eine Regel, wann ein Verhalten querschnittlich ist. → `observations.md`
