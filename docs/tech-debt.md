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

## TD-S101-1 — Frontend Hook: `useResultMutation` 4er-Positions-Tupel
**Priorität:** Niedrig
**Problem:** `useResultMutation` gibt ein 4-Tupel `[mutate, error, isPending, reset]` zurück (zwei davon Funktionen). Positions-Tupel werden mit wachsender Länge fehleranfällig: Call-Sites destrukturieren in exakter Reihenfolge, `error`/`isPending` sind leicht verwechselbar. Ein Objekt `{ save, error, isPending, reset }` wäre selbstdokumentierend und reihenfolgeunabhängig.
**Behebung/Trigger:** Mit dem nächsten großen Hook-Schritt bündeln (volle MutationState-Union, ADR-S083-2) – dann die Rückgabe auf ein Objekt umstellen, damit die Call-Sites nicht zweimal angefasst werden.

---

## TD-S102-1 — Backend: kein explizites app-weites Request-Body-Size-Limit
**Priorität:** Niedrig – SKELETON ohne Auth; durch Kestrels impliziten ~30-MB-Default begrenzt
**Problem:** `POST /api/ingredients` deserialisiert/bindet den vollständigen Request-Body, BEVOR die Feld-Validierung greift (`name.Value.Length > 30` läuft erst nach Model-Binding). Ein anonymer Client kann daher wiederholt große Bodies (bis Kestrels implizitem ~30-MB-Default, in `Program.cs` nirgends explizit gesetzt) senden → Parsing-/Trimming-Last vor jeder Ablehnung. Kein durch run-3 verschärftes Risiko – der Zustand ist ggü. vorher unverändert. (Die fehlende `defaultUnit`-Längenbegrenzung ist Teil von TD-S083-4, nicht hier.) Quelle: security-auditor (Review run-3, SR-2).
**Behebung/Trigger:** Explizites app-weites `MaxRequestBodySize` in `Program.cs` (statt Verlass auf den impliziten Framework-Default) – mit run-4 oder einer eigenen Härtungs-Aufgabe.

---

