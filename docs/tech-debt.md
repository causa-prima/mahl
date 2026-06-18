# Technische Schuld

<!--
wann-lesen: Wenn der zu bearbeitende Code einen der Bereiche unten berührt (z.B. Architektur-Check
            in implementing-scenario) sowie beim Session-Abschluss (closing-session, nfr.md).
wann-schreiben: Sobald eine bewusst aufgeschobene Schuld entsteht (⚠️-Finding nicht sofort gefixt,
            bewusste Vereinfachung, vertagte Härtung).

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen (kein Umsortieren).
            Priorität ist ein Feld pro Eintrag (Triage/Filter), nicht die Sortierachse.

Eintrag-Format:
  ## TD-S<NNN>-<n> — <Bereich/Kurztitel>
  **Priorität:** Hoch | Mittel | Niedrig  (ggf. + ab wann relevant)
  **Problem:** <was ist die Schuld>
  **Behebung/Trigger:** <geplante Behebung oder auslösende Bedingung>

  ID: TD-S<NNN>-<n> – 3-stellige Session (Ursprung), laufende Nummer innerhalb der Session.
-->

## TD-S044-1 — STJ/Deserialisierung
**Priorität:** Hoch – erst ab US-602 relevant
**Problem:** 400 vs. 500 bei ungültigem URI; STJ via `OriginalString` unverifiziert.
**Behebung/Trigger:** Mit US-602 (URI-Felder) verifizieren und 400 statt 500 erzwingen.

---

## TD-S077-1 — Frontend Komponente: Dialog ohne `onClose`, manuelles State-Sync
**Priorität:** Niedrig
**Problem:** Dialog ohne `onClose` (kein Esc/Backdrop). `isDialogOpen` + `closeDialog` synct 3 `useState`-Slices manuell. UX-Politur offen: `<p>`→`Typography`, TextFields `fullWidth`/`margin`, Layout-Container/Heading.
**Behebung/Trigger:** Eigenes Mini-Szenario; bei Speichern/Validierung auf Discriminated Union umstellen.

---

## TD-S080-1 — Frontend Deps: `qs`-DoS (dev-only, akzeptiert)
**Priorität:** Niedrig
**Problem:** `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert.
**Behebung/Trigger:** Entfällt bei Stryker-Major-Bump.

---

## TD-S083-1 — Frontend Hooks: `onSuccess` feuert auch bei `Err`
**Priorität:** Mittel – Error-Szenario
**Problem:** `useResultMutation.onSuccess` feuert auch bei `Err` (`Promise.resolve(ResultAsync)` wirft nicht). `throwOnError` entfernt + kein `r.ok`-Check in `ingredientsApi` (ADR-S083-2). **Erweitert (S084):** `conditionalGet.ts` setzt das Muster fort – kein `response.ok`-Check, d.h. ein 4xx/5xx-Body würde als Erfolg geparst+gecacht; zusätzlich `cached!` im 304-Pfad (YAGNI, 304 ohne Cache-Eintrag würfe).
**Behebung/Trigger:** Vor dem Error-Szenario auf `result.match(onSuccess, onError)` umstellen – dieselbe Error-Handling-Umstellung konsistent für GET+POST (ApiError-aus-Status, `response.ok`-Check).

---

## TD-S083-2 — Frontend UX (projektweit): kein `ThemeProvider`/`CssBaseline`
**Priorität:** Mittel
**Problem:** Kein `ThemeProvider`/`CssBaseline` → Touch-Targets <44px, kein MD3-Type-Scale.
**Behebung/Trigger:** Eigene UX-Foundation-Aufgabe.

---

## TD-S083-3 — Frontend: Cold-Start-Race beim ersten GET
**Priorität:** Niedrig
**Problem:** Feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET) → gerade angelegte Zutat erscheint nicht. Nur bei kaltem Server / langsamem erstem GET (warm: unkritisch).
**Behebung/Trigger:** pending-State-Szenario („Speichern-Button deaktiviert") sperrt den Save bis zum Settle der Query.

---

## TD-S083-4 — Validierung (FE+BE): keine Max-Length, keine Branded-Types
**Priorität:** Niedrig
**Problem:** Keine Max-Length auf Name/DefaultUnit (Kestrel-Body-Limit deckelt); keine Frontend-Branded-Types/`makeIngredientName`-Factory.
**Behebung/Trigger:** Validierungs-Szenario.

---

## TD-S083-5 — E2E-Test: `EmptyDb`-Test ohne DB-Reset
**Priorität:** Niedrig
**Problem:** `EmptyDb`-Test ohne DB-Reset – latent flaky wenn DB vorher befüllt (durch „Zutat anlegen" jetzt verschärft).
**Behebung/Trigger:** DB-Reset/Isolation im E2E-Setup einführen.

---

## TD-S084-1 — HTTP/ETag-Middleware (BE): vollständige Response-Pufferung
**Priorität:** Niedrig jetzt / Hoch vor File-Serving bzw. Auth
**Problem:** `ETagMiddleware` puffert **jede** GET-Response komplett in einen `MemoryStream` (+`ToArray()`-Kopie) → (a) DoS-/Speicher-Risiko sobald große/paginierungsfreie Collections oder File-/Image-GETs dazukommen (Buffering+Hash zwingt Nicht-Streaming); (b) `next()` ist nicht in try/finally → bei Endpoint-Exception wird `Response.Body` nicht auf den Original-Stream zurückgesetzt (heute folgenlos – keine Error-Handling-Middleware); (c) 304 setzt kein `Cache-Control: private`/`Vary` → ab MVP-Auth + Reverse-Proxy Cross-User-Leak über Shared-Caches.
**Behebung/Trigger:** Alle drei aufgeschoben (derzeit Survivor-/Scope-frei nicht umsetzbar). Auslöser: (a) vor File-/Image-Serving bzw. großen Collections → Größen-Cap oder Routen-/Content-Type-Whitelist; (b) sobald eine Error-Handling-Middleware davorkommt → try/finally; (c) vor MVP-Auth + Reverse-Proxy.

---

## TD-S084-2 — HTTP/ETag (BE): `GET /api/ingredients` ohne `OrderBy`
**Priorität:** Mittel – der gerade gebaute ETag ist bis dahin nutzlos; SKELETON nicht deployt
**Problem:** `GET /api/ingredients` ohne `OrderBy` → Collection-Content-Hash-ETag (ADR-S084-1/-2) ist auf Postgres nicht stabil (undefinierte Heap-Order) → `If-None-Match` matcht nie → 304 feuert nie, Caching wirkungslos (Daten korrekt; Effektivitäts-, kein Korrektheits-Bug). Tests grün nur wegen EF-InMemory-Insertion-Order.
**Behebung/Trigger:** Alphabetisches Sortier-Szenario (@US-904) führt `OrderBy(name)` Stryker-killbar ein. Reines `OrderBy(id)` jetzt wäre un-killbar (Suppression).
