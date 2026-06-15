# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **4-KB-Limit temporär AUFGEHOBEN (S083):** war 3–4 Sessions in Folge schwer zu halten, ohne Notizen unverständlich zu kürzen → Umstrukturierung des Gedächtnissystems ist Retro-Thema (`countermeasures.md`, OFFEN). Bis dahin: **Notizen selbsterklärend halten hat Vorrang vor Kürze** – nicht brutal trimmen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process)

**Letzte Aktualisierung:** 2026-06-15 (Session 084 – ETag-Querschnitts-Zyklus: Frontend-Conditional-Layer + Backend-ETag-Middleware, beide 100 % Stryker; ADRs S084-1..4; Poka-Yoke gegen stale E2E-Backend)
**Phase:** SKELETON 🔄 – US-904 Szenarien-Fortschritt s. „Nächste Prioritäten"

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **Retro fällig (Jenga-Score ≤ 0):** Nächste Session mit Skill `kaizen` beginnen.

- **US-904 weiter** (`features/ingredients.feature`-Reihenfolge): zuerst **@US-904-error** (erzwingt `NonEmptyTrimmedString`-Validierung → ADR-S000-4-Suppression entfällt), dann **sortiert** (führt `OrderBy(name)` ein → **aktiviert den in S084 gebauten ETag real**, s. Tech-Debt; Stryker-killbar weil Insertion-Order ≠ alphabetisch)/Löschen/Undo/„Speichern-Button deaktiviert" (pending-State, behebt Cold-Start-Race). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Offene Maßnahmen** (`docs/kaizen/countermeasures.md`, OFFEN): HOCH→CM-Härtung (closing-session-Prüfung weich); **qa-check.py härten** (still veralteter Hash bei DLL-Lock/Build-Fehler → harter Lauf-Fehler + Lock-Guard, S083).

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |
| Frontend Hooks | `useResultMutation.onSuccess` feuert auch bei `Err` (`Promise.resolve(ResultAsync)` wirft nicht) → vor Error-Szenario auf `result.match(onSuccess,onError)` umstellen; `throwOnError` entfernt + kein `r.ok`-Check in `ingredientsApi` (ADR-S083-2). **Erweitert (S084):** `conditionalGet.ts` setzt das Muster fort – kein `response.ok`-Check, d.h. ein 4xx/5xx-Body würde als Erfolg geparst+gecacht; zusätzlich `cached!` im 304-Pfad (YAGNI, 304 ohne Cache-Eintrag würfe). Fix gehört in dieselbe Error-Handling-Umstellung (konsistent für GET+POST, ApiError-aus-Status). | Mittel – Error-Szenario |
| Frontend UX (projektweit) | Kein `ThemeProvider`/`CssBaseline` → Touch-Targets <44px, kein MD3-Type-Scale. Eigene UX-Foundation-Aufgabe. | Mittel |
| Frontend Komponente | Dialog ohne `onClose` (kein Esc/Backdrop) → Kandidat für eigenes Mini-Szenario. `isDialogOpen` + `closeDialog` synct 3 `useState`-Slices manuell → bei Speichern/Validierung auf Discriminated Union. UX-Politur: `<p>`→`Typography`, TextFields `fullWidth`/`margin`, Layout-Container/Heading. | Niedrig |
| Frontend | Cold-Start-Race: feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET). Symptom: gerade angelegte Zutat erscheint nicht in der Liste. Tritt nur bei kaltem Server / langsamem erstem GET auf (warm: unkritisch). Behebung mit pending-State-Szenario („Speichern-Button deaktiviert"), das den Save bis zum Settle der Query sperrt. | Niedrig |
| Validierung (FE+BE) | Keine Max-Length auf Name/DefaultUnit (Kestrel-Body-Limit deckelt); keine Frontend-Branded-Types/`makeIngredientName`-Factory → beides Validierungs-Szenario. | Niedrig |
| Frontend Deps | `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert; entfällt bei Stryker-Major-Bump. | Niedrig |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt (durch „Zutat anlegen" jetzt verschärft) | Niedrig |
| HTTP/ETag-Middleware (BE) | `ETagMiddleware` puffert **jede** GET-Response komplett in einen `MemoryStream` (+`ToArray()`-Kopie) → (a) DoS-/Speicher-Risiko sobald große/paginierungsfreie Collections oder File-/Image-GETs dazukommen (Buffering+Hash zwingt Nicht-Streaming; Größen-Cap oder Routen-/Content-Type-Whitelist nötig); (b) `next()` ist nicht in try/finally → bei Endpoint-Exception wird `Response.Body` nicht auf den Original-Stream zurückgesetzt (heute folgenlos – keine Error-Handling-Middleware; scharf sobald eine davorkommt); (c) 304 setzt kein `Cache-Control: private`/`Vary` → ab MVP-Auth + Reverse-Proxy Cross-User-Leak über Shared-Caches. Alle drei aufgeschoben (jetzt: Survivor-/Scope-frei nicht umsetzbar). | Niedrig jetzt / Hoch vor File-Serving bzw. Auth |
| HTTP/ETag (BE) | `GET /api/ingredients` ohne `OrderBy` → Collection-Content-Hash-ETag (ADR-S084-1/-2) ist auf Postgres nicht stabil (undefinierte Heap-Order) → `If-None-Match` matcht nie → 304 feuert nie, Caching wirkungslos (Daten bleiben korrekt; Effektivitäts-, kein Korrektheits-Bug). Tests grün nur wegen EF-InMemory-Insertion-Order. Behebung: alphabetisches Sortier-Szenario (@US-904) führt `OrderBy(name)` Stryker-killbar ein. Reines `OrderBy(id)` jetzt wäre un-killbar (Suppression). | Mittel – der gerade gebaute ETag ist bis dahin nutzlos; SKELETON nicht deployt |

---

## Offene Fragen / geparkte Diskussionen (mit User)

- **ADR vs. technische Schuld – Taxonomie klären:** User-Sicht: dauerhafte, code-unabhängige Entscheidung = ADR; Doku konkreter Code-Ausnahmen = Tech-Debt. **Auslöser:** Suppression-ADRs (S000-3/S000-4) pinnen `// Stryker disable`-Kommentare auf **konkrete Code-Zeilen** – und S000-4 beschrieb Code, der diese Session erst (neu) geschrieben wurde; solche code-spezifischen Ausnahmen sind eher Tech-Debt als dauerhafte Architekturentscheidung. Prüfen: ADR-S000-3/S000-4 (und ggf. S083-1/-2) ggf. in einen Tech-Debt-/Suppression-Katalog auslagern; Konsequenzen für die ADR-Konvention.
- **Getypte IDs?** `IngredientId` statt rohes `Guid` – Inkonsistenz zu „immer Value Objects" (name/unit gekapselt, Id nicht). ADR-S030-1 ggf. neu formulieren wenn getypte IDs gewünscht. Merksatz: kanonische Guideline-Beispiele sind Beispiele, kein Dogma.