## TD-S106-1 — Backend: kein globaler Exception-Handler / ProblemDetails-Fallback
**Priorität:** Niedrig – SKELETON ohne Auth; der konkrete run-10-500-Pfad (malformed If-Match) ist bereits gefixt (ADR-S106-2)
**Problem:** `Server/Program.cs` registriert keinen `app.UseExceptionHandler(...)` / kein `AddProblemDetails`. Eine unbehandelte Exception in irgendeinem Endpoint schlägt daher als roher 500 durch – bei versehentlichem `ASPNETCORE_ENVIRONMENT=Development` mit voller Developer-Exception-Page (Stack-Trace-Leak, NFR-Verstoß „keine Stack-Traces für User"). DELETE war der erste Endpoint mit client-steuerbarem Input, der das sichtbar machte; der konkrete Pfad ist mit `XminETag.TryParse` → 400 (ADR-S106-2) geschlossen, aber die systemische Verteidigungslinie fehlt weiterhin. Quelle: security-auditor (Review run-10, SEC-2).
**Behebung/Trigger:** Zentralen Exception-Handler ergänzen (mappt unbehandelte Exceptions generisch auf RFC7807-ProblemDetails ohne Stack-Trace) – bei der ersten Härtungs-/Resilience-Aufgabe oder sobald ein weiterer Endpoint client-steuerbaren Input verarbeitet.

---

## TD-S108-1 — Frontend Delete/Restore-Pfad: optimistischer Undo-Toast + kein Status-Check
**Priorität:** Mittel – ab dem ersten Delete-Resilience-/Fehler-Szenario
**Problem:** Zwei zusammenhängende Lücken im Löschen-/Undo-Pfad (`useDeleteIngredientWithUndo.ts`, `ingredientsApi.ts`):
(a) **Optimistischer Toast.** `requestDelete` setzt `deleted` **synchron vor** dem Mutation-Call – der Toast „X gelöscht" erscheint also, bevor der DELETE-Request überhaupt beantwortet ist, während die Liste erst nach Server-Antwort + `invalidateQueries` aktualisiert wird. Folgen: bei spürbarer Latenz zeigt die UI gleichzeitig „X gelöscht" **und** X unverändert in der Liste (inkl. klickbarem Löschen-Button); bei einem Netzwerkfehler bleibt eine **falsche Erfolgsmeldung** samt Undo-Button für eine Löschung stehen, die nie stattfand. Der Restore-Pfad macht es bereits richtig (`setDeleted(null)` + `onChanged()` gemeinsam im `onSuccess`).
(b) **Kein Status-Check.** `deleteIngredient`/`restoreIngredient` nutzen `ResultAsync.fromPromise(fetch(...))` ohne Auswertung von `response.status` – ein 404/412/428 wird wie ein Erfolg behandelt. Das ist derselbe Defekt, den TD-S083-1 für den GET-Pfad beschreibt; für den POST-Pfad wurde er in S090 behoben, DELETE/RESTORE sind neue Mutation-Pfade, die den Check nicht übernommen haben.
(c) **Undo kann wirkungslos verpuffen (Race).** Weil der Toast optimistisch erscheint, ist „Rückgängig" bereits klickbar, während der DELETE noch unterwegs ist. Trifft der `POST /restore` **vor** dem `SaveChangesAsync` des DELETE ein, findet der Restore die Zeile noch aktiv (`DeletedAt` ist noch `null`) → EF erkennt keine Änderung → kein UPDATE, kein xmin-Bump. Der danach eintreffende DELETE matcht seinen alten xmin weiterhin und committet normal. Endzustand: **Zutat bleibt gelöscht, obwohl der Nutzer „Rückgängig" geklickt hat** – ohne jede Fehlermeldung, der Toast verschwindet einfach. Das ist schärfer als (a): dort geht es um eine Anzeige-Inkonsistenz, hier um einen real verlorenen Undo. Praktisch selten (erfordert einen Klick innerhalb der DELETE-Roundtrip-Zeit), aber bei langsamer Verbindung erreichbar.
Alle drei Punkte sind im Erfolgsfall bei schnellem Netz unbeobachtbar – deshalb erzwingt kein Szenario sie heute. Quelle: ux-ui-auditor + functional-correctness-auditor (Review run-8, (a)/(b) unabhängig doppelt gefunden, (c) in Review-Runde 2).
**Behebung/Trigger:** Mit dem ersten Delete-Fehler-/Resilience-Szenario gemeinsam beheben: `setDeleted` in den Erfolgs-Callback verschieben **und** die Fehler-Union für Delete/Restore einführen (dann trägt `ApiError` echte Domain-Kinds statt nur `Unexpected`, vgl. ADR-S056-1). Getrennt zu fixen lohnt nicht – (a) ohne (b) lässt einen 404 weiterhin als Erfolg durchgehen. Das Verschieben von `setDeleted` schließt (c) als Nebeneffekt mit: Ist der Undo-Button erst nach dem Delete-Erfolg klickbar, kann der Restore den DELETE nicht mehr überholen.

---

## TD-S108-2 — Frontend: kein Fokus-Management nach Löschen und nach Undo
**Priorität:** Niedrig – relevant, sobald die App mehr Seiten/Navigation hat
**Problem:** Nach dem Löschen einer Zutat unmountet das fokussierte Element (der Löschen-`IconButton` bzw. bei der letzten Zutat die ganze Liste), ohne dass der Fokus gezielt weitergeführt wird – der Browser setzt ihn auf `<body>` zurück. Dasselbe passiert nach einem Undo-Klick, wenn die Snackbar unmountet. Tastatur- und Screenreader-Nutzer müssen den „Rückgängig"-Weg danach per Tab suchen. Entschärfend: `SnackbarContent` setzt `role="alert"` (MUI-Default), die Meldung samt Undo-Möglichkeit wird also **angesagt**; MUI pausiert zudem den Auto-Hide-Timer, sobald der Button Fokus erhält – wer ihn erreicht, verliert die Zeit nicht. Heute sind es 1–2 Tab-Stopps, das wächst aber mit jeder weiteren Seite. Quelle: ux-ui-auditor (Review run-8, Runde 2).
**Behebung/Trigger:** Nicht als Schnellfix erledigen – die naheliegende Lösung (Autofokus auf „Rückgängig") hat echte Nebenwirkungen: Fokus-Stealing in ein selbstschließendes Element reißt den Nutzer aus dem Arbeitsfluss, und weil MUI bei Fokus den Timer pausiert, bliebe der Toast für Tastaturnutzer stehen, bis er aktiv weggedrückt wird. Zusammen mit dem ersten Navigations-/Mehrseiten-Schritt (US-602, vgl. UX-Guideline Prinzip 9) als bewusste Fokus-Strategie entscheiden – dann liegt auch ein realistischer Tab-Kontext zur Bewertung vor.

---

## TD-S108-3 — Frontend-Tests: Given+When-Setup der Löschen-Tests dreifach dupliziert
**Priorität:** Niedrig
**Problem:** Die Kombination aus MSW-Handler-Setup, `renderWithProviders` und dem Löschen-Klick steht in drei Component-Tests in `Client/src/pages/IngredientsPage.test.tsx` nahezu wortgleich, ohne gemeinsamen Helper – analog in den E2E-Tests. In derselben Datei ist das Rule-of-Three-Muster bereits etabliert (`renderWithPendingSave`, `submitWithDelayedPost`); hier wurde es nicht angewandt, obwohl die Schwelle erreicht ist. Quelle: test-quality-auditor (Review run-8).
**Behebung/Trigger:** Beim nächsten Lauf, der diese Tests ohnehin anfasst (run-9 „Löschen·Pending" berührt genau diese Fläche), einen gemeinsamen Given+When-Helper extrahieren. Nicht als eigener Refactoring-Schritt – der Nutzen rechtfertigt keinen separaten Test-Freigabe-Zyklus.

---

## TD-S108-4 — Frontend: Undo-Toast auf Touch-Geräten nicht manuell schließbar
**Priorität:** Niedrig
**Problem:** Seit der Undo-Toast `clickaway` bewusst ignoriert (damit ein beiläufiger Klick den einzigen Weg zurück nicht wegnimmt, `IngredientsPage.tsx`), bleiben als Schließ-Wege nur Timeout und Escape. Auf Touch-Geräten ist Escape praktisch nicht auslösbar und ein Schließen-Button existiert nicht – dort verschwindet der Toast ausschließlich nach Ablauf der 6 Sekunden. Kein Datenverlust und keine Blockade (die Snackbar ist nicht-blockierend), aber auf dem primären Zielgerät der App (Mobile-First) kann der Nutzer die Meldung nicht aktiv wegräumen. Quelle: functional-correctness-auditor (Review run-8).
**Behebung/Trigger:** Zusätzliche Schließen-Action (`CloseIcon`) neben „Rückgängig" – ein expliziter Button ist eine bewusste Geste und kollidiert nicht mit dem clickaway-Guard, der nur beiläufige Klicks abfängt. Da es sichtbares Nutzerverhalten ist, gehört ein Gherkin-Szenario davor (nicht wie in run-8 nachträglich). Trigger: der nächste Lauf, der den Toast ohnehin verändert – z.B. run-9 „Löschen·Pending".
