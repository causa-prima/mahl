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

## TD-S077-1 — Frontend Komponente: manuelles State-Sync + UX-Politur
**Priorität:** Niedrig
**Problem:** `isDialogOpen` + `closeDialog` synct 3 `useState`-Slices manuell. UX-Politur offen: `<p>`→`Typography`, TextFields `fullWidth`/`margin`, Layout-Container/Heading.
**Behebung/Trigger:** Eigenes Mini-Szenario; bei Speichern/Validierung auf Discriminated Union umstellen.

---

## TD-S080-1 — Frontend Deps: `qs`-DoS (dev-only, akzeptiert)
**Priorität:** Niedrig
**Problem:** `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert.
**Behebung/Trigger:** Entfällt bei Stryker-Major-Bump.

---

## TD-S083-1 — Frontend GET-Pfad: kein `response.ok`-Check, Err wird verschluckt
**Priorität:** Mittel – resilience-„Laden"-Szenarien
**Teilweise behoben (S090):** Der POST/Mutation-Pfad ist erledigt – `useResultMutation.onSuccess` feuert via `result.match` nur noch im `Ok`-Zweig, und `createIngredient` prüft den Status (422 → `FieldErrors`). **Offen bleibt der GET-Pfad:** `conditionalGet.ts` hat weiterhin **keinen `response.ok`-Check** (ein 4xx/5xx-Body würde als Erfolg geparst+gecacht; zusätzlich `cached!` im 304-Pfad, YAGNI). Außerdem **schluckt `useResultQuery` den `Err`** via `unwrapOr(undefined as TData)` (Type-Lie) → ein GET-Fehler ist nicht von „noch keine Daten"/Leerzustand unterscheidbar (war separat als Review-Finding cq-F3/„TD3" notiert).
**Behebung/Trigger:** Mit den resilience-„Laden"-Szenarien (`@NFR-resilience` „Backend nicht erreichbar/Serverfehler beim Laden") den GET-Fehlerpfad einführen: `response.ok`-Check in `conditionalGet`, GET-Err in `useResultQuery` als beobachtbaren Fehlerzustand statt Leerzustand.

---

## TD-S083-2 — Frontend UX (projektweit): kein `ThemeProvider`/`CssBaseline`
**Priorität:** Mittel
**Problem:** Kein `ThemeProvider`/`CssBaseline` → Touch-Targets <44px, kein MD3-Type-Scale.
**Behebung/Trigger:** Eigene UX-Foundation-Aufgabe.

---

## TD-S083-3 — Frontend: Cold-Start-Race beim ersten GET
**Priorität:** Niedrig
**Problem:** Feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET) → gerade angelegte Zutat erscheint nicht. Nur bei kaltem Server / langsamem erstem GET (warm: unkritisch).
**Behebung/Trigger:** Save (bzw. den POST) sperren, bis der initiale Listen-GET **gesettled** ist – z.B. Speichern-Button `disabled`, solange die Ingredients-Query `isPending`/`isLoading`. **Achtung:** run-2's `disabled={isPending}` löst das *nicht* – dessen `isPending` ist der Pending-State der *POST-Mutation* (sperrt während des Speicherns, nachdem der POST schon feuerte), nicht der des initialen GET.

---

## TD-S083-4 — Validierung (FE+BE): Max-Length, keine Branded-Types
**Priorität:** Niedrig
**Teilweise behoben (S102/run-3):** `name`-Max-Length (30 Zeichen, nach Trimming) server-seitig implementiert (ADR-S051-3, `IngredientMappings.ValidateName`).
**Offen:** `defaultUnit`-Max-Length (20, ADR-S051-3) → mit run-4 (Einheit-Validierung); Frontend-Branded-Types/`makeIngredientName`-Factory (kein Szenario, YAGNI).
**Behebung/Trigger:** `defaultUnit`-Max-Length mit run-4; Branded-Types bei Bedarf.

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

---

## TD-S089-1 — Backend Coverage-Gate unter MTP nicht funktionsfähig (vorübergehend deaktiviert)
**Priorität:** Hoch – das Branch-Coverage-Gate (NFR/DoD) ist aktuell ohne Wirkung
**Problem:** Das Test-Projekt nutzt den Microsoft.Testing.Platform-Runner (xunit.v3). `coverlet.collector` (VSTest-DataCollector) ist darunter wirkungslos → der alte `dotnet-test.py` „bestand" das Gate über **veraltete** cobertura-Reports aus dem `/mnt/c`-Altrepo (Stale-Masking; erst durch den ext4-Umzug aufgedeckt). MTP-native Engines klemmen am gepinnten Stack: `Microsoft.Testing.Extensions.CodeCoverage` 18.3.2 und `coverlet.MTP` 8.0.1/10.0.1 → `TypeLoadException` (`TestHost.IDataConsumer`) gegen MTP 2.0.2.0/2.2.2.0; nur CodeCoverage 17.14.2 lief, scheiterte aber am `--coverage-settings`-Format. Gate daher in `dotnet-test.py` **explizit deaktiviert** (`collect_coverage = False`; kein Fake-100%, kein Hard-Block); Parser/Reporter + fail-closed-Logik bleiben re-enable-bereit.
**Behebung/Trigger:** MTP-Coverage sauber aufsetzen — entweder `Microsoft.Testing.Extensions.CodeCoverage` **18.1.x** (versionsalignt zu MTP 2.0.x; `--coverage-settings` = bloßes `<Configuration>`-Root; Auto-Props nur via breitem `CompilerGeneratedAttribute`-Exclude, schließt async/yield mit aus) **oder** `xunit.v3`-Bump auf den MTP-2.2-Stack + `coverlet.MTP` 10.x (präzises `--coverlet-skip-auto-props`, bevorzugt). Danach `collect_coverage` reaktivieren + 100% verifizieren.

---

## TD-S090-1 — Backend-Validierung: collect-all-Merge (beide Felder gleichzeitig)
**Priorität:** Mittel – fällig beim „beide leer"-Szenario
**Problem:** `IngredientsEndpoints.ToDomain` validiert die Felder **sequenziell/kurzschließend** (Name zuerst, dann Einheit) → sind beide leer, kommt nur die erste Meldung zurück. Das „Beide Pflichtfelder leer"-Szenario verlangt aber **beide** Meldungen gleichzeitig (ADR-S000-1 collect-all).
**Behebung/Trigger:** Beim „beide leer"-Szenario `ToDomain` auf **unabhängige** Validierung beider Felder + Merge der Fehler umstellen (`IngredientValidationError` zu einer Menge/Liste erweitern).

---

## TD-S090-2 — Frontend: `matchKind` für Komponenten-Fehler-Unions noch nicht adoptiert
**Priorität:** Niedrig – fällig mit dem resilience-`QueryCache.onError`-Setup
**Problem:** `IngredientsPage` liest den Domain-Fehler per geguardetem direktem `kind`-Check (`saveError?.kind === 'FieldErrors' ? …`), nicht über `matchKind` (ADR-S056-1 / Guideline §4b „Pflicht"). Bewusst aufgeschoben (Code-Kommentar an der Stelle): das kanonische Muster trennt Netzwerk/5xx (werfen → `QueryCache.onError`/Toast) von Domain-Fehlern (matchKind); `onError` existiert noch nicht, daher trägt `ApiError` aktuell den `Unexpected`-kind. `matchKind` jetzt über `FieldErrors|Unexpected` bräuchte eine Suppression auf dem ungetesteten `Unexpected`-Arm, den die resilience-Arbeit wieder entfernt (Churn).
**Behebung/Trigger:** Mit dem resilience-„Speichern/Laden"-Szenario `QueryCache.onError` einführen → Netzwerk/5xx wirft dorthin, die Komponenten-Fehler-Union kollabiert auf Domain-Fehler-only (`FieldErrors`), dann `matchKind` mit einem voll getriebenen Arm (kein Survivor).

---

## TD-S090-3 — Backend: `CreateIngredientDto` non-nullable → fehlendes JSON-Property evtl. 400 statt 422
**Priorität:** Niedrig – kein treibendes Szenario
**Problem:** `CreateIngredientDto(string Name, string DefaultUnit)` ist non-nullable. Lässt ein Client das `name`-Property **ganz weg** (statt `""`), kann ASP.NET Minimal API je nach STJ-Konfiguration `null` binden (Warnung) oder **400** vor dem Handler werfen — nicht das vertragliche **422** mit `{"errors":{…}}`. Der Client parst in `toIngredientResult` nur `status === 422` als Fehler; ein 400 würde als `Ingredient` interpretiert → stiller Fehlzustand. Aktuell unerreichbar (das Szenario sendet stets `name: ""`).
**Behebung/Trigger:** Sobald ein Szenario fehlende/null-Properties adressiert: `string?`-Properties + bewusste Null-Behandlung in `ToDomain`, oder ein einheitlicher 4xx→`{"errors"}`-Mapper.

---

## TD-S094-1 — Zutaten-Dialog: Fokus aufs erste fehlerhafte Feld fehlt (Prinzip 8)
**Priorität:** Mittel – passend zu run-4 „Anlegen·Einheit-Validierung"
**Problem:** Nach einem Validierungsfehler springt der Fokus nicht aufs erste fehlerhafte Feld (UX-Guideline Prinzip 8); die Error-Tests prüfen nur `aria-invalid`, nicht den Fokus. Der Fehlerpfad wird erst von den @US-904-error-Läufen getrieben – run-2 (Dialog-Verhalten, Happy-Path) enthält kein Szenario, das Fokus-nach-Fehler beobachtbar macht.
**Behebung/Trigger:** Braucht ein Szenario (spec-first), das den Fokus-nach-Fehler fordert – passend zu run-4 „Einheit-Validierung", wo der Fehlerpfad das treibende Szenario ist; per Review (Prinzip 8) erzwungen.

---

## TD-S101-1 — Frontend Hook: `useResultMutation` 4er-Positions-Tupel
**Priorität:** Niedrig
**Problem:** `useResultMutation` gibt ein 4-Tupel `[mutate, error, isPending, reset]` zurück (zwei davon Funktionen). Positions-Tupel werden mit wachsender Länge fehleranfällig: Call-Sites destrukturieren in exakter Reihenfolge, `error`/`isPending` sind leicht verwechselbar. Ein Objekt `{ save, error, isPending, reset }` wäre selbstdokumentierend und reihenfolgeunabhängig.
**Behebung/Trigger:** Mit dem nächsten großen Hook-Schritt bündeln (volle MutationState-Union, ADR-S083-2) – dann die Rückgabe auf ein Objekt umstellen, damit die Call-Sites nicht zweimal angefasst werden.

---

## TD-S102-1 — Backend: kein explizites app-weites Request-Body-Size-Limit
**Priorität:** Niedrig – SKELETON ohne Auth; durch Kestrels impliziten ~30-MB-Default begrenzt
**Problem:** `POST /api/ingredients` deserialisiert/bindet den vollständigen Request-Body, BEVOR die Feld-Validierung greift (`name.Value.Length > 30` läuft erst nach Model-Binding). Ein anonymer Client kann daher wiederholt große Bodies (bis Kestrels implizitem ~30-MB-Default, in `Program.cs` nirgends explizit gesetzt) senden → Parsing-/Trimming-Last vor jeder Ablehnung. Kein durch run-3 verschärftes Risiko – der Zustand ist ggü. vorher unverändert. (Die fehlende `defaultUnit`-Längenbegrenzung ist Teil von TD-S083-4, nicht hier.) Quelle: security-auditor (Review run-3, SR-2).
**Behebung/Trigger:** Explizites app-weites `MaxRequestBodySize` in `Program.cs` (statt Verlass auf den impliziten Framework-Default) – mit run-4 oder einer eigenen Härtungs-Aufgabe.
