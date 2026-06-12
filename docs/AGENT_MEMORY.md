# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **4-KB-Limit temporär AUFGEHOBEN (S083):** war 3–4 Sessions in Folge schwer zu halten, ohne Notizen unverständlich zu kürzen → Umstrukturierung des Gedächtnissystems ist Retro-Thema (`countermeasures.md`, OFFEN). Bis dahin: **Notizen selbsterklärend halten hat Vorrang vor Kürze** – nicht brutal trimmen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`)
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, process)

**Letzte Aktualisierung:** 2026-06-12 (Session 083 – US-904 „Zutat anlegen" Full-Stack end-to-end: Frontend+Backend+erste EF-Migration, beide 100 % Stryker, E2E grün; ADRs S083-1/-2; ETag bewusst verschoben; Details: session_083)
**Phase:** SKELETON 🔄 – US-904 Szenarien-Fortschritt s. „Nächste Prioritäten"

---

## Nächste Prioritäten (Reihenfolge bindend; keine Nummerierung verwenden, sondern nur Anstriche)

- **ETag-Querschnitts-Zyklus (User-priorisiert, ZUERST):** Frontend-Conditional-Layer (einmalig: `If-None-Match`/ETag/304→Cache) + Backend-Collection-ETag (`GET /api/ingredients`, SHA-256-Content-Hash, ggf. Middleware; ADR-S058-1/-3, S000-12). **Wichtig:** react-query macht von Haus aus KEINE HTTP-Conditional-Requests – ohne die Frontend-Schicht hat das Backend-ETag keinen Konsumenten und damit keinen Nutzen (der 304-Spareffekt entsteht nur, wenn der Client `If-None-Match` sendet). Die Frontend-Schicht ist also Pflicht, nicht optional. Getrieben durch Service-Client- (MSW) + Backend-Integrationstests – **KEIN E2E** (Caching-Concern; Begründung: ADR-S041-5-Addendum). **Offene Design-Entscheidung im Zyklus:** Collection-ETag als EINE generische Content-Hash-Middleware (hasht jede GET-Collection-Response → gilt sofort überall; passt zu S058-3 „Content-Hash") **vs.** per-Endpoint inkrementell (wie S000-12 „pro Endpoint beim ersten echten GET" nahelegt). S058-3 und S000-12 wirken dadurch widersprüchlich → im Zyklus klären, dann S000-12-Wortlaut entsprechend präzisieren.

- **Danach US-904 weiter** (`features/ingredients.feature`-Reihenfolge): zuerst **@US-904-error** (erzwingt `NonEmptyTrimmedString`-Validierung → ADR-S000-4-Suppression entfällt), dann sortiert/Löschen/Undo/„Speichern-Button deaktiviert" (pending-State, behebt Cold-Start-Race). `user.type`/`fireEvent.click` (TS-Guideline).

- **gherkin-workshop US-904 V1:** Separater Schritt vor V1-Implementierung: Feature-Datei und Szenarien ergänzen, die erst in V1 umgesetzt werden (Funktionalität die über MVP hinausgeht: Update einer Zutat + Tags für Zutaten).

- **Deep-Link-Anforderung klären:** Vor US-602 (Rezept-Detailansicht) – welche Entitäten, Hintergründe, Architektur-Implikationen.

- **Visuelle Konsistenz-Guideline:** `docs/guidelines/coding-guideline-ux.md` um Spacing/Hierarchie/Farbe erweitern, sobald >3 Komponenten dieselben visuellen Entscheidungen treffen.

- **Offene Maßnahmen** (`docs/kaizen/countermeasures.md`, OFFEN): HOCH→CM-Härtung (closing-session-Prüfung weich); **qa-check.py härten** (still veralteter Hash bei DLL-Lock/Build-Fehler → harter Lauf-Fehler + Lock-Guard, S083).

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |
| Frontend Hooks | `useResultMutation.onSuccess` feuert auch bei `Err` (`Promise.resolve(ResultAsync)` wirft nicht) → vor Error-Szenario auf `result.match(onSuccess,onError)` umstellen; `throwOnError` entfernt + kein `r.ok`-Check in `ingredientsApi` (ADR-S083-2). | Mittel – Error-Szenario |
| Frontend UX (projektweit) | Kein `ThemeProvider`/`CssBaseline` → Touch-Targets <44px, kein MD3-Type-Scale. Eigene UX-Foundation-Aufgabe. | Mittel |
| Frontend Komponente | Dialog ohne `onClose` (kein Esc/Backdrop) → Kandidat für eigenes Mini-Szenario. `isDialogOpen` + `closeDialog` synct 3 `useState`-Slices manuell → bei Speichern/Validierung auf Discriminated Union. UX-Politur: `<p>`→`Typography`, TextFields `fullWidth`/`margin`, Layout-Container/Heading. | Niedrig |
| Frontend | Cold-Start-Race: feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET). Symptom: gerade angelegte Zutat erscheint nicht in der Liste. Tritt nur bei kaltem Server / langsamem erstem GET auf (warm: unkritisch). Behebung mit pending-State-Szenario („Speichern-Button deaktiviert"), das den Save bis zum Settle der Query sperrt. | Niedrig |
| Validierung (FE+BE) | Keine Max-Length auf Name/DefaultUnit (Kestrel-Body-Limit deckelt); keine Frontend-Branded-Types/`makeIngredientName`-Factory → beides Validierungs-Szenario. | Niedrig |
| Frontend Deps | `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert; entfällt bei Stryker-Major-Bump. | Niedrig |
| E2E-Test | `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt (durch „Zutat anlegen" jetzt verschärft) | Niedrig |

---

## Offene Fragen / geparkte Diskussionen (mit User)

- **ADR vs. technische Schuld – Taxonomie klären:** User-Sicht: dauerhafte, code-unabhängige Entscheidung = ADR; Doku konkreter Code-Ausnahmen = Tech-Debt. **Auslöser:** Suppression-ADRs (S000-3/S000-4) pinnen `// Stryker disable`-Kommentare auf **konkrete Code-Zeilen** – und S000-4 beschrieb Code, der diese Session erst (neu) geschrieben wurde; solche code-spezifischen Ausnahmen sind eher Tech-Debt als dauerhafte Architekturentscheidung. Prüfen: ADR-S000-3/S000-4 (und ggf. S083-1/-2) ggf. in einen Tech-Debt-/Suppression-Katalog auslagern; Konsequenzen für die ADR-Konvention.
- **Getypte IDs?** `IngredientId` statt rohes `Guid` – Inkonsistenz zu „immer Value Objects" (name/unit gekapselt, Id nicht). ADR-S030-1 ggf. neu formulieren wenn getypte IDs gewünscht. Merksatz: kanonische Guideline-Beispiele sind Beispiele, kein Dogma.
