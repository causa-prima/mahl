# Technische Schuld

<!--
wann-lesen: Wenn der zu bearbeitende Code einen der Bereiche unten berührt (z.B. Architektur-Check
            in implementing-scenario) sowie beim Session-Abschluss (closing-session, nfr.md).
wann-schreiben: Sobald eine bewusst aufgeschobene Schuld entsteht (⚠️-Finding nicht sofort gefixt,
            bewusste Vereinfachung, vertagte Härtung).

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen (kein Umsortieren).

Eintrag-Format:
  ## TD-S<NNN>-<n> — <Bereich/Kurztitel>
  **Fällig:** <Anker>[, <Anker>…] – <Freitext-Erläuterung>
  **Problem:** <was ist die Schuld>
  **Behebung:** <wie behoben wird>

  ID: TD-S<NNN>-<n> – 3-stellige Session (Ursprung), laufende Nummer innerhalb der Session.
  Freie fettgesetzte Absätze (`**Zusammenhang:**`, `**Reichweite präzisiert:**` …) sind erlaubt,
  die drei Felder oben sind Pflicht.

Regeln zum Feld `**Fällig:**` (mechanisch geprüft von `.claude/hooks/check-td-capture.py`,
Grammatik und Auflösung kanonisch in `.claude/scripts/td_anchors.py`):

  1. Pflicht. Ein Eintrag, der nur sagt, WIE behoben wird, schuldet niemandem einen Zeitpunkt.

  2. Der **Kopf** vor dem Gedankenstrich ist maschinenlesbar, der Rest bleibt Prosa und trägt
     weiter die Nuance. Anker-Vokabular:

       jetzt              sofort
       Phase:MVP          Phasenwechsel (auch V1/V2) – tritt ein, wenn AGENT_MEMORY sie erreicht
       S130               Spätestens-Termin (Session-Nummer)
       Szenario:„…"       ein Gherkin-Szenario aus features/ (Titel exakt, muss existieren)
       US-602             eine Story – nur gültig, SOLANGE sie keine Szenarien hat
       TD-S089-1          ein anderer Eintrag – tritt ein, wenn jener behoben (entfernt) ist

  3. Mindestens ein Anker muss **terminiert** sein, also sagen WANN. Terminiert sind `jetzt`,
     `Phase:`, `S<NNN>` und ein `Szenario:` mit `# @run-N`-Zuordnung. NICHT terminiert sind
     `US-NNN` (die Story kann beliebig lange ungeplant bleiben) und ein `Szenario:` ohne
     Lauf-Zuordnung; eine `TD-`-Kette erbt die Terminierung und muss zyklenfrei sein. Fehlt sie,
     gehört ein Backstop dazu: `Szenario:„…", Phase:MVP`. Grund: Ein Anker, der nur eintreten
     *kann*, lässt den Eintrag lautlos verwaisen (OBS-S099-1).

  4. `jetzt` verlangt einen Punkt in `docs/AGENT_MEMORY.md` unter „Nächste Prioritäten" – der
     Hook prüft, ob die TD-ID dort vorkommt. Diese Datei hier wird nur situativ gelesen
     (Architektur-Check in `implementing-scenario`), `AGENT_MEMORY.md` bei jedem Session-Start.

  5. Verletzt der Eintrag eine HEUTE geltende Regel (NFR, Guideline, DoD), ist die Fälligkeit
     immer `jetzt` – eine geltende Regel wartet auf keine Bedingung. Soll sie doch warten, ist
     das eine Entscheidung über die Regel: Regel ändern oder Ausnahme als ADR dokumentieren
     (so ADR-S083-2 für TD-S101-1). Ein ungeprüfter Verdacht ist keine Verletzung – dann ist
     die Prüfung die Behebung und bekommt eine eigene Fälligkeit.

  6. **Story-Anker umhängen, sobald die Story Szenarien hat.** Vor dem `gherkin-workshop` ist
     `US-NNN` die feinste verfügbare Granularität; danach steht fest, zu welchem Szenario die
     Schuld gehört – oder die ehrliche Antwort ist `jetzt` (vor Implementierungsbeginn zu
     erledigen). Der Übergang wird nicht vom `gherkin-workshop` erzwungen (der soll ohne Wissen
     über TD-Tracking funktionieren), sondern vom `td-due`-Modul der `session-agenda.py`: Es
     meldet jeden Story-Anker, dessen Story inzwischen Szenarien trägt.
-->

## TD-S044-1 — STJ/Deserialisierung
**Fällig:** US-602, Phase:V1 – URI-Felder. Der Story-Anker gilt nur, solange US-602 keine Szenarien hat; danach auf das tragende Szenario umhängen.
**Problem:** 400 vs. 500 bei ungültigem URI; STJ via `OriginalString` unverifiziert.
**Behebung:** STJ-Pfad verifizieren und 400 statt 500 erzwingen.

---

## TD-S077-1 — `IngredientsPage`: manuelles State-Sync, fehlende UX-Baseline, überlange Komponenten
**Fällig:** TD-S083-2 – Theme-Foundation (dort `jetzt`). (a) und (c) auch früher, sobald die Datei ohnehin angefasst wird.
**Problem:** Drei Befunde in derselben Datei, alle auf zu grob geschnittene Komponenten zurückgehend:
(a) **Manuelles State-Sync.** `closeDialog` setzt drei `useState`-Slices von Hand zurück (`isDialogOpen`, `name`, `unit`) – jeder künftige Feld-Zustand muss dort mitgepflegt werden, sonst bleibt ein Rest stehen.
(b) **Fehlende UX-Baseline.** Der Leerzustand ist ein nacktes `<p>Noch keine Zutaten angelegt.</p>` statt `Typography`; die TextFields tragen weder `fullWidth` noch `margin`; der Seitenrumpf ist ein blankes `<div>` ohne Layout-Container und ohne Überschrift.
(c) **Zwei Funktionen über dem Lint-Deckel.** `CreateIngredientDialog` (53 Zeilen) und `IngredientsPage` (57 Zeilen) gegen `max-lines-per-function` 50 – die einzigen beiden ESLint-Warnungen des Projekts neben einer Test-Helper-Warnung.
**Behebung:** (b) reist mit der Theme-Foundation aus TD-S083-2 – gleiche Datei, gleiche visuelle Baseline. (a) und (c) sind reine Refactorings **ohne beobachtbare Verhaltensänderung** und brauchen deshalb kein Szenario: bei grünen Tests mitnehmen.

---

## TD-S080-1 — Frontend Deps: `qs`-DoS (dev-only, akzeptiert)
**Fällig:** Phase:MVP – primär der nächste Stryker-Major-Bump; ein Dependency-Bump ist kein maschinenlesbarer Anker, deshalb trägt hier der Backstop: ab MVP neu bewerten, falls der Bump bis dahin ausbleibt.
**Problem:** `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert.
**Behebung:** Entfällt mit dem Bump von selbst; bis dahin bewusst getragen.

---

## TD-S083-1 — Frontend GET-Pfad: kein `response.ok`-Check, Err wird verschluckt
**Fällig:** Szenario:„Backend nicht erreichbar beim Laden einer Seite", Szenario:„Backend liefert Serverfehler beim Laden einer Seite", Phase:MVP – die beiden `@NFR-resilience`-„Laden"-Szenarien existieren, sind aber keinem Lauf zugeordnet; daher der Phasen-Backstop.
**Problem:** Zwei Lücken im GET-Pfad (der POST/Mutation-Pfad ist davon nicht betroffen):
(a) **Kein `response.ok`-Check.** `conditionalGet.ts` parst die Antwort unbedingt – ein 4xx/5xx-Body wird als Erfolg geparst und als Daten zurückgegeben. Nicht gecacht: `cache200` schreibt nur bei vorhandenem ETag-Header, und `ETagMiddleware` setzt den ausschließlich bei Status 200. Zusätzlich `cached!` im 304-Pfad (YAGNI).
(b) **`useResultQuery` schluckt den `Err`** via `unwrapOr(undefined as TData)` (Type-Lie) → ein GET-Fehler ist nicht von „noch keine Daten"/Leerzustand unterscheidbar.
**Behebung:** GET-Fehlerpfad einführen: `response.ok`-Check in `conditionalGet`, GET-Err in `useResultQuery` als beobachtbaren Fehlerzustand statt Leerzustand.

---

## TD-S083-2 — Keine Theme-Foundation; Touch-Targets verletzen dadurch eine stehende Anforderung
**Fällig:** jetzt – die Accessibility-Anforderung gilt heute und wird heute verletzt; terminiert in `docs/AGENT_MEMORY.md` (vor Beginn der nächsten Story)
**Problem:** In `Client/src` existiert weder `ThemeProvider` noch `CssBaseline` noch `createTheme` – `main.tsx` hält allein den `QueryClientProvider`. Folge 1: `docs/process/nfr.md` (Accessibility) fordert Touch-Targets ≥ 44×44px; `IngredientsPage.tsx` rendert **sechs** interaktive Controls (Zeilen 124, 125, 148, 246, 296) ohne jede Größenangabe – `size=` und `sx=` kommen in der Datei nicht vor – und liegt damit auf MUIs Defaults (Button ~36,5px, IconButton 40×40). Einzig die TextFields (56px) erfüllen die Anforderung. Folge 2: kein MD3-Type-Scale, keine zentrale Quelle für Spacing/Hierarchie/Farbe, keine MUI-Baseline-Styles – jede Komponente entscheidet visuell für sich.
**Behebung:** `ThemeProvider` + `CssBaseline` in `main.tsx`, Mindestgrößen als Komponenten-Defaults (`MuiButton`/`MuiIconButton`). Verworfen: Mindestgrößen je Element via `sx` – sechs Stellen, und das siebte Control fällt wieder durch. Der Nachweis ist eine NFR-Eigenschaft, kein Nutzer-Szenario: als ausgewiesener Infra-Test nach ADR-S106-3 über die Bounding-Box führen. Zieht die Priorität „Visuelle Konsistenz-Guideline" in `docs/AGENT_MEMORY.md` mit – das Theme ist der Mechanismus, den jene Guideline vorschreiben würde.

---

## TD-S083-3 — Frontend: Cold-Start-Race beim ersten GET
**Fällig:** TD-S083-1 – Query-Zustand in `useResultQuery` (ADR-S083-2); vorher technisch nicht umsetzbar.
**Problem:** Feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET) → gerade angelegte Zutat erscheint nicht. Nur bei kaltem Server / langsamem erstem GET (warm: unkritisch). **Vorher nicht umsetzbar:** `useResultQuery` liefert ausschließlich `TData | undefined` und exponiert keinerlei Lade-/Fehlerzustand – die Seite *kann* nicht wissen, ob der initiale GET gesettled ist.
**Behebung:** Speichern sperren, solange die Ingredients-Query nicht gesettled ist. **Achtung:** Das vorhandene `disabled={isPending}` löst das nicht – dessen `isPending` stammt aus `useCreateIngredientWithReactivation` und ist der Zustand der *POST-Mutation*, greift also erst, nachdem der POST bereits feuerte.

---

## TD-S083-4 — Frontend-Domänentypen ohne Branded Types
**Fällig:** jetzt – `coding-guideline-typescript.md` §2 gilt heute und wird heute verletzt; terminiert in `docs/AGENT_MEMORY.md` (vor Beginn der nächsten Story)
**Problem:** `ingredientsApi.ts` definiert `Ingredient` (id, name, defaultUnit, etag) und `NewIngredient` (name, defaultUnit) mit nackten `string`-Feldern; in `Client/src` existiert kein einziger Branded Type. Guideline §2 verlangt die Kapselung. Signaturen mit mehreren gleichartigen Parametern hintereinander – etwa `restoreIngredient(id, name, defaultUnit)` – sind dadurch gegen Vertauscher ungeschützt, obwohl der Compiler sie fangen könnte; genau diese Signatur führt §2 als Motivation an.
**Behebung:** Nominale Brands nach ADR-S112-4 (Vergabe an der API-Grenze, keine Regelprüfung) für beide Typen.

---

## TD-S084-1 — HTTP/ETag-Middleware (BE): vollständige Response-Pufferung
**Fällig:** TD-S106-1, Phase:MVP – (a) vor File-/Image-Serving bzw. paginierungsfreien Collections; (b) mit TD-S106-1 (Error-Handling-Middleware); (c) vor MVP-Auth + Reverse-Proxy. Alle drei spätestens ab MVP.
**Problem:** `ETagMiddleware` puffert **jede** GET-Response komplett in einen `MemoryStream` (+`ToArray()`-Kopie) → (a) DoS-/Speicher-Risiko sobald große/paginierungsfreie Collections oder File-/Image-GETs dazukommen (Buffering+Hash zwingt Nicht-Streaming); (b) `next()` ist nicht in try/finally → bei Endpoint-Exception wird `Response.Body` nicht auf den Original-Stream zurückgesetzt (heute folgenlos – keine Error-Handling-Middleware); (c) 304 setzt kein `Cache-Control: private`/`Vary` → ab MVP-Auth + Reverse-Proxy Cross-User-Leak über Shared-Caches.
**Behebung:** (a) Größen-Cap oder Routen-/Content-Type-Whitelist; (b) `next()` in try/finally; (c) `Cache-Control: private`/`Vary` beim 304. Derzeit Survivor-/Scope-frei nicht umsetzbar.

---

## TD-S089-1 — Backend Coverage-Gate unter MTP nicht funktionsfähig (vorübergehend deaktiviert)
**Fällig:** jetzt – das Branch-Coverage-Gate aus NFR/DoD ist ohne Wirkung; terminiert in `docs/AGENT_MEMORY.md` (vor Beginn der nächsten Story), weil diese Datei nur situativ gelesen wird und ein passiver Trigger den Eintrag seit S089 nicht bewegt hat
**Problem:** Das Test-Projekt nutzt den Microsoft.Testing.Platform-Runner (xunit.v3). `coverlet.collector` (VSTest-DataCollector) ist darunter wirkungslos → der alte `dotnet-test.py` „bestand" das Gate über **veraltete** cobertura-Reports aus dem `/mnt/c`-Altrepo (Stale-Masking; erst durch den ext4-Umzug aufgedeckt). MTP-native Engines klemmen am gepinnten Stack: `Microsoft.Testing.Extensions.CodeCoverage` 18.3.2 und `coverlet.MTP` 8.0.1/10.0.1 → `TypeLoadException` (`TestHost.IDataConsumer`) gegen MTP 2.0.2.0/2.2.2.0; nur CodeCoverage 17.14.2 lief, scheiterte aber am `--coverage-settings`-Format. Gate daher in `dotnet-test.py` **explizit deaktiviert** (`collect_coverage = False`; kein Fake-100%, kein Hard-Block); Parser/Reporter + fail-closed-Logik bleiben re-enable-bereit.
**Stack-Stand hat sich seit S089 verschoben – die untenstehenden Wege zielen auf eine Konstellation, die nicht mehr vorliegt.** Aufgelöst ist laut `Server.Tests/obj/project.assets.json` heute `Microsoft.Testing.Platform` **1.9.1** (nicht 2.0.x/2.2.x), `xunit.v3` 3.2.2 in der **`mtp-v1`**-Variante (`xunit.v3.core.mtp-v1`), und `Microsoft.CodeCoverage` **18.3.0** liegt bereits transitiv über `Microsoft.NET.Test.Sdk` 18.3.0 vor. Die Recherche muss daher bei MTP 1.9 neu ansetzen; welche Coverage-Engine dort trägt, ist **offen und ungeprüft**.
**Behebung:** Coverage-Engine für den tatsächlichen MTP-1.9-Stack ermitteln, aufsetzen, dann `collect_coverage` in `dotnet-test.py` reaktivieren und 100% Branch-Coverage verifizieren. **Nicht erneut probieren** (bereits gescheitert, grenzt den Lösungsraum ein): `Microsoft.Testing.Extensions.CodeCoverage` 18.3.2 und `coverlet.MTP` 8.0.1/10.0.1 → `TypeLoadException`; CodeCoverage 17.14.2 lief, scheiterte am `--coverage-settings`-Format. Diese Versuche liefen gegen MTP 2.x – ob sie gegen den heutigen 1.9er-Stack anders ausgehen, ist ungeprüft.

---

## TD-S090-2 — Frontend: `matchKind` für Discriminated Unions noch nicht adoptiert
**Fällig:** Phase:MVP – das `QueryCache.onError`-Setup der `@NFR-resilience`-„Speichern/Laden"-Szenarien. Gemeinsam mit TD-S101-1 zu behandeln, aber **nicht** darauf verankert: beide hingen wechselseitig aneinander, während real beide an MVP hängen.
**Problem:** Drei Stellen lesen eine Discriminated Union per direktem `kind`-Vergleich statt über `matchKind` (ADR-S056-1): der Fehler-Union-Zugriff in `useCreateIngredientWithReactivation.ts:67` (`saveError?.kind === 'FieldErrors' ? …`) sowie zwei Erfolgs-Unions – `:21` (`ReactivationConflict`) und `ingredientsApi.ts:114` (`Restored`). **Kein formaler Guideline-Verstoß:** Die Guideline verbietet den direkten Zugriff unter „Verbotene Muster" ausdrücklich nur *in Komponenten*, und alle drei Stellen liegen in Hooks bzw. im Service-Layer. Es geht um Konsistenz mit dem Zielbild, nicht um eine verletzte Regel. Bewusst aufgeschoben (Code-Kommentar an der Stelle): Das kanonische Muster trennt Netzwerk/5xx (werfen → `QueryCache.onError`/Toast) von Domain-Fehlern (`matchKind`); `onError` existiert noch nicht, daher trägt `ApiError` aktuell den `Unexpected`-kind. `matchKind` jetzt über `FieldErrors|Unexpected` bräuchte eine Suppression auf dem ungetesteten `Unexpected`-Arm, den die resilience-Arbeit wieder entfernt (Churn).
**Behebung:** `QueryCache.onError` einführen → Netzwerk/5xx wirft dorthin, die Komponenten-Fehler-Union kollabiert auf Domain-Fehler-only (`FieldErrors`), dann `matchKind` mit einem voll getriebenen Arm (kein Survivor).

---

## TD-S090-3 — Backend: `IngredientValuesDto` non-nullable → fehlendes JSON-Property evtl. 400 statt 422
**Fällig:** Phase:MVP – primär, sobald ein **anderer Client als unser Frontend** das API nutzt (bis dahin strukturell unerreichbar); das ist kein maschinenlesbarer Anker, daher trägt der Backstop: spätestens mit dem öffentlich erreichbaren API ab MVP.
**Problem:** `IngredientValuesDto(string Name, string DefaultUnit)` ist non-nullable und wird von **zwei** Endpoints per Body gebunden: `POST /api/ingredients` und `POST /{id}/restore`. Lässt ein Client ein Property **ganz weg** (statt `""`), kann ASP.NET Minimal API je nach STJ-Konfiguration `null` binden (Warnung) oder **400** vor dem Handler werfen — nicht das vertragliche **422** mit `{"errors":{…}}`. Beide Client-Pfade werten den 400 nicht aus: `toIngredientResult` erkennt nur `status === 422`, `toRestoreOutcome` nur den `409`; ein 400 würde in beiden Fällen als Erfolg geparst → stiller Fehlzustand. Über unser eigenes Frontend nicht auslösbar, weil es beide Properties immer sendet.
**Behebung:** `string?`-Properties + bewusste Null-Behandlung in `ToDomain`, oder ein einheitlicher 4xx→`{"errors"}`-Mapper.

---

## TD-S101-1 — Frontend Hook: `useResultMutation` weicht von der kanonischen Wrapper-Form ab
**Fällig:** Phase:MVP – das `QueryCache.onError`-Setup der `@NFR-resilience`-Szenarien; erst dann ist `throwOnError` möglich und die Zustands-Union hat ausgeübte Zweige. Gemeinsam mit TD-S090-2, aber nicht darauf verankert (s. dort: wechselseitiger Verweis aufgelöst).
**Problem:** Der Hook liefert `[mutate, error, isPending, reset]`. Kanonisch nach `coding-guideline-typescript.md` §4b wäre `[mutate, MutationState<TData, TError>]` mit voller Zustands-Union. Die Abweichung ist bewusst; Entscheidung, Begründung und die bekannten Konsequenzen stehen in **ADR-S083-2**. Sie wächst mit jedem Addendum weiter (run-2 hängte `isPending` an, run-11 den `onSuccess`-Wert).
**Behebung:** Auf `[mutate, MutationState<TData, TError>]` umstellen; vorher entstünden Survivor und Suppressions außerhalb des treibenden Szenarios.

---

## TD-S102-1 — Backend: kein explizites app-weites Request-Body-Size-Limit
**Fällig:** Phase:MVP – vor MVP-Auth; spätestens sobald ein Endpoint authentifizierte oder größere Payloads annimmt.
**Problem:** `POST /api/ingredients` deserialisiert/bindet den vollständigen Request-Body, BEVOR die Feld-Validierung greift (`name.Value.Length > 30` läuft erst nach Model-Binding). Ein anonymer Client kann daher wiederholt große Bodies (bis Kestrels implizitem ~30-MB-Default, in `Program.cs` nirgends explizit gesetzt) senden → Parsing-/Trimming-Last vor jeder Ablehnung. Heute entschärft durch SKELETON ohne Auth und Kestrels impliziten Default; kein durch run-3 verschärftes Risiko – der Zustand ist ggü. vorher unverändert. (Die fehlende `defaultUnit`-Längenbegrenzung ist Teil von TD-S083-4, nicht hier.) Quelle: security-auditor (Review run-3, SR-2).
**Behebung:** Explizites app-weites `MaxRequestBodySize` in `Program.cs`, statt sich auf den impliziten Framework-Default zu verlassen.

---

## TD-S106-1 — Backend: kein globaler Exception-Handler / ProblemDetails-Fallback
**Fällig:** Phase:MVP – dort greift die tragende Anforderung (`docs/process/nfr.md`, Sektion Security: „Fehlerantworten enthalten keine technischen Details"). **Vorbedingung:** ein geklärtes Logging-Konzept (s. TD-S112-2); der Stack-Trace soll ins Log wandern, ein gestaltetes Log existiert noch nicht.
**Problem:** `Server/Program.cs` registriert keinen `app.UseExceptionHandler(...)` / kein `AddProblemDetails`. Eine unbehandelte Exception in irgendeinem Endpoint schlägt daher als roher 500 durch. DELETE war der erste Endpoint mit client-steuerbarem Input, der das sichtbar machte; der konkrete run-10-Pfad (malformed If-Match) ist mit `XminETag.TryParse` → 400 (ADR-S106-2) geschlossen, aber die systemische Verteidigungslinie fehlt weiterhin. Quelle: security-auditor (Review run-10, SEC-2).
**Reichweite präzisiert (an learn.microsoft.com verifiziert, Kommentar an der Stelle in `Server/Program.cs`):** Ohne Handler liefert Kestrel in Production einen **500 ohne Response-Body** – dort leakt nichts. Der Stack-Trace-Leak über die Developer-Exception-Page setzt `ASPNETCORE_ENVIRONMENT=Development` voraus, was ausschließlich `Server/Properties/launchSettings.json` beim lokalen Start setzt, nie ein Deployment. Zu korrigieren ist außerdem die frühere Begründung: Der NFR „keine Stack-Traces für User" (`nfr.md`, Reliability) ist eine **Frontend**-Anforderung – die UI zeigt nichts Technisches an – und trägt diesen Backend-Eintrag nicht.
**Behebung:** Unbedingte Registrierung von `UseExceptionHandler`, damit der Fehlerpfad keinen Umgebungs-Zweig mehr hat – Entscheidung, Begründung, Verworfenes und offene Punkte stehen in **ADR-S112-1**. Prüfbar als Backend-Integrationstest (`WebApplicationFactory`), nicht per E2E – die Eigenschaft ist an der Oberfläche nicht beobachtbar. Zieht `TD-S084-1(b)` (try/finally in der ETag-Middleware) unmittelbar nach sich.

---

## TD-S108-1 — Frontend Delete/Restore-Pfad: optimistischer Undo-Toast + kein Status-Check
**Fällig:** Phase:MVP – die `@NFR-resilience`-Szenarien und das dort mitzuschreibende **Delete-Fehler-Szenario**. Kein `Szenario:`-Anker möglich: Die vorhandenen Szenarien üben GET und POST aus, **nicht DELETE**; das treibende Szenario existiert noch nicht und ist in `docs/AGENT_MEMORY.md` als aufzunehmen vermerkt.
**Problem:** Zwei zusammenhängende Lücken im Löschen-/Undo-Pfad (`useDeleteIngredientWithUndo.ts`, `ingredientsApi.ts`):
(a) **Optimistischer Toast.** `requestDelete` setzt `deleted` **synchron vor** dem Mutation-Call – der Toast „X gelöscht" erscheint also, bevor der DELETE-Request überhaupt beantwortet ist, während die Liste erst nach Server-Antwort + `invalidateQueries` aktualisiert wird. Folgen: bei spürbarer Latenz zeigt die UI gleichzeitig „X gelöscht" **und** X unverändert in der Liste (inkl. klickbarem Löschen-Button); bei einem Netzwerkfehler bleibt eine **falsche Erfolgsmeldung** samt Undo-Button für eine Löschung stehen, die nie stattfand. Der Restore-Pfad macht es bereits richtig (`setDeleted(null)` + `onChanged()` gemeinsam im `onSuccess`).
(b) **Kein ausreichender Status-Check.** `deleteIngredient` wertet `response.status` **überhaupt nicht** aus (`ResultAsync.fromPromise(fetch(...))`) – ein 404/412/428 gilt als Erfolg. `restoreIngredient` wertet über `toRestoreOutcome` ausschließlich den `409` aus; jeder andere Status fällt in den Erfolgszweig und wird als `Ingredient` geparst. Bei einem `404` entsteht so ein `Restored`-Outcome mit einem ProblemDetails-Objekt als vermeintlicher Zutat, ohne dass irgendwo ein Fehler sichtbar würde. Der Restore-Endpoint kann zudem mit `422` antworten (Namenskollision mit einer anderen Zeile, ADR-S111-1-Addendum) – ein Statuscode, den der Client nicht kennt; über die aktuelle UI nicht auslösbar, weil pro LOWER-Name nur eine Zeile existieren kann, aber der Pfad besteht. Derselbe Defekt wie in TD-S083-1 für den GET-Pfad.
(c) **Undo kann wirkungslos verpuffen (Race).** Weil der Toast optimistisch erscheint, ist „Rückgängig" bereits klickbar, während der DELETE noch unterwegs ist. Trifft der `POST /restore` **vor** dem `SaveChangesAsync` des DELETE ein, findet der Restore die Zeile noch aktiv (`DeletedAt` ist noch `null`) → EF erkennt keine Änderung → kein UPDATE, kein xmin-Bump. Der danach eintreffende DELETE matcht seinen alten xmin weiterhin und committet normal. Endzustand: **Zutat bleibt gelöscht, obwohl der Nutzer „Rückgängig" geklickt hat** – ohne jede Fehlermeldung, der Toast verschwindet einfach. Das ist schärfer als (a): dort geht es um eine Anzeige-Inkonsistenz, hier um einen real verlorenen Undo. Praktisch selten (erfordert einen Klick innerhalb der DELETE-Roundtrip-Zeit), aber bei langsamer Verbindung erreichbar.
Alle drei Punkte sind im Erfolgsfall bei schnellem Netz unbeobachtbar – deshalb erzwingt kein Szenario sie heute. Quelle: ux-ui-auditor + functional-correctness-auditor (Review run-8, (a)/(b) unabhängig doppelt gefunden, (c) in Review-Runde 2).
**Zusammenhang:** TD-S110-1 beschreibt dieselbe Fehlerpfad-Lücke für den seit run-9 bestehenden `deletingId`-State und wird sinnvollerweise im selben Schritt mitbehoben.
**Behebung:** In einem Zug: `setDeleted` in den Erfolgs-Callback verschieben **und** die Fehler-Union für Delete/Restore einführen (dann trägt `ApiError` echte Domain-Kinds statt nur `Unexpected`, vgl. ADR-S056-1). Getrennt zu fixen lohnt nicht – (a) ohne (b) lässt einen 404 weiterhin als Erfolg durchgehen. Das Verschieben von `setDeleted` schließt (c) als Nebeneffekt mit: Ist der Undo-Button erst nach dem Delete-Erfolg klickbar, kann der Restore den DELETE nicht mehr überholen. Ohne das `QueryCache.onError`-Setup aus den resilience-Szenarien ist die Fehler-Union nicht sinnvoll.

---

## TD-S108-2 — Frontend: kein Fokus-Management nach Löschen und nach Undo
**Fällig:** US-602, Phase:V1 – erster Navigations-/Mehrseiten-Schritt; dann liegt ein realistischer Tab-Kontext zur Bewertung vor. Der Story-Anker gilt nur, solange US-602 keine Szenarien hat.
**Problem:** Nach dem Löschen einer Zutat unmountet das fokussierte Element (der Löschen-`IconButton` bzw. bei der letzten Zutat die ganze Liste), ohne dass der Fokus gezielt weitergeführt wird – der Browser setzt ihn auf `<body>` zurück. Dasselbe passiert nach einem Undo-Klick, wenn die Snackbar unmountet. Tastatur- und Screenreader-Nutzer müssen den „Rückgängig"-Weg danach per Tab suchen. Entschärfend: `SnackbarContent` setzt `role="alert"` (MUI-Default), die Meldung samt Undo-Möglichkeit wird also **angesagt**; MUI pausiert zudem den Auto-Hide-Timer, sobald der Button Fokus erhält – wer ihn erreicht, verliert die Zeit nicht. Heute sind es 1–2 Tab-Stopps, das wächst aber mit jeder weiteren Seite. Quelle: ux-ui-auditor (Review run-8, Runde 2).
**Früher noch als beim Unmount:** Weil der Löschen-Button während des laufenden DELETE `disabled` wird (`IngredientsPage.tsx`), verliert er den Fokus bereits **beim Disable** – also unmittelbar nach dem Tastendruck und **vor** jedem Ergebnis, nicht erst beim Unmount nach Abschluss. Ein `disabled`-Element kann den Fokus per HTML-Semantik nicht halten; der Browser setzt ihn auf `<body>`. Anders als im Anlege-Dialog fängt hier keine MUI-Fokusfalle den Rücksprung ab, weil die Liste kein Modal ist. Ein Tastatur-/Screenreader-Nutzer verliert damit die DOM-Orientierung, während die Aktion noch läuft. Quelle: ux-ui-auditor (Review run-9).
**Behebung:** Als bewusste Fokus-Strategie entscheiden, nicht als Schnellfix – die naheliegende Lösung (Autofokus auf „Rückgängig") hat echte Nebenwirkungen: Fokus-Stealing in ein selbstschließendes Element reißt den Nutzer aus dem Arbeitsfluss, und weil MUI bei Fokus den Timer pausiert, bliebe der Toast für Tastaturnutzer stehen, bis er aktiv weggedrückt wird. Strukturelle Nav-Vorgabe: UX-Guideline Prinzip 9.

---

## TD-S108-4 — Frontend: Undo-Toast auf Touch-Geräten nicht manuell schließbar
**Fällig:** Szenario:„Der Undo-Toast lässt sich manuell schließen", Phase:MVP – das Szenario existiert inzwischen (`features/interaction.feature`), ist aber keinem Lauf zugeordnet, daher der Phasen-Backstop. Ein rein reaktiver Auslöser („der nächste Lauf, der den Toast ohnehin verändert") ist ausdrücklich **nicht** ausreichend – er wurde bereits einmal übersehen, während der Toast-Bereich verändert wurde (LL-S111-2).
**Problem:** Seit der Undo-Toast `clickaway` bewusst ignoriert (damit ein beiläufiger Klick den einzigen Weg zurück nicht wegnimmt, `IngredientsPage.tsx`), bleiben als Schließ-Wege nur Timeout und Escape. Auf Touch-Geräten ist Escape praktisch nicht auslösbar und ein Schließen-Button existiert nicht – dort verschwindet der Toast ausschließlich nach Ablauf der 6 Sekunden. Kein Datenverlust und keine Blockade (die Snackbar ist nicht-blockierend), aber auf dem primären Zielgerät der App (Mobile-First) kann der Nutzer die Meldung nicht aktiv wegräumen. Quelle: functional-correctness-auditor (Review run-8).
**Schärfer beim zweiten Toast:** Der `ReactivationConflictToast` (ADR-S111-3) schließt zwar bei clickaway (kein Aktions-Button, der geschützt werden müsste), steht aber **10 Sekunden** statt 6 – bewusst so entkoppelt, weil der Text rund zehnmal so lang ist. Genau das Argument, das die längere Dauer rechtfertigt, verschärft die Lücke: MUIs Pause-bei-Hover greift auf Touch nicht, und auf dem primären Zielgerät bleibt die Meldung damit am längsten stehen, ohne dass der Nutzer sie aktiv wegräumen kann.
**Behebung:** Zusätzliche Schließen-Action (`CloseIcon`) neben „Rückgängig" – ein expliziter Button ist eine bewusste Geste und kollidiert nicht mit dem clickaway-Guard, der nur beiläufige Klicks abfängt. Weil es sichtbares Nutzerverhalten ist, muss ein Gherkin-Szenario davor liegen.

---

## TD-S110-1 — Frontend: Sperr-States im Löschen-/Undo-Pfad decken nur den Erfolgspfad ab
**Fällig:** TD-S108-1, Szenario:„Zwei gleichzeitige Löschvorgänge sperren beide Zeilen", Szenario:„Rückgängig ist während des Wiederherstellens deaktiviert", Phase:MVP – (a) und (b) mit TD-S108-1 (dessen Fehler-Union bringt den Fehler-Zweig ohnehin mit); (c) und (d) je mit ihrem Szenario, beide inzwischen in `features/interaction.feature` geschrieben, aber keinem Lauf zugeordnet. Alle spätestens ab MVP.
**Problem:** `useDeleteIngredientWithUndo.ts` führt seit run-9 einen `deletingId: string | null`-State, der die gerade löschende Zeile sperrt (`disabled={ingredient.id === deletingId}` in `IngredientsPage.tsx`). Er wird ausschließlich in `requestDelete` gesetzt und ausschließlich im `onSuccess` von `deleteMutate` zurückgesetzt. Daraus folgen drei Lücken – gemeinsam erfasst, weil sie denselben State, dieselbe Datei und denselben Fix-Ort betreffen:
(a) **Kein Reset im Fehlerpfad.** `useResultMutation`s `onSuccess` feuert nur bei `Ok`. Ein Netzwerkfehler (`Err`) lässt `deletingId` für immer stehen → der Löschen-Button dieser Zeile ist **dauerhaft** deaktiviert, ohne Fehlermeldung und ohne Retry-Weg; nur ein Reload hilft. Quelle: ux-ui-auditor (Review run-9).
(b) **Kein Reset im Restore-Pfad.** `restoreMutate`s `onSuccess` setzt `deleted` zurück, aber nicht `deletingId`. Klickt der Nutzer „Rückgängig", während der DELETE noch läuft (das Fenster aus TD-S108-1(c)), erscheint die Zeile durch das Refetch wieder – mit weiterhin gesperrtem Löschen-Button und ohne Toast, also ohne jeden sichtbaren Grund für die Sperre. Quelle: functional-correctness-auditor (Review run-9). **Hinweis:** Die in TD-S108-1 beschriebene Behebung (`setDeleted` in den Erfolgs-Callback verschieben) schließt dieses Fenster als Nebeneffekt mit, weil „Rückgängig" dann erst klickbar ist, wenn `deletingId` bereits `null` ist – beim Umsetzen von TD-S108-1 verifizieren, statt es separat zu fixen.
(c) **Skalar statt Menge.** Bei zwei überlappenden Löschvorgängen überschreibt der zweite `deletingId`; die erste Zeile wird wieder klickbar, obwohl ihr DELETE noch aussteht – ein zweiter DELETE auf dieselbe Zeile ist dann auslösbar. Quelle: ux-ui-auditor (Review run-9).
(d) **Kein Pending-Guard am „Rückgängig"-Button.** `deletingId` sperrt die Zeile während des DELETE; für den umgekehrten Weg gibt es nichts Vergleichbares – der „Rückgängig"-Button bleibt klickbar, während sein Restore noch läuft. Zwei schnelle Klicks lösen zwei parallele Restores derselben Zeile aus. Serverseitig sauber abgefangen (identische Werte → `200`, der Verlierer eines echten Races → `200`/`409` statt `500`, s. ADR-S111-1-Addendum), es entsteht also kein Datenschaden – die Lücke ist rein UI-seitig: eine laufende Aktion ohne sichtbare Rückmeldung, erneut auslösbar. Eine Button-Sperre ist sichtbares Nutzerverhalten und braucht ein eigenes Gherkin-Szenario. Quelle: functional-correctness-auditor (Review run-11).
Keine der vier Lücken ist heute durch ein Szenario beobachtbar: Das treibende Szenario ist ein Singleton-Happy-Path („nur Mehl existiert"), Fehlerpfade sind ihm bewusst entzogen; für (d) fehlt das Szenario, das die Sperre überhaupt fordert.
**Behebung:** (a) und (b) gemeinsam mit TD-S108-1: `deletingId` im Fehler-Zweig und im Restore-`onSuccess` mit zurücksetzen. (c) auf `ReadonlySet<string>` umstellen, (d) analog zu `deletingId` als Pending-Flag im selben Hook – beides erst **nach** dem jeweiligen Szenario: vorab umgesetzt entstünde ein Zweig, den kein Szenario ausübt → Stryker-Survivor → Suppression außerhalb des treibenden Szenarios, genau die Konstellation, die ADR-S083-2 vermeiden will.

---

## TD-S112-1 — Konfigurations-Parität E2E↔Produktion und Umgebungs-Allow-Liste nicht umgesetzt
**Fällig:** TD-S106-1, Phase:MVP – gemeinsam mit TD-S106-1: (c) hängt an (b), und der Wächter ist ohne den Exception-Handler gegenstandslos.
**Problem:** ADR-S112-2 ist entschieden, aber nichts davon existiert im Code: (a) kein Test, der die Schlüssel umgebungsspezifischer `appsettings.*.json` gegen eine Allow-Liste prüft – heute hält allein Disziplin `appsettings.E2E.json` auf den Connection-String beschränkt; (b) keine Umgebungs-Allow-Liste beim App-Start – die App läuft unter jedem beliebigen `ASPNETCORE_ENVIRONMENT` an; (c) folglich auch keine Liste, aus der der Umgebungs-Regressionswächter aus ADR-S112-1 seine Aufzählung ziehen könnte.
**Behebung:** (a)–(c) nach ADR-S112-2 umsetzen. Beim Umsetzen verifizieren, dass der Startup-Guard die werkzeuggebauten Hosts (`dotnet ef`, `WebApplicationFactory`) nicht bricht.

---

## TD-S112-2 — Observability-Anforderung ohne Umsetzung: Backend loggt nirgends aktiv
**Fällig:** TD-S106-1, Phase:MVP – die Anforderung selbst gilt bereits, ungeprüft ist allein, ob der Framework-Default sie schon erfüllt; die Prüfung ist deshalb Teil der Behebung, keine offene Verletzung.
**Problem:** Die Anforderung steht seit S112 in `docs/process/nfr.md` (Sektion Observability), im Code existiert davon nichts: `Server/appsettings.json` hat keine `Logging`-Sektion, und in `Server/` wie `Infrastructure/` gibt es keine einzige `ILogger`-Nutzung. Vorhanden ist allein der Framework-Default (Console-/Debug-Provider aus `WebApplication.CreateBuilder`). Für die Kernzusicherung – unbehandelte Exceptions landen mit Stack-Trace im Log – reicht das vermutlich bereits aus, weil die Hosting-Schicht unbehandelte Exceptions selbst auf Error-Level protokolliert; **verifiziert ist das nicht**.
**Behebung:** Empirisch prüfen, ob eine unbehandelte Exception tatsächlich mit Stack-Trace auf stdout landet, und die Zusicherung mit einem Test festnageln. Nur falls die Prüfung eine Lücke zeigt, explizite Logging-Konfiguration ergänzen – nicht vorsorglich.

---

## TD-S118-1 — `Ingredient`: rohe `Guid`-Id, und `ToDomain()` erzeugt eine Wegwerf-Id
**Fällig:** jetzt – verletzt eine heute geltende Regel (`architecture.md` Kernprinzip 1 nennt `Guid` namentlich, `coding-guideline-csharp.md` §2 nennt `ItemId` als Beispiel). Kosten und Nutzen wachsen beide mit jeder weiteren Entität; der zweite Befund ist ohne den ersten nicht sichtbar.
**Problem:** Zwei Befunde in `Server/Domain/Ingredient.cs` und `Server/Endpoints/IngredientsEndpoints.cs`, beide auf dieselbe fehlende Modellierung zurückgehend.
(a) `Ingredient` trägt die Id als rohes `Guid`, während `Name` und `DefaultUnit` gekapselt sind – die Id ist das einzige Feld, das den Sprung in einen Domänentyp nie mitgemacht hat.
(b) Schwerwiegender: `IngredientsEndpoints.cs:135` erzeugt in `ToDomain()` per `Guid.CreateVersion7()` eine **Wegwerf-Id**, weil `Ingredient.Create` eine verlangt – obwohl an diesem Punkt noch keine Identität existiert (ADR-S030-1: serverseitig vergeben). Der Restore-Pfad dokumentiert das ausdrücklich (`:240`: „die dabei … erzeugte Id … wird nie gelesen"). Ein illegaler Zustand wird routinemäßig erzeugt und verworfen; `Guid.Empty` dient dabei in-band als Sentinel für „keine Identität" (`Ingredient.cs:13`).
**Behebung:** Entscheidung und Begründung stehen in `docs/history/sessions/session_118.md`, Abschnitt E3. Kurzfassung: Constraint-Typ `Uuid7` in `Server/Types/` (UUIDv7-Prädikat nach ADR-S030-1, subsumiert die `Guid.Empty`-Prüfung; `Create → OneOf`, `implicit operator Guid` heraus; `default(T)`-Guard nach dem Muster von `NonEmptyTrimmedString`, ADR-S041-9). Darüber `IngredientId` in `Server/Domain/` als Union `Known`/`Unknown` – Optionalität out-of-band statt als Sonderwert. Nur die Domäne umbauen: DTO, DbType und Route-Parameter bleiben `Guid` (`coding-guideline-csharp.md` §57/§157–158 begrenzen die Regel auf Geschäftsmodelle; die Grenze bleibt damit verlustfrei und ohne Converter). Tote `Unknown`-Arme an Lesestellen über `SumType.Unreachable<T>()` (ADR-S040-1, Suppression via ADR-S018-2). Die UUIDv7-Prüfung im **Lesepfad aus der DB** führt einen Fehlerzweig ein, den es heute nicht gibt – sie gehört deshalb an das DB-Inkonsistenz-Szenario, nicht in diesen Eintrag. Als Ausweichweg dokumentiert, falls die `Unreachable`-Arme stören: `IngredientValues` (Value Object) + `Ingredient(IngredientId, IngredientValues)`, analog zum bereits existierenden `IngredientValuesDto` und den Frontend-Typen aus ADR-S112-4.

---

## TD-S118-2 — `Ingredient`: Constraint-Typen statt Domänentypen für `Name` und `DefaultUnit`
**Fällig:** jetzt – verletzt `architecture.md` Kernprinzip 1 („jedes Domänen-Konzept bekommt einen eigenen Typ, der seine Invarianten selbst durchsetzt"). Vor TD-S118-1 zu klären, weil beide dieselben Signaturen anfassen.
**Problem:** `Name` und `DefaultUnit` sind `NonEmptyTrimmedString` – ein **Constraint-Typ** (Prädikat über einem Primitive, feldagnostisch, `Server/Types/`), kein Domänenkonzept. Zwei Folgen: (a) Die Feldregeln liegen im Endpoint (`IngredientsEndpoints.cs:117/119`, `MaxNameLength = 30`, `MaxUnitLength = 20`), nicht im Typ – `Ingredient.Create` akzeptiert einen 500-Zeichen-Namen, und dass das nicht passiert, hält allein der eine Aufrufer `ToDomain()`. Die Zusicherung aus `architecture.md` Kernprinzip 1 („ein Wert, der diesen Typ hat, ist garantiert gültig") trägt hier nicht der Typ, sondern Aufrufer-Disziplin. (b) Beide Parameter sind typgleich und damit vertauschbar. `Quantity` (ADR-S020-1) zeigt, dass die Ebene im Projekt bekannt ist; bei `Ingredient` wurde sie nicht gezogen. Undokumentierte Abweichung – `architecture.md` 0b verlangt für Abweichungen einen ADR-Eintrag, es gibt keinen.
**Behebung:** Zuerst das Prinzip festschreiben (`coding-guideline-csharp.md` §2 + Verweis aus `architecture.md`), dann `Ingredient` daran anpassen. Prinzip und Begründung: `docs/history/sessions/session_118.md`, Abschnitt E2 – der Domänentyp ist die stabile Schnittstelle, der Constraint-Typ die austauschbare Implementierung; Rolle ≠ Typ; Verwechslungsschutz ist Nebenprodukt, kein Entwurfsziel; Abwesenheit ist keine Einschränkung; Regeln in den Typ, Meldungen an die Grenze (ADR-S051-2 bleibt unberührt). Konkret: `IngredientName` und **`Unit`** – geteilt, nicht `IngredientUnit`, weil Rezept und Einkaufsliste dasselbe Konzept verwenden werden. `MaxNameLength`/`MaxUnitLength` wandern in die Typen. Zusätzlich das Guideline-Beispiel `coding-guideline-csharp.md:216` korrigieren, das mit `Create(Guid id, …)` §2 und §68 derselben Datei widerspricht (gleiches Muster wie ADR-S112-4).
