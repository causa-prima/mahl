# Technische Schuld

<!--
wann-lesen: Wenn der zu bearbeitende Code einen der Bereiche unten berührt (z.B. Architektur-Check
            in implementing-scenario) sowie beim Session-Abschluss (closing-session, nfr.md).
wann-schreiben: Sobald eine bewusst aufgeschobene Schuld entsteht (⚠️-Finding nicht sofort gefixt,
            bewusste Vereinfachung, vertagte Härtung).
aufnahmebedingung: Hier steht eine **entschiedene** Sache am Produkt (Code + Build-/Test-Kette),
            die mit ihrer Behebung **ersatzlos verschwindet** – nichts bleibt zu erklären übrig.
            Operativer Test (Kurzfassung; kanonischer Wortlaut in `AGENTS.md`): „Ist die Sache
            erledigt – bleibt dann etwas zu erklären übrig?"
            Nein → hierher (der Eintrag wird gelöscht). Ja → `docs/history/adr.md` (bleibt als
            `Superseded` stehen). Noch nicht entschieden → `docs/open-questions.md`. Hierher
            gehört auch der **Aufschub-Teil** einer Entscheidung, deren terminaler Rest als ADR
            abgelegt ist – eine ADR trägt keinen Aufschub. Abgrenzung ADR/TD/OQ kanonisch:
            [„Ablage: in welchen Tracker gehört dieser Eintrag?"](../AGENTS.md#CLA-ablage)

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen (kein Umsortieren).

Eintrag-Format:
  ## TD-S<NNN>-<n> — <Bereich/Kurztitel>
  **Fällig:** <Anker>[, <Anker>…] – <Freitext-Erläuterung>
  **Problem:** <was ist die Schuld>
  **Behebung:** <wie behoben wird>
  **Aufschubgrund:** User | Recherche – <warum erfasst statt sofort behoben>
            (Pflicht für neue Einträge seit S133; trifft keiner der Werte zu, wird behoben
             statt erfasst. Bedeutung der Werte: `prozesscode/eintrag_felder.py`)

  ID: TD-S<NNN>-<n> – 3-stellige Session (Ursprung), laufende Nummer innerhalb der Session.
  Freie fettgesetzte Absätze (`**Zusammenhang:**`, `**Reichweite präzisiert:**` …) sind erlaubt,
  die Felder oben sind Pflicht.

Regeln zum Feld `**Fällig:**` (mechanisch geprüft von `prozesscode/hooks/check-td-capture.py`,
Grammatik und Auflösung kanonisch in `prozesscode/td_anchors.py`):

  1. Pflicht. Ein Eintrag, der nur sagt, WIE behoben wird, schuldet niemandem einen Zeitpunkt.

  2. Der **Kopf** vor dem Gedankenstrich ist maschinenlesbar, der Rest bleibt Prosa und trägt
     weiter die Nuance. Anker-Vokabular:

       jetzt              sofort
       Phase:MVP          Phasenwechsel (auch V1/V2) – tritt ein, wenn AGENT_MEMORY sie erreicht
       S130               Spätestens-Termin (Session-Nummer)
       Szenario:„…"       ein Gherkin-Szenario aus features/ (Titel exakt, muss existieren) –
                          erscheint, sobald sein Lauf der nächste ist, unter „Nächster Lauf"
                          als „Teil dieses Laufs"
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
     das eine Entscheidung über die Regel: Regel ändern, oder die Abweichung als **dauerhafte**
     Ausnahme per ADR festschreiben. Im zweiten Fall ist die Sache entschieden und dieser
     Eintrag **entfällt** – es gibt dann keine Schuld mehr, nur eine begründete Ausnahme.
     Was es nicht gibt: eine ADR, die dem Eintrag lediglich erlaubt zu warten. Das ist der
     Hybrid, den die Ablage-Taxonomie ausschließt ([„Ablage: in welchen Tracker gehört dieser
     Eintrag?"](../AGENTS.md#CLA-ablage)): Der Aufschub gehört hierher, die ADR behält nur den terminalen Rest.
     Ein ungeprüfter Verdacht ist keine Verletzung – dann ist die Prüfung die Behebung und
     bekommt eine eigene Fälligkeit.

  6. **Story-Anker umhängen, sobald die Story Szenarien hat.** Vor dem `gherkin-workshop` ist
     `US-NNN` die feinste verfügbare Granularität; danach steht fest, zu welchem Szenario die
     Schuld gehört – oder die ehrliche Antwort ist `jetzt` (vor Implementierungsbeginn zu
     erledigen). Der Übergang wird nicht vom `gherkin-workshop` erzwungen (der soll ohne Wissen
     über TD-Tracking funktionieren), sondern vom `td-due`-Modul der `session-agenda.py`: Es
     meldet jeden Story-Anker, dessen Story inzwischen Szenarien trägt.
-->

## TD-S044-1 — STJ/Deserialisierung
**Fällig:** Phase:V1 – URI-Felder. US-602 trägt keine (die Quell-URL gehört nicht zum Scope seiner Szenarien).
**Problem:** 400 vs. 500 bei ungültigem URI; STJ via `OriginalString` unverifiziert.
**Behebung:** STJ-Pfad verifizieren und 400 statt 500 erzwingen.

## TD-S080-1 — Frontend Deps: `qs`-DoS (dev-only, akzeptiert)
**Fällig:** Phase:MVP – primär der nächste Stryker-Major-Bump; ein Dependency-Bump ist kein maschinenlesbarer Anker, deshalb trägt hier der Backstop: ab MVP neu bewerten, falls der Bump bis dahin ausbleibt.
**Problem:** `qs`-DoS (moderate) via `@stryker-mutator/core`→`typed-rest-client`→`qs` – dev-only, kein untrusted-Input-Pfad, akzeptiert. Auch Stryker 10 pinnt `typed-rest-client ~2.3.0`, das `qs` exakt auf 6.15.1 festlegt; ein `overrides` in `package.json` wäre möglich, lohnt bei fehlender Angriffsfläche aber nicht.
**Behebung:** Entfällt mit dem Bump von selbst; bis dahin bewusst getragen.

---

## TD-S083-1 — Frontend GET-Pfad: kein `response.ok`-Check, Err wird verschluckt
**Fällig:** Szenario:„Backend nicht erreichbar beim Laden einer Seite", Szenario:„Backend liefert Serverfehler beim Laden einer Seite", Phase:MVP – die beiden `@NFR-resilience`-„Laden"-Szenarien existieren, sind aber keinem Lauf zugeordnet; daher der Phasen-Backstop.
**Problem:** Zwei Lücken im GET-Pfad (der POST/Mutation-Pfad ist davon nicht betroffen):
(a) **Kein `response.ok`-Check.** `conditionalGet.ts` parst die Antwort unbedingt – ein 4xx/5xx-Body wird als Erfolg geparst und als Daten zurückgegeben (ausgenommen 404, das als `NotFound` abgefangen wird). Nicht gecacht: `cache200` schreibt nur bei vorhandenem ETag-Header, und `ETagMiddleware` setzt den ausschließlich bei Status 200. Zusätzlich `cached!` im 304-Pfad (YAGNI). Auf der Rezept-Detailansicht wird ein 5xx-Body mit JSON (z. B. ProblemDetails) so zu „Found" und die Seite stürzt an `recipe.ingredients.map` ab, statt still leer zu bleiben.
(b) **`useResultQuery` schluckt den `Err`** via `unwrapOr(undefined as TData)` (Type-Lie) → ein GET-Fehler ist nicht von „noch keine Daten"/Leerzustand unterscheidbar. Folge auch mitten in einer Sitzung: Scheitert nach einem erfolgreichen Vormerken das Neuladen der Vormerkungen, verschwinden die Umschalter „Vormerken" in Rezept-Liste und Detailansicht.
**Behebung:** GET-Fehlerpfad einführen: `response.ok`-Check in `conditionalGet`, GET-Err in `useResultQuery` als beobachtbaren Fehlerzustand statt Leerzustand.

## TD-S083-3 — Frontend: Cold-Start-Race beim ersten GET
**Fällig:** TD-S083-1 – Query-Zustand in `useResultQuery` (heutige Minimal-Form: TD-S101-1); vorher technisch nicht umsetzbar.
**Problem:** Feuert der POST/`invalidateQueries`, während der initiale Listen-GET noch in-flight ist, koalesziert react-query und nutzt das stale leere Ergebnis (kein zweiter GET) → gerade angelegte Zutat erscheint nicht. Nur bei kaltem Server / langsamem erstem GET (warm: unkritisch). **Vorher nicht umsetzbar:** `useResultQuery` liefert ausschließlich `TData | undefined` und exponiert keinerlei Lade-/Fehlerzustand – die Seite *kann* nicht wissen, ob der initiale GET gesettled ist.
**Behebung:** Speichern sperren, solange die Ingredients-Query nicht gesettled ist. **Achtung:** Das vorhandene `disabled={isPending}` löst das nicht – dessen `isPending` stammt aus `useCreateIngredientWithReactivation` und ist der Zustand der *POST-Mutation*, greift also erst, nachdem der POST bereits feuerte.

## TD-S083-5 — Backend Read-Pfade: Zutaten, Rezepte und Vormerkungen mappen DB→DTO direkt, ohne `ToDomain()`
**Fällig:** Phase:MVP – der tragende Auslöser ist ein dediziertes DB-Inkonsistenz-Szenario, das den Fehlerzweig erstmals ausübt; es existiert in `features/` noch nicht und lässt sich deshalb nicht als Anker setzen. Vorher umzubauen erzeugt einen Zweig, den kein Szenario ausübt → Survivor → Suppression außerhalb des treibenden Szenarios. Spätestens zum MVP muss der Read-Pfad stimmen.
**Problem:** Die Lesepfade projizieren DB-Zeilen **direkt** auf DTOs, statt den kanonischen Read-Pfad `DbType → ToDomain() → OneOf<Domain, Error<string>> → DTO` zu gehen ([SKELETON-Scope-Constraints](reference/architecture.md#ARC-skeleton-constraints), [Domain-Typen](guidelines/coding-guideline-csharp.md#CGC-domain-typen)): `GET /api/ingredients` (`db.Ingredients.Select(i => new IngredientDto(…))`), `GET /api/recipes` (`Select(r => new RecipeSummaryDto(r.Id, r.Title))`), `GET /api/recipes/{id}` (`RecipeMappings.GetRecipe`: Rezeptzeile, Zutatenzeilen per Join und Schritte direkt aufs `RecipeDto`) und `GET /api/planned-recipes` (Join der Vormerkungen auf die Rezepte, direkt aufs `RecipeSummaryDto`). Weder `ToDomain()` noch das Skip-/Log- bzw. 500-Verhalten für korrupte DB-Zeilen existieren auf diesen Pfaden. Die Domäne sieht die DB-Daten also nicht – ihre Zusicherung „ein Wert dieses Typs ist garantiert gültig" trägt hier nicht. Dieselbe Abweichung zusätzlich im Restore-Pfad in `IngredientsEndpoints.cs` (dort mit eigener Begründung, ADR-S108-1).
**Behebung:** Read-Pfade auf `ToDomain()` umstellen (Skip+Log bei Listen, 500 bei Einzel-Ressource), für Rezepte zusammen mit TD-S141-3 (Zutat-Id ungeprüft). Die Zielsemantik ist für Recipes bereits entschieden – ADR-S039-3: 500 + `application/problem+json` bei korrupter DB-Zeile, kein silent `null`. Das [kanonische Beispiel](guidelines/coding-guideline-csharp.md#CGC-kanonisches-beispiel) zeigt die Zielform inklusive Fehlersammlung.
**Herkunft:** War bis S119 als ADR-S083-1 abgelegt. Umgehängt, weil der Eintrag ein Hybrid ohne terminalen Rest ist: Ist der Read-Pfad umgestellt, gibt es keine Abweichung mehr, die zu erklären wäre – der Eintrag verschwindet ersatzlos. Was terminal ist (Zielsemantik bei korrupter DB), steht schon in ADR-S039-3; ADR-S083-1 trug nur den Aufschub, und den trägt eine ADR nicht.

---

## TD-S084-1 — HTTP/ETag-Middleware (BE): vollständige Response-Pufferung
**Fällig:** TD-S106-1, Phase:MVP – (a) vor File-/Image-Serving bzw. paginierungsfreien Collections; (b) mit TD-S106-1 (Error-Handling-Middleware); (c) vor MVP-Auth + Reverse-Proxy. Alle drei spätestens ab MVP.
**Problem:** `ETagMiddleware` puffert **jede** GET-Response komplett in einen `MemoryStream` (+`ToArray()`-Kopie) → (a) DoS-/Speicher-Risiko sobald große/paginierungsfreie Collections oder File-/Image-GETs dazukommen (Buffering+Hash zwingt Nicht-Streaming); (b) `next()` ist nicht in try/finally → bei Endpoint-Exception wird `Response.Body` nicht auf den Original-Stream zurückgesetzt (heute folgenlos – keine Error-Handling-Middleware); (c) 304 setzt kein `Cache-Control: private`/`Vary` → ab MVP-Auth + Reverse-Proxy Cross-User-Leak über Shared-Caches.
**Behebung:** (a) Größen-Cap oder Routen-/Content-Type-Whitelist; (b) `next()` in try/finally; (c) `Cache-Control: private`/`Vary` beim 304. Derzeit Survivor-/Scope-frei nicht umsetzbar.

## TD-S090-2 — Frontend: `matchKind` für Discriminated Unions noch nicht adoptiert
**Fällig:** Phase:MVP – das `QueryCache.onError`-Setup der `@NFR-resilience`-„Speichern/Laden"-Szenarien. Gemeinsam mit TD-S101-1 zu behandeln, aber **nicht** darauf verankert: beide hingen wechselseitig aneinander, während real beide an MVP hängen.
**Problem:** Drei Stellen lesen eine Discriminated Union per direktem `kind`-Vergleich statt über `matchKind` (ADR-S056-1): der Fehler-Union-Zugriff in `useCreateIngredientWithReactivation.ts:67` (`saveError?.kind === 'FieldErrors' ? …`) sowie zwei Erfolgs-Unions – `:21` (`ReactivationConflict`) und `ingredientsApi.ts:114` (`Restored`). **Kein formaler Guideline-Verstoß:** Die Guideline verbietet den direkten Zugriff unter „Verbotene Muster" ausdrücklich nur *in Komponenten*, und alle drei Stellen liegen in Hooks bzw. im Service-Layer. Es geht um Konsistenz mit dem Zielbild, nicht um eine verletzte Regel. Bewusst aufgeschoben (Code-Kommentar an der Stelle): Das kanonische Muster trennt Netzwerk/5xx (werfen → `QueryCache.onError`/Toast) von Domain-Fehlern (`matchKind`); `onError` existiert noch nicht, daher trägt `ApiError` aktuell den `Unexpected`-kind. `matchKind` jetzt über `FieldErrors|Unexpected` bräuchte eine Suppression auf dem ungetesteten `Unexpected`-Arm, den die resilience-Arbeit wieder entfernt (Churn).
**Behebung:** `QueryCache.onError` einführen → Netzwerk/5xx wirft dorthin, die Komponenten-Fehler-Union kollabiert auf Domain-Fehler-only (`FieldErrors`), dann `matchKind` mit einem voll getriebenen Arm (kein Survivor).

---

## TD-S090-3 — Backend: `IngredientValuesDto` non-nullable → fehlendes JSON-Property evtl. 400 statt 422
**Fällig:** Phase:MVP – primär, sobald ein **anderer Client als unser Frontend** das API nutzt (bis dahin strukturell unerreichbar); das ist kein maschinenlesbarer Anker, daher trägt der Backstop: spätestens mit dem öffentlich erreichbaren API ab MVP.
**Problem:** `IngredientValuesDto(string Name, string BaseUnit)` ist non-nullable und wird von **zwei** Endpoints per Body gebunden: `POST /api/ingredients` und `POST /{id}/restore`. Lässt ein Client ein Property **ganz weg** (statt `""`), kann ASP.NET Minimal API je nach STJ-Konfiguration `null` binden (Warnung) oder **400** vor dem Handler werfen — nicht das vertragliche **422** mit `{"errors":{…}}`. Beide Client-Pfade werten den 400 nicht aus: `toIngredientResult` erkennt nur `status === 422`, `toRestoreOutcome` nur den `409`; ein 400 würde in beiden Fällen als Erfolg geparst → stiller Fehlzustand. Über unser eigenes Frontend nicht auslösbar, weil es beide Properties immer sendet.
**Behebung:** `string?`-Properties + bewusste Null-Behandlung in `ToValues`, oder ein einheitlicher 4xx→`{"errors"}`-Mapper.

**Nachtrag S120 – zwei Beobachtungslücken derselben Klasse, beide über unser Frontend nicht auslösbar:**
1. **`null` als Feldwert ist ungetestet.** Die Constraint-/Domänentypen behandeln ihn korrekt (`input?.Trim()` → `Empty` → 422), aber kein Test pinnt das, und Stryker mutiert `?.` nicht — der Operator ist die einzige Absicherung gegen einen 500er, und kein Gate schlägt an, wenn er verschwindet. Die `Create`-Signaturen tragen seit S120 `string?`, damit Vertrag und Implementierung übereinstimmen; der Test fehlt weiterhin.
2. **„422 dominiert vor 404" beim Restore ist ungetestet.** Der Kommentar an `RestoreIngredient` sagt zu, dass ein ungültiger Body auch für eine nicht existierende Id mit 422 beantwortet wird (Validierung läuft vor dem Lookup). Getestet sind nur die Einzelachsen — nicht existierende Id mit *gültigem* Body, existierende Id mit *ungültigem* Body. Dreht jemand die Reihenfolge um, bleiben beide grün und die Kombination liefert 404.

Beide Tests gehören zu dieser Behebung: Sie werden sinnvoll, sobald ein fremder Client das API erreicht — vorher gibt es keinen Weg, sie auszulösen. Aufgedeckt vom `functional-correctness-auditor` im S120-Review.

---

## TD-S101-1 — Frontend Hook: `useResultMutation` weicht von der kanonischen Wrapper-Form ab
**Fällig:** Phase:MVP – das `QueryCache.onError`-Setup der `@NFR-resilience`-Szenarien; erst dann ist `throwOnError` möglich und die Zustands-Union hat ausgeübte Zweige. Gemeinsam mit TD-S090-2, aber nicht darauf verankert (s. dort: wechselseitiger Verweis aufgelöst).
**Problem:** Der Hook liefert `[mutate, error, isPending, reset]`. Kanonisch nach [React Query](guidelines/coding-guideline-typescript.md#CGT-react-query) und ADR-S056-1 wäre `[mutate, MutationState<TData, TError>]` mit voller Zustands-Union (`idle|pending|success|error`) plus `matchState()`/`matchKind()` und `throwOnError: true`. Betroffen sind beide Wrapper in `Client/src/hooks/`: `useResultQuery` liefert `TData | undefined` (nur success-Zweig), `useResultMutation` das Tupel oben. Die Abweichung ist bewusst und stammt aus dem US-904-Happy-Path „Zutat anlegen" (S083), der nur den success-Pfad ausübt.

**Bekannte Konsequenzen, solange die Schuld steht:** (1) Name-Kollision mit den kanonischen Wrappern – ein Leser der Guideline erwartet das `MutationState`-Tupel. (2) `onSuccess` feuert auch bei einem `Err`-Result, da `Promise.resolve(ResultAsync)` den `Err` nicht wirft – im success-only-Pfad harmlos, aber vor dem Error-Szenario auf `result.match(onSuccess, onError)` umzustellen. (3) Fehlendes `throwOnError` → bei Netzwerkfehler bliebe `query.data` undefined und der Empty-State würde fälschlich gerendert.

**Bereits eingelöste Teile** (die Schuld schrumpft schrittweise, statt am Stück behoben zu werden): `isPending` kam mit run-2 („Speichern-Button deaktiviert während des Speicherns") dazu; `onSuccess` reicht seit run-11 („Reaktivierung") den Erfolgswert durch, statt ihn zu verschlucken (getrieben von ADR-S111-3, das den gespeicherten Stand für die Snackbar braucht). Beides ohne neue Zustände oder Union.

**Behebung:** Auf `[mutate, MutationState<TData, TError>]` umstellen, samt `matchState` und `throwOnError`. Vorher entstünden unausgeübte `idle`/`error`-Zweige → Survivor → Suppressions außerhalb des treibenden Szenarios. `throwOnError` setzt zusätzlich `QueryCache.onError` voraus (existiert noch nicht) – deshalb die Kopplung an die `@NFR-resilience`-Szenarien im Fälligkeitsanker oben.
**Herkunft:** Entscheidung, Begründung und Konsequenzen standen bis S119 als ADR-S083-2 in `docs/history/adr.md` und sind hier aufgegangen. Umgehängt, weil der Eintrag ein Hybrid ohne terminalen Rest war: Ist der Hook auf die kanonische Form umgestellt, gibt es keine Abweichung mehr zu erklären – der Eintrag verschwindet ersatzlos. Die kanonische Form selbst ist in ADR-S056-1 und [React Query](guidelines/coding-guideline-typescript.md#CGT-react-query) verankert, nicht hier.

---

## TD-S102-1 — Backend: kein explizites app-weites Request-Body-Size-Limit
**Fällig:** Phase:MVP – vor MVP-Auth; spätestens sobald ein Endpoint authentifizierte oder größere Payloads annimmt.
**Problem:** `POST /api/ingredients` deserialisiert/bindet den vollständigen Request-Body, BEVOR die Feld-Validierung greift (`name.Value.Length > 30` läuft erst nach Model-Binding). Ein anonymer Client kann daher wiederholt große Bodies (bis Kestrels implizitem ~30-MB-Default, in `Program.cs` nirgends explizit gesetzt) senden → Parsing-/Trimming-Last vor jeder Ablehnung. Heute entschärft durch SKELETON ohne Auth und Kestrels impliziten Default; kein durch run-3 verschärftes Risiko – der Zustand ist ggü. vorher unverändert. Quelle: security-auditor (Review run-3, SR-2). Verschärft seit S147 (CROSS-text/run-1): Die Normalisierung im geteilten Texttyp (`NonEmptyNormalizedString.Normalize`, ADR-S135-1) kopiert den Rohwert mehrfach (Filtern, Falten, Split/Join, NFC), bevor die Längengrenze greift – statt einer Kopie durch `Trim()` (abgeleitet aus dem Code, nicht gemessen; Quelle: security-auditor S147, SEC-5).
**Behebung:** Explizites app-weites `MaxRequestBodySize` in `Program.cs`, statt sich auf den impliziten Framework-Default zu verlassen. Zusätzlich prüfen, ob `NonEmptyNormalizedString` vor dem Normalisieren eine Obergrenze für die Rohlänge braucht (z. B. ein Vielfaches der größten Feldgrenze).

---

## TD-S106-1 — Backend: kein globaler Exception-Handler / ProblemDetails-Fallback
**Fällig:** Phase:MVP – dort greift die tragende Anforderung (`docs/process/nfr.md`, Sektion Security: „Fehlerantworten enthalten keine technischen Details"). **Vorbedingung:** ein geklärtes Logging-Konzept (s. TD-S112-2); der Stack-Trace soll ins Log wandern, ein gestaltetes Log existiert noch nicht.
**Problem:** `Server/Program.cs` registriert keinen `app.UseExceptionHandler(...)` / kein `AddProblemDetails`. Eine unbehandelte Exception in irgendeinem Endpoint schlägt daher als roher 500 durch. DELETE war der erste Endpoint mit client-steuerbarem Input, der das sichtbar machte; der konkrete run-10-Pfad (malformed If-Match) ist mit `XminETag.TryParse` → 400 (ADR-S106-2) geschlossen, aber die systemische Verteidigungslinie fehlt weiterhin. Quelle: security-auditor (Review run-10, SEC-2). Weitere bekannte Pfade (S147, CROSS-text/run-1, nicht nachgestellt): ein Name mit U+0000 (Postgres lehnt NUL in text ab → DbUpdateException) und ein einzelnes Surrogat (`string.Normalize` in `NonEmptyNormalizedString` wirft vermutlich ArgumentException, sofern System.Text.Json es durchlässt) enden vermutlich in 500 statt 422 (Quelle: security-auditor SEC-6, functional-correctness-auditor F-9). Seit US-602 run-11 trifft der U+0000-Pfad auch jede Zutatenzeile: Der Name geht schon beim Nachschlagen der Zutaten als Parameter an die DB, vor der übrigen Validierung – der 500 verdeckt dann alle gesammelten Meldungen (Security-Review run-11, nicht nachgestellt). Ob U+0000 und Surrogate als Verstoß gelten sollen, hängt an der offenen Frage zur Zeichenmenge der Normalisierung.
**Reichweite präzisiert (an learn.microsoft.com verifiziert, Kommentar an der Stelle in `Server/Program.cs`):** Ohne Handler liefert Kestrel in Production einen **500 ohne Response-Body** – dort leakt nichts. Der Stack-Trace-Leak über die Developer-Exception-Page setzt `ASPNETCORE_ENVIRONMENT=Development` voraus, was ausschließlich `Server/Properties/launchSettings.json` beim lokalen Start setzt, nie ein Deployment. Zu korrigieren ist außerdem die frühere Begründung: Der NFR „keine Stack-Traces für User" (`nfr.md`, Reliability) ist eine **Frontend**-Anforderung – die UI zeigt nichts Technisches an – und trägt diesen Backend-Eintrag nicht.
**Behebung:** Unbedingte Registrierung von `UseExceptionHandler`, damit der Fehlerpfad keinen Umgebungs-Zweig mehr hat – Entscheidung, Begründung, Verworfenes und offene Punkte stehen in **ADR-S112-1**. Prüfbar als Backend-Integrationstest (`WebApplicationFactory`), nicht per E2E – die Eigenschaft ist an der Oberfläche nicht beobachtbar. Zieht `TD-S084-1(b)` (try/finally in der ETag-Middleware) unmittelbar nach sich.

---

## TD-S108-1 — Frontend Delete/Restore-Pfad: optimistischer Undo-Toast + kein Status-Check
**Fällig:** Szenario:„Während eine Löschung läuft, erscheint noch kein Toast", Szenario:„Eine Zutat, die in Rezepten verwendet wird, lässt sich nicht löschen", Phase:MVP – die ersten UI-Szenarien, in denen DELETE scheitert (Löschsperre aus US-602, recipes.feature): Das erste beobachtet den Toast vor der Antwort (a), das zweite den fehlenden Status-Check. Spätestens mit den @NFR-resilience-Szenarien (MVP).
**Problem:** Zwei zusammenhängende Lücken im Löschen-/Undo-Pfad (`useDeleteIngredientWithUndo.ts`, `ingredientsApi.ts`):
(a) **Optimistischer Toast.** `requestDelete` setzt `deleted` **synchron vor** dem Mutation-Call – der Toast „X gelöscht" erscheint also, bevor der DELETE-Request überhaupt beantwortet ist, während die Liste erst nach Server-Antwort + `invalidateQueries` aktualisiert wird. Folgen: bei spürbarer Latenz zeigt die UI gleichzeitig „X gelöscht" **und** X unverändert in der Liste (inkl. klickbarem Löschen-Button); bei einem Netzwerkfehler bleibt eine **falsche Erfolgsmeldung** samt Undo-Button für eine Löschung stehen, die nie stattfand. Der Restore-Pfad macht es bereits richtig (`setDeleted(null)` + `onChanged()` gemeinsam im `onSuccess`).
(b) **Kein ausreichender Status-Check.** `deleteIngredient` wertet `response.status` **überhaupt nicht** aus (`ResultAsync.fromPromise(fetch(...))`) – ein 404/412/428 gilt als Erfolg. `restoreIngredient` wertet über `toRestoreOutcome` ausschließlich den `409` aus; jeder andere Status fällt in den Erfolgszweig und wird als `Ingredient` geparst. Bei einem `404` entsteht so ein `Restored`-Outcome mit einem ProblemDetails-Objekt als vermeintlicher Zutat, ohne dass irgendwo ein Fehler sichtbar würde. Der Restore-Endpoint kann zudem mit `422` antworten (Namenskollision mit einer anderen Zeile, ADR-S111-1-Addendum) – ein Statuscode, den der Client nicht kennt; über die aktuelle UI nicht auslösbar, weil pro LOWER-Name nur eine Zeile existieren kann, aber der Pfad besteht. Derselbe Defekt wie in TD-S083-1 für den GET-Pfad.
(c) **Undo kann wirkungslos verpuffen (Race).** Weil der Toast optimistisch erscheint, ist „Rückgängig" bereits klickbar, während der DELETE noch unterwegs ist. Trifft der `POST /restore` **vor** dem `SaveChangesAsync` des DELETE ein, findet der Restore die Zeile noch aktiv (`DeletedAt` ist noch `null`) → EF erkennt keine Änderung → kein UPDATE, kein xmin-Bump. Der danach eintreffende DELETE matcht seinen alten xmin weiterhin und committet normal. Endzustand: **Zutat bleibt gelöscht, obwohl der Nutzer „Rückgängig" geklickt hat** – ohne jede Fehlermeldung, der Toast verschwindet einfach. Das ist schärfer als (a): dort geht es um eine Anzeige-Inkonsistenz, hier um einen real verlorenen Undo. Praktisch selten (erfordert einen Klick innerhalb der DELETE-Roundtrip-Zeit), aber bei langsamer Verbindung erreichbar.
Alle drei Punkte sind im Erfolgsfall bei schnellem Netz unbeobachtbar – deshalb erzwingt kein Szenario sie heute. Quelle: ux-ui-auditor + functional-correctness-auditor (Review run-8, (a)/(b) unabhängig doppelt gefunden, (c) in Review-Runde 2).
**Zusammenhang:** TD-S110-1 beschreibt dieselbe Fehlerpfad-Lücke für den seit run-9 bestehenden `deletingId`-State und wird sinnvollerweise im selben Schritt mitbehoben.
**Behebung:** In einem Zug: `setDeleted` in den Erfolgs-Callback verschieben **und** die Fehler-Union für Delete/Restore einführen (dann trägt `ApiError` echte Domain-Kinds statt nur `Unexpected`, vgl. ADR-S056-1). Getrennt zu fixen lohnt nicht – (a) ohne (b) lässt einen 404 weiterhin als Erfolg durchgehen. Das Verschieben von `setDeleted` schließt (c) als Nebeneffekt mit: Ist der Undo-Button erst nach dem Delete-Erfolg klickbar, kann der Restore den DELETE nicht mehr überholen. Ohne das `QueryCache.onError`-Setup aus den resilience-Szenarien ist die Fehler-Union nicht sinnvoll.

---

## TD-S108-2 — Frontend: kein Fokus-Management nach Löschen und nach Undo
**Fällig:** Szenario:„Während eine Löschung läuft, erscheint noch kein Toast", Phase:V1 – der Lauf baut den Lösch-/Toast-Pfad der Zutaten-Seite ohnehin um (TD-S108-1 hängt dort); die Navigationsleiste liefert den Tab-Kontext zur Bewertung
**Problem:** Nach dem Löschen einer Zutat unmountet das fokussierte Element (der Löschen-`IconButton` bzw. bei der letzten Zutat die ganze Liste), ohne dass der Fokus gezielt weitergeführt wird – der Browser setzt ihn auf `<body>` zurück. Dasselbe passiert nach einem Undo-Klick, wenn die Snackbar unmountet. Tastatur- und Screenreader-Nutzer müssen den „Rückgängig"-Weg danach per Tab suchen. Entschärfend: `SnackbarContent` setzt `role="alert"` (MUI-Default), die Meldung samt Undo-Möglichkeit wird also **angesagt**; MUI pausiert zudem den Auto-Hide-Timer, sobald der Button Fokus erhält – wer ihn erreicht, verliert die Zeit nicht. Heute sind es 1–2 Tab-Stopps, das wächst aber mit jeder weiteren Seite. Quelle: ux-ui-auditor (Review run-8, Runde 2).
**Früher noch als beim Unmount:** Weil der Löschen-Button während des laufenden DELETE `disabled` wird (`IngredientsPage.tsx`), verliert er den Fokus bereits **beim Disable** – also unmittelbar nach dem Tastendruck und **vor** jedem Ergebnis, nicht erst beim Unmount nach Abschluss. Ein `disabled`-Element kann den Fokus per HTML-Semantik nicht halten; der Browser setzt ihn auf `<body>`. Anders als im Anlege-Dialog fängt hier keine MUI-Fokusfalle den Rücksprung ab, weil die Liste kein Modal ist. Ein Tastatur-/Screenreader-Nutzer verliert damit die DOM-Orientierung, während die Aktion noch läuft. Quelle: ux-ui-auditor (Review run-9).
**Behebung:** Als bewusste Fokus-Strategie entscheiden, nicht als Schnellfix – die naheliegende Lösung (Autofokus auf „Rückgängig") hat echte Nebenwirkungen: Fokus-Stealing in ein selbstschließendes Element reißt den Nutzer aus dem Arbeitsfluss, und weil MUI bei Fokus den Timer pausiert, bliebe der Toast für Tastaturnutzer stehen, bis er aktiv weggedrückt wird. Strukturelle Nav-Vorgabe: UX-Guideline „Erreichbarkeit / Navigation".

---

## TD-S108-4 — Frontend: Undo-Toast auf Touch-Geräten nicht manuell schließbar
**Fällig:** Szenario:„Der Undo-Toast lässt sich manuell schließen", Phase:MVP – das Szenario existiert inzwischen (`features/interaction.feature`), ist aber keinem Lauf zugeordnet, daher der Phasen-Backstop. Ein rein reaktiver Auslöser („der nächste Lauf, der den Toast ohnehin verändert") ist ausdrücklich **nicht** ausreichend – er wurde bereits einmal übersehen, während der Toast-Bereich verändert wurde (LL-S111-2).
**Problem:** Seit der Undo-Toast `clickaway` bewusst ignoriert (damit ein beiläufiger Klick den einzigen Weg zurück nicht wegnimmt, `IngredientsPage.tsx`), bleiben als Schließ-Wege nur Timeout und Escape. Auf Touch-Geräten ist Escape praktisch nicht auslösbar und ein Schließen-Button existiert nicht – dort verschwindet der Toast ausschließlich nach Ablauf der 6 Sekunden. Kein Datenverlust und keine Blockade (die Snackbar ist nicht-blockierend), aber auf dem primären Zielgerät der App (Mobile-First) kann der Nutzer die Meldung nicht aktiv wegräumen. Quelle: functional-correctness-auditor (Review run-8).
**Schärfer beim zweiten Toast:** Der `ReactivationConflictToast` (ADR-S111-3) schließt zwar bei clickaway (kein Aktions-Button, der geschützt werden müsste), steht aber **10 Sekunden** statt 6 – bewusst so entkoppelt, weil der Text rund zehnmal so lang ist. Genau das Argument, das die längere Dauer rechtfertigt, verschärft die Lücke: MUIs Pause-bei-Hover greift auf Touch nicht, und auf dem primären Zielgerät bleibt die Meldung damit am längsten stehen, ohne dass der Nutzer sie aktiv wegräumen kann.
**Behebung:** Zusätzliche Schließen-Action (`CloseIcon`) neben „Rückgängig" – ein expliziter Button ist eine bewusste Geste und kollidiert nicht mit dem clickaway-Guard, der nur beiläufige Klicks abfängt. Weil es sichtbares Nutzerverhalten ist, muss ein Gherkin-Szenario davor liegen.

---

## TD-S110-1 — Frontend: Sperr-States im Löschen-/Undo-Pfad decken nur den Erfolgspfad ab
**Fällig:** TD-S108-1, Szenario:„Eine Zutat, die in Rezepten verwendet wird, lässt sich nicht löschen", Szenario:„Zwei gleichzeitige Löschvorgänge sperren beide Zeilen", Szenario:„Rückgängig ist während des Wiederherstellens deaktiviert", Phase:MVP – (a) und (b) mit TD-S108-1; die Löschsperre aus US-602 verlangt, dass „Löschen" nach der Sperrmeldung wieder bedienbar ist (deletingId wird bisher nur im Erfolgspfad zurückgesetzt); (c) und (d) je mit ihrem Szenario in features/interaction.feature. Alle spätestens ab MVP.
**Problem:** `useDeleteIngredientWithUndo.ts` führt seit run-9 einen `deletingId: string | null`-State, der die gerade löschende Zeile sperrt (`disabled={ingredient.id === deletingId}` in `IngredientsPage.tsx`). Er wird ausschließlich in `requestDelete` gesetzt und ausschließlich im `onSuccess` von `deleteMutate` zurückgesetzt. Daraus folgen drei Lücken – gemeinsam erfasst, weil sie denselben State, dieselbe Datei und denselben Fix-Ort betreffen:
(a) **Kein Reset im Fehlerpfad.** `useResultMutation`s `onSuccess` feuert nur bei `Ok`. Ein Netzwerkfehler (`Err`) lässt `deletingId` für immer stehen → der Löschen-Button dieser Zeile ist **dauerhaft** deaktiviert, ohne Fehlermeldung und ohne Retry-Weg; nur ein Reload hilft. Quelle: ux-ui-auditor (Review run-9).
(b) **Kein Reset im Restore-Pfad.** `restoreMutate`s `onSuccess` setzt `deleted` zurück, aber nicht `deletingId`. Klickt der Nutzer „Rückgängig", während der DELETE noch läuft (das Fenster aus TD-S108-1(c)), erscheint die Zeile durch das Refetch wieder – mit weiterhin gesperrtem Löschen-Button und ohne Toast, also ohne jeden sichtbaren Grund für die Sperre. Quelle: functional-correctness-auditor (Review run-9). **Hinweis:** Die in TD-S108-1 beschriebene Behebung (`setDeleted` in den Erfolgs-Callback verschieben) schließt dieses Fenster als Nebeneffekt mit, weil „Rückgängig" dann erst klickbar ist, wenn `deletingId` bereits `null` ist – beim Umsetzen von TD-S108-1 verifizieren, statt es separat zu fixen.
(c) **Skalar statt Menge.** Bei zwei überlappenden Löschvorgängen überschreibt der zweite `deletingId`; die erste Zeile wird wieder klickbar, obwohl ihr DELETE noch aussteht – ein zweiter DELETE auf dieselbe Zeile ist dann auslösbar. Quelle: ux-ui-auditor (Review run-9).
(d) **Kein Pending-Guard am „Rückgängig"-Button.** `deletingId` sperrt die Zeile während des DELETE; für den umgekehrten Weg gibt es nichts Vergleichbares – der „Rückgängig"-Button bleibt klickbar, während sein Restore noch läuft. Zwei schnelle Klicks lösen zwei parallele Restores derselben Zeile aus. Serverseitig sauber abgefangen (identische Werte → `200`, der Verlierer eines echten Races → `200`/`409` statt `500`, s. ADR-S111-1-Addendum), es entsteht also kein Datenschaden – die Lücke ist rein UI-seitig: eine laufende Aktion ohne sichtbare Rückmeldung, erneut auslösbar. Eine Button-Sperre ist sichtbares Nutzerverhalten und braucht ein eigenes Gherkin-Szenario. Quelle: functional-correctness-auditor (Review run-11).
Keine der vier Lücken ist heute durch ein Szenario beobachtbar: Das treibende Szenario ist ein Singleton-Happy-Path („nur Mehl existiert"), Fehlerpfade sind ihm bewusst entzogen; für (d) fehlt das Szenario, das die Sperre überhaupt fordert.
**Behebung:** (a) und (b) gemeinsam mit TD-S108-1: `deletingId` im Fehler-Zweig und im Restore-`onSuccess` mit zurücksetzen. (c) auf `ReadonlySet<string>` umstellen, (d) analog zu `deletingId` als Pending-Flag im selben Hook – beides erst **nach** dem jeweiligen Szenario: vorab umgesetzt entstünde ein Zweig, den kein Szenario ausübt → Stryker-Survivor → Suppression außerhalb des treibenden Szenarios, genau die Konstellation, die auch TD-S101-1 offen hält.

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

## TD-S120-1 — DB-Spalten ohne Längenbegrenzung: keine zweite Verteidigungslinie
**Fällig:** Phase:MVP – der Schutz der Anwendungsschicht greift heute vollständig; die DB-Ebene wird relevant, sobald mehr als ein Schreibpfad existiert oder Daten anders als über das API entstehen (Import, Seed, Fremdclient).
**Problem:** `IngredientDbType.Name` und `.BaseUnit` tragen kein `HasMaxLength` – die Spalten sind `text` ohne Obergrenze. Die 30/20-Zeichen-Regel (ADR-S051-3) wird ausschließlich in der Anwendungsschicht erzwungen. Das ist heute lückenlos: `Ingredient.Create` nimmt nur validierte Domänentypen, ist `internal` und hat genau einen Aufrufer, und `db.Ingredients.Add(...)` kommt im ganzen Server-Baum nur einmal vor (verifiziert im S120-Review). Es fehlt also nichts Akutes – es fehlt die zweite Verteidigungslinie, falls je ein Pfad an der Domäne vorbei schreibt.
**Behebung:** `HasMaxLength(30)`/`HasMaxLength(20)` in der Modell-Konfiguration, damit die Migration `varchar(n)` erzeugt. Die Grenzwerte stehen dann an zwei Orten – Marker-Typ und DB-Schema; ein Test, der beide gegeneinander hält, wäre das Mittel gegen Drift. Aufgedeckt vom `security-auditor` im S120-Review.

---

## TD-S120-2 — `.editorconfig`: tote Pfade und Suppressionen auf der falschen Ebene
**Fällig:** Phase:MVP – reine Aufräumarbeit ohne funktionales Risiko; sie wird nur teurer, je mehr Einträge dazukommen. Kein sachlicher Auslöser vorhanden, daher der Phasen-Backstop.
**Problem:** Drei Befunde in derselben Datei.
(a) **Tote Pfade:** Die Blöcke `[Server/Domain/Recipe.cs]`, `[Server/Data/DatabaseTypes/*.cs]`, `[Server/Data/SeedDataExtensions.cs]`, `[Server/Pages/*.cs]` und `[{Server/Migrations,…}]` zeigen auf Pfade, die es nicht gibt – keine dieser Dateien oder Verzeichnisse existiert. Sie unterdrücken nichts und täuschen Präzedenzfälle vor: `Recipe.cs` wurde im S120-Review als Begründung für eine Suppressions-Entscheidung herangezogen, bevor auffiel, dass die Datei fehlt.
(b) **Zeilenfälle auf Dateiebene:** Sechs Suppressionen betreffen jeweils **eine Stelle**, gelten aber für die ganze Datei – `[Server/Program.cs]` S1118 (eine Klassendeklaration), `[Server/Data/SeedDataExtensions.cs]` MA0051/S1075 (eine Methode / die URL-Literale), `[Server/Endpoints/*.cs]` MA0051 (je eine `MapXxxEndpoints`-Methode), `[Server/Domain/Recipe.cs]` MA0048. Das widerspricht der Regel, dass Zeilenfälle inline mit Begründung unterdrückt werden – siehe TD-S120-5.
(c) **Breite Globs ohne Einzelbegründung:** `[Server/Domain/*.cs]` MA0008 und `[Server/Types/*.cs]` CA2225/CA1000 gelten für alle heutigen und künftigen Dateien dieser Verzeichnisse.
**Behebung:** (a) löschen; (b) auf `#pragma warning disable/restore` an der betroffenen Stelle umstellen, inklusive **ADR-S040-1, „S3060 pro Sum-Type-Datei unterdrücken"**, die für S3060 heute ausdrücklich einen `.editorconfig`-Block vorschreibt, obwohl S3060 auf genau einen `this switch` feuert – die ADR ist mit anzupassen; (c) je Eintrag prüfen, ob er trägt. In S120 wurde bereits eine tote Suppression (CA2225, begründet mit Konvertierungsoperatoren, die es nicht mehr gibt) entfernt und eine falsch begründete (CA1000, verwies auf einen nicht existenten Typ) korrigiert. Aufgedeckt vom `code-quality-auditor` im S120-Review.

---

## TD-S120-3 — Funktionaler Unique-Index lebt als Hand-SQL in der Migration
**Fällig:** Phase:MVP – entschärft durch den Warnhinweis in `dev-workflow.md`; die Umstellung beseitigt die Fehlerquelle statt sie zu dokumentieren.
**Problem:** Der case-insensitive Unique-Index `IX_Ingredients_Name_Lower` (ADR-S105-2) steht als handgeschriebener `migrationBuilder.Sql(...)`-Block in der Migration, weil ein funktionaler Index über `LOWER("Name")` nicht per Fluent-API ausdrückbar ist. Er ist damit **nicht Teil des EF-Modells** – und die Projektphase sieht vor, die Migration bei Schema-Änderungen zu verwerfen und neu zu generieren (`dev-workflow.md`, „Drop + Recreate"). Genau das ist in S120 passiert: Die neu generierte Datei enthielt den Block nicht, der Build blieb grün, und erst der vollständige Testlauf zeigte den Verlust als sechs fehlschlagende Duplikat-Tests. Der Block wurde von Hand übertragen.
**Behebung:** Den Index ins Modell holen, damit `migrations add` ihn reproduziert – als persistierte generierte Spalte plus gewöhnlichen Unique-Index darauf (`HasComputedColumnSql("LOWER(\"Name\")", stored: true)` + `HasIndex(...).IsUnique()`). **Nicht verifiziert:** ob diese Kombination mit Npgsql sauber durchläuft und ob der Index denselben Namen behält, auf den `E2ETestSupport` sich bezieht. Preis ist eine zusätzliche Spalte; die Aussage in ADR-S105-2, das sei per Fluent-API nicht ausdrückbar, gilt dann nur noch für den funktionalen Index und wäre nachzuziehen.

## TD-S120-5 — Regel für Analyzer-Suppressionen steht nirgends
**Fällig:** TD-S120-2 – die Aufräumarbeit dort braucht das Kriterium als Maßstab; umgekehrt wäre die Regel ohne den ersten Anwendungsfall unbelegt. Wer zuerst drankommt, schreibt beides.
**Problem:** Für **Stryker**-Suppressionen ist alles geregelt ([`csharp-stryker.md` – Inline-Suppressions](guidelines/csharp-stryker.md#STK-suppressions): inline, Zeile davor, Begründung nach Doppelpunkt, nur äquivalente Mutanten, jede zusätzlich in `adr.md`). Für **Analyzer**-Suppressionen gibt es keine einzige Regel – nur gelebte Praxis und einen normativen Halbsatz in ADR-S040-1 („S3060 pro Sum-Type-Datei unterdrücken") zu genau einer Diagnose (S3060). Folge: Die Ablage entscheidet jeder neu, und zwar nach Gefühl. In S120 wurde MA0048 im selben Zug auf zwei Wegen unterdrückt (inline in `IngredientName.cs`/`Unit.cs`, per `.editorconfig` für `StringConstraints.cs`), bevor die Frage überhaupt gestellt wurde; ein Reviewer hat die Inkonsistenz unabhängig gemeldet.
**Behebung:** Absatz in `coding-guideline-csharp.md` neben den Stryker-Regeln. Das mit dem User in S120 festgelegte Kriterium:
- **Betrifft die Diagnose einzelne Zeilen → `#pragma warning disable/restore` dort**, mit Begründung. Grund: Die Begründung ist dann Pflicht und wird bei jedem Edit an der Stelle mitgelesen; die Form verrät zugleich die Reichweite.
- **Gilt sie wirklich dateiweit → `.editorconfig`**, als begründete Ausnahme, jedes Mal kritisch geprüft. Tragfähiger Fall: eine Datei, in der Mehrtypigkeit die *erwartete* Eigenschaft ist (`StringConstraints.cs`, MA0048) – dann ist ein Eintrag, der das einmal festhält, ehrlicher als N Pragmas.
- **Kein `#pragma` ohne `restore` am Dateianfang.** Es sieht aus wie eine lokale Suppression, wirkt aber bis Dateiende – diese Tarnung ist schlechter als ein offener `.editorconfig`-Eintrag.

---

## TD-S122-1 — `useResultMutation` gibt ein 4er-Positions-Tupel zurück
**Fällig:** Phase:MVP – der MVP-Ausbau der Formulare fasst die Aufrufstellen ohnehin an; bei den heutigen wenigen Call-Sites trägt das Tupel noch.
**Problem:** `useResultMutation` liefert `[mutate, error, isPending, reset]` – vier Positionen, zwei davon Funktionen. Positions-Tupel werden mit wachsender Länge fehleranfällig: Jede Call-Site muss exakt in der richtigen Reihenfolge destrukturieren, und `error`/`isPending` sind beim Lesen leicht zu verwechseln. Eine vertauschte Reihenfolge fängt der Compiler nur, wenn sich die Typen unterscheiden.
**Behebung:** Rückgabe auf ein Objekt `{ save, error, isPending, reset }` umstellen – selbstdokumentierend und reihenfolgeunabhängig; Aufrufstellen mitziehen.
**Herkunft:** OBS-S101-3 (S101), in S122 hierher umgezogen.

---

## TD-S122-2 — Restore-Endpoint ist ein CORS-„Simple Request" ohne Preflight-Schutz
**Fällig:** Phase:MVP – vor der ersten Nutzung außerhalb der lokalen Entwicklung; bis dahin ist der Schutz der übrigen mutierenden Endpoints ein Nebeneffekt, kein Entwurf.
**Problem:** `POST /api/ingredients/{id}/restore` verlangt weder Custom-Header noch Request-Body und ist damit ein CORS-„Simple Request": Ein Browser sendet ihn cross-origin **ohne** Preflight. CORS verhindert dann nur das Auslesen der Antwort, nicht die serverseitige Ausführung – der Restore liefe also durch. Alle übrigen mutierenden Endpoints sind nur **zufällig** geschützt: `DELETE` durch den verpflichtenden `If-Match`-Header, `POST /api/ingredients` durch `Content-Type: application/json`; beide erzwingen dadurch eine Preflight, die mangels CORS-Policy scheitert. Dass der Restore kein `If-Match` verlangt, ist in ADR-S108-2 bewusst und mit Concurrency-Argumenten entschieden – dass `If-Match` nebenbei auch die Preflight erzwingt, war dabei nicht Teil der Abwägung.
**Behebung:** Den Schutz zur Entwurfsentscheidung machen, statt ihn der Header-Wahl einzelner Endpoints zu überlassen – explizite CORS-Policy serverseitig.
**Herkunft:** OBS-S108-5 (S108), in S122 hierher umgezogen.

---

---

## TD-S132-1 — EF Core Relational: Versionsschiefe 10.0.4/10.0.5 im Testprojekt (MSB3277)
**Fällig:** Phase:MVP – bis dahin nur eine Build-Warnung und Patch-Abstand; mit MVP kommen weitere EF-Features, deren Laufzeitverhalten im Test dann gegen eine ältere Relational-Version liefe
**Problem:** `Server` zieht über `Microsoft.EntityFrameworkCore.Design` 10.0.5 `Microsoft.EntityFrameworkCore.Relational` 10.0.5, `Infrastructure` über `Npgsql.EntityFrameworkCore.PostgreSQL` 10.0.1 nur 10.0.4 (Untergrenze `[10.0.4, 11.0.0)`). `Server.Tests` löst 10.0.4 auf, `mahl.Server.dll` ist gegen 10.0.5 gebaut → Build-Warnung MSB3277 bei jedem Backend-Lauf; die Tests laufen gegen eine ältere Relational-Version als die, gegen die der Server kompiliert ist. Bestand schon vor S132, sichtbar wurde sie erst, als `dotnet-test.py` die Build-Ausgabe nicht mehr wegfilterte. Ein Npgsql-Update löst es nicht: auch 10.0.3 nennt nur die Untergrenze 10.0.4.
**Behebung:** Versionen angleichen: entweder `Microsoft.EntityFrameworkCore.Relational` 10.0.5 explizit in `Infrastructure` referenzieren (Allowlist-Erweiterung, User-Freigabe nach `dependencies.md`) oder `Microsoft.EntityFrameworkCore.Design` auf die Relational-Version der Npgsql-Kette ausrichten. Erledigt, wenn ein Backend-Build ohne MSB3277 durchläuft.

---

## TD-S135-1 — Ausgaben unbegrenzt lang – Querschnitt „Länge begrenzen" fehlt
**Fällig:** Phase:MVP – dann ersetzt der MVP-Zerleger (US-607) den SKELETON-Zerleger, und die Löschsperre aus US-602 (Aufzählung der Rezepte) kommt hinzu.
**Problem:** Die UX-Guideline verlangt, dass Ausgaben nicht mit den Daten wachsen (CGU-fehlermeldungen, „Länge begrenzen"): Aufzählungen höchstens drei Einträge + „und N weitere", zitierter eingegebener Text gekürzt mit „…". Es gibt dafür weder Szenarien noch eine geteilte Umsetzung. Im SKELETON zitiert die Meldung zu einer Zutatenzeile (recipes.feature) die Zeile unbegrenzt – eine versehentlich eingefügte Riesenzeile erscheint vollständig. Seit US-602 run-11 zeigt das Zutatenfeld zudem alle Zeilenmeldungen als Aufzählung, ohne Obergrenze; eine Kürzung auf drei Einträge widerspräche dem Szenario „Alle fehlerhaften Zutatenzeilen werden gemeinsam und in Zeilenreihenfolge gemeldet" und braucht dessen Anpassung. Eine zitierte Zeile ohne Leerzeichen (z. B. eingefügte URL) läuft am Handy vermutlich waagerecht über – im Client setzt nichts overflow-wrap (UX-Review run-11, im Browser nicht geprüft).
**Behebung:** Querschnittsdatei mit Szenarien (eine Seite als Vertreter), geteilte Umsetzung nach ADR-S112-5 für beide Formen, ADR mit der Kürzungslänge; Zitat der Zutatenzeile und Löschsperre-Meldung darüber führen.
**Aufschubgrund:** User – Regel gilt, Umsetzung erst im MVP; der SKELETON-Zerleger, der das unbegrenzte Zitat erzeugt, wird dort ohnehin ersetzt.

---

---

## TD-S141-1 — Frontend: Conditional-GET-Cache ist nicht an den Nutzer gebunden
**Fällig:** Phase:MVP – mit der Einführung von Login/Logout (Auth-Gate) entsteht erst ein Nutzerwechsel im selben Tab
**Problem:** conditionalGetJson (Client/src/services/conditionalGet.ts, ADR-S084-3) hält einen modul-lokalen Cache URL → { etag, body } für die gesamte Lebensdauer des Tabs. Er kennt keinen Nutzer. Meldet sich nach Einführung von Auth ein anderer Nutzer im selben Tab an, könnte eine 304-Antwort den gecachten Body des vorigen Nutzers ausliefern. Heute ohne Wirkung: SKELETON hat keine Anmeldung. Quelle: security-auditor, Review US-602 run-1.
**Behebung:** Beim Login und Logout resetConditionalGetCache() aufrufen (existiert bereits) – oder den Cache-Schlüssel um die Nutzerkennung erweitern; Entscheidung mit dem Auth-Design.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-1 mit allen drei Optionen vorgelegt; ohne Auth nicht umsetzbar

## TD-S141-3 — Backend: Rezept-Zutat liest die Zutat-Id ohne Prüfung aus der DB
**Fällig:** Phase:MVP – mit dem DB-Inkonsistenz-Verhalten (docs/reference/architecture.md#ARC-db-inkonsistenz), gemeinsam mit TD-S083-5
**Problem:** US-602 run-2 braucht für die Rezept-Zutat die Id einer bestehenden Zutat aus der DB. Uuid7 und IngredientId hatten bewusst nur New(); für den Lesepfad entstand ein nicht validierendes IngredientId.Create(Guid) über Uuid7.Create(Guid). Eine aus der DB gelesene Id, die kein gültiges UUIDv7 ist (manueller Eingriff, fehlerhafte Migration), wird damit ungeprüft übernommen – der Fehlerzweig, den der Kommentar in Uuid7.cs für den Lesepfad vorsieht, fehlt.
**Behebung:** Mit dem DB-Inkonsistenz-Szenario Create(Guid) validierend machen (UUIDv7-Prädikat, OneOf) und den Fehlerzweig auf die Regel aus ARC-db-inkonsistenz abbilden (Liste: überspringen + loggen, Einzel-Endpoint: 500).
**Aufschubgrund:** User – beim Architektur-Check von US-602 run-2 ist der Lesepfad ohne Prüfung als Zwischenschritt gewählt; ein validierender Zweig wäre ohne Szenario ungetestet

## TD-S141-10 — Rezept-Eingaben ohne Obergrenze für Zutatentext, Zeilen- und Schrittzahl
**Fällig:** Phase:MVP – im Workshop der MVP-Stufe von US-602 als Szenario festlegen, ggf. später
**Problem:** POST /api/recipes begrenzt weder die Länge des Zutatentexts noch die Zahl der Zutatenzeilen oder Schritte; die Spalten sind text ohne Constraint, die einzige Schranke ist Kestrels Default-Body-Grenze (30 MB). features/recipes.feature begrenzt nur Titel (100) und Schritt-Anweisung (1000). Versehentlich unsinnige Eingaben (z.B. eingefügter Großtext) werden so ungeprüft gespeichert. Die 422-Antwort wächst zudem mit der Schrittzahl: Jeder leere (seit US-602 run-8) und jeder zu lange Schritt (seit run-9) ergibt einen eigenen Eintrag steps[i].instruction – 10 000 Schritte mit je 1001 Zeichen liefern 10 000 Meldungen. Eine Schrittobergrenze begrenzt damit auch die Fehlerantwort (Security-Review run-8). Seit US-602 run-11 schlägt jedes Anlegen die Zutatennamen aller Zeilen in einer DB-Abfrage nach (bis zu zwei Namen je Zeile als Parameter-Array), auch bei sonst ungültigem Request; ohne Zeilenobergrenze wächst diese Abfrage mit der Eingabe (Security-Review run-11).
**Behebung:** Fachliche Obergrenzen als Szenario festlegen – Zweck wie bei den Zutaten-Namen: versehentliche unsinnige Eingaben abfangen, nicht Lastschutz (der liegt bei TD-S102-1) – und mit Meldung am Feld umsetzen.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-2 entschieden: für den SKELETON egal, frühestens MVP

## TD-S142-2 — Rezept-Detail: ETag und Abfragen decken Rezeptzeilen, Schritte und Zutatendaten nicht ab
**Fällig:** Phase:MVP – Backstop; eigentlicher Auslöser ist das erste Szenario, das Rezeptzeilen, Schritte oder Name/Einheit einer verwendeten Zutat ändert (bisher keins spezifiziert)
**Problem:** GET /api/recipes/{id} (Server/Endpoints/RecipesEndpoints.cs, GetRecipe) setzt als ETag den xmin der Rezeptzeile (ADR-S142-2). Die Antwort enthält aber auch Zutatenname und -einheit (Tabelle Ingredients), die Rezeptzeilen und die Schritte; deren Änderung lässt den Rezept-xmin unverändert, ein If-None-Match bekäme 304 mit veraltetem Inhalt, und der Frontend-Cache (ADR-S084-3) zeigte ihn weiter. Zudem laufen die drei Abfragen (Rezept, Zeilen, Schritte) ohne gemeinsamen Snapshot: Ein Schreibvorgang dazwischen ergäbe einen Mischzustand. Heute folgenlos – es gibt keinen Schreibweg auf diese Daten außer der Reaktivierung einer gelöschten Zutat mit anderer Einheit, und ein Rezept mit gelöschter Zutat ist eine hingenommene SKELETON-Grenze (features/recipes.feature, Bekannte Grenzen).
**Behebung:** Mit dem ersten solchen Schreibweg die ETag-Quelle anpassen (z. B. Rezeptzeile bei jeder Änderung an Zeilen/Schritten mitschreiben, damit ihr xmin wechselt; für Zutatendaten Hash oder Kombination) und die Abfragen in einer Transaktion mit Snapshot-Isolation lesen; ein Server-Test belegt, dass nach der Änderung kein 304 mehr kommt.
**Aufschubgrund:** User – im Review von US-602 run-4 als TD statt Sofort-Fix entschieden, weil noch kein Schreibweg existiert

---

## TD-S142-3 — Rezeptseiten: Listenzeilen ohne Klick-Hinweis, Zutatenliste der Detailansicht zu locker
**Fällig:** Phase:MVP – im SKELETON ist die Gestaltung nachrangig (User)
**Problem:** Client/src/pages/RecipesPage.tsx: Die Einträge der Rezept-Liste sind Links (ListItemButton), sehen am Handy aber wie reiner Text aus – kein Trenner, kein Pfeil, ohne Hover keine Klick-Andeutung. Client/src/pages/RecipeDetailPage.tsx: Die Zutatenliste hat rund 48 px Zeilenabstand bei 16-px-Text (Sichtprüfung bei 375 px); eine Liste mit 15 Zutaten läuft über mehrere Bildschirme, beim Kochen ist sie nicht auf einen Blick lesbar.
**Behebung:** Klick-Andeutung für Listenzeilen (z. B. Pfeil am Zeilenende und/oder Trenner) und eine dichtere Zutatenliste festlegen, beides als Eintrag in docs/guidelines/coding-guideline-ux.md#CGU-visuelle-baseline statt Einzelwerte per sx; bei 375 px im Browser prüfen.
**Aufschubgrund:** User – im Review von US-602 run-4 entschieden: im SKELETON nebensächlich, ab MVP beheben

---

## TD-S142-4 — Rezept-Detailansicht: Schrittliste unter VoiceOver nicht geprüft
**Fällig:** Phase:V1 – Barrierefreiheit muss laut User im MVP noch nicht vollständig sein
**Problem:** Client/src/pages/RecipeDetailPage.tsx rendert die Schritte als List component="ol" mit sichtbarer Nummer im ListItemIcon; MUI setzt list-style: none. Nach verbreiteter, aber schwach belegter Darstellung (Blogposts, WebKit-Bugtracker, hier nicht geprüft) nimmt Safari/VoiceOver einer Liste mit list-style: none die Listen-Semantik – die Reihenfolge-Ansage, für die die geordnete Liste gewählt wurde, entfiele dann. Andere Screenreader könnten Listenposition und sichtbare Nummer doppelt ansagen.
**Behebung:** Mit VoiceOver (Safari) und einem zweiten Screenreader prüfen; falls nötig role="list" an der Liste ergänzen bzw. die sichtbare Nummer per aria-hidden ausblenden. Der heutige Aufbau verbaut nichts – die Korrektur ist ein Attribut, kein Umbau.
**Aufschubgrund:** User – im Review von US-602 run-4 entschieden: Barrierefreiheit ist im MVP noch zu früh, solange kein Weg verbaut ist

---

## TD-S143-1 — Rezeptformular: Schrittfeld-Fokus hängt am Einhängen (autoFocus)
**Fällig:** Phase:MVP – beim Bearbeiten (US-614) hängt das Formular mit vorbefüllten Schritten ein; ein Szenario „Fokus beim Öffnen auf dem Titel" mit mehreren Schritten macht den Fehler dort sichtbar
**Problem:** Client/src/pages/CreateRecipePage.tsx (StepsSection) setzt autoFocus={index > 0}: Jedes Schrittfeld ab Nummer 2 holt sich beim Einhängen den Fokus. Das trägt nur, solange Schrittfelder ausschließlich einzeln angehängt werden. Hängt die Gruppe einmal mit mehreren Feldern neu ein (Remount nach Fehler, Vorbefüllung, Entwurf), stiehlt das letzte Feld den Fokus und kollidiert mit „Fokus aufs erste fehlerhafte Feld" (ADR-S135-4).
**Behebung:** Im Lauf mit dem Fehler-Fokus prüfen, ob die Gruppe neu einhängt; falls ja, den Fokus nach „Schritt hinzufügen" imperativ per Ref im onAdd-Handler setzen statt über autoFocus.
**Aufschubgrund:** User – in run-13 entschieden: nach einem Fehler hängt die Schrittgruppe nicht neu ein (Szenario „Fokus springt auf das erste fehlerhafte Feld" und der Test mit drei Schrittfeldern grün), das Risiko entsteht erst beim Vorbefüllen

## TD-S143-4 — Nachfrage „Eingaben verwerfen?“: Aktionen brechen bei 320 px um
**Fällig:** Phase:MVP – wenn weitere Dialoge mit zwei Text-Aktionen dazukommen, als gemeinsame Baseline-Regel
**Problem:** Bei 320 px Breite (laut docs/process/nfr.md primärer Bereich) bricht „WEITER BEARBEITEN“ in der Nachfrage des Rezeptformulars (DiscardDialog in Client/src/pages/CreateRecipePage.tsx) auf zwei Zeilen um, „VERWERFEN“ daneben einzeilig – die Buttons wirken ungleich hoch. Lesbar und bedienbar (Touch-Ziele ≥ 44 px), bei 390 und 1280 px sauber. Die Visuelle Baseline (coding-guideline-ux.md#CGU-visuelle-baseline) regelt den Umbruch von Dialog-Aktionen nicht.
**Behebung:** Eine Baseline-Regel für Dialog-Aktionen auf schmalen Bildschirmen festlegen (z. B. auf xs untereinander in voller Breite) und in DialogActions umsetzen; Beleg per Screenshot bei 320 px.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-6 entschieden: Schönheitsmangel, eine Einzellösung ohne Szenario lohnt nicht

## TD-S144-2 — Backend: Rezept-POST mit null als Schritt-Element endet in 500
**Fällig:** Phase:MVP – mit dem öffentlich erreichbaren API und dem globalen Exception-Handler (TD-S106-1)
**Problem:** Ein Body mit "steps": [null] bindet ein null-StepDto; RecipesEndpoints.ToSteps greift auf step.Instruction zu und wirft NullReferenceException (500). Über das Formular nicht auslösbar (der Client sendet immer Schritt-Objekte). Fehlende Properties (ADR-S144-2) und ein fehlendes instruction im Schritt-Objekt sind dagegen behandelt.
**Behebung:** null-Elemente in steps wie eine leere Anweisung behandeln (422 mit steps[i].instruction, ADR-S144-1) oder als fehlerhaften Request ablehnen (400) – Entscheidung in ADR-S144-2 ergänzen; mit einem Integrationstest belegen.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-8 entschieden

---

## TD-S144-3 — Rezeptformular: weitere Meldungen für Screenreader nicht angesagt
**Fällig:** Phase:MVP – Barrierefreiheit der Formulare vor dem öffentlichen Betrieb
**Problem:** Nach einem Speichern mit mehreren Fehlern springt der Fokus aufs erste fehlerhafte Feld (ADR-S135-4); dessen Meldung wird vorgelesen. Die übrigen Meldungen (z.B. Zutaten und Schritte im leeren Formular) sind weder role="alert" noch aria-live – ein Screenreader-Nutzer erfährt erst davon, wenn er die Felder anspringt. Sehende sehen alle gleichzeitig (Szenario „Leeres Formular speichern zeigt alle Pflichtmeldungen gleichzeitig“). UX-Review US-602 run-8.
**Behebung:** Eine kurze Zusammenfassung per role="status" (z.B. „3 Angaben fehlen“) oder role="alert" an den eigenen Meldungselementen; als Szenario bzw. UX-Guideline-Regel festlegen, dann umsetzen.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-8 entschieden: Erweiterung über den freigegebenen UI-Entwurf hinaus

## TD-S144-5 — Frontend: createRecipe wertet jede Antwort außer 422 als Erfolg
**Fällig:** Szenario:„Backend liefert Serverfehler beim Speichern – Formular bleibt offen", Phase:MVP – wenn der Querschnitt auf das Rezeptformular angewendet wird (ADR-S112-5), spätestens mit dem öffentlichen API
**Problem:** Client/src/services/recipesApi.ts createRecipe behandelt nur 422 als Fehler (toFieldErrors); bei 400 oder 500 wird der Problem-Body als Recipe gelesen, created.id ist undefined und die Seite navigiert nach /recipes/undefined. Ein 500 ohne JSON-Body lässt response.json() rejecten (fromSafePromise, unbehandelt). Seit US-602 run-8 gibt es zusätzlich den 400-Pfad für fehlende Properties (ADR-S144-2), über das Formular nicht erreichbar.
**Behebung:** response.ok prüfen; 422 → FieldErrors, sonst UnexpectedError, sodass das Formular mit allen Eingaben stehen bleibt (Querschnittsvertrag „Formular speichern“, recipes.feature).
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-8 entschieden

## TD-S148-2 — Backend: Zeilenauflösung des Rezept-Anlegens steckt in RecipesEndpoints und arbeitet auf Strings
**Fällig:** Phase:MVP – mit US-607, das das Freitext-Zutatenfeld durch Zutaten je Schritt ablöst (ADR-S135-2): Die Zeilenauflösung wird dort ersetzt, ein Umbau vorher polierte Code, der wegfällt
**Problem:** RecipeMappings in Server/Endpoints/RecipesEndpoints.cs ist mit US-602 run-11 auf rund 400 Zeilen gewachsen und mischt Zerlegen der Zutatenzeilen, DB-Nachschlagen, Auflösen (Einheit passt, Zutat doppelt), Speichern, Lesen und DTO-Mapping. Die Regeln „Einheit passt zur Zutat" und „Zutat höchstens einmal" prüfen rohe Strings bzw. Guids an der API-Grenze (Einheitenvergleich OrdinalIgnoreCase), obwohl es den Domänentyp Unit gibt; Recipe.Create kennt die Doppelt-Regel nicht. Bewusst so gebaut, weil die Meldung die Zeile zitiert und der Zutatenbestand erst an der Grenze bekannt ist (ADR-S135-2, Addendum S148). Quelle: code-quality-auditor, Review run-11.
**Behebung:** Die Zeilenauflösung (ParsedIngredientLine bis ResolvedIngredientLine, FindActiveIngredientsAsync) in eine eigene Datei bzw. einen eigenen Resolver ziehen; prüfen, ob der Einheitenvergleich über Unit laufen kann und ob die Doppelt-Regel als Domänenregel ausdrückbar ist, ohne die gesammelte Meldung mit Zeilenzitat zu verlieren. Verhalten unverändert, Beleg: qa-check.
**Aufschubgrund:** User – in der Architektur-Prüfung von US-602 run-12 entschieden: run-12 ergänzt die Datei nur um das Abfangen der Titel-Eindeutigkeit (rund zehn Zeilen); der Schnitt lohnt erst mit US-607

---

## TD-S150-1 — Backend: Upgrade auf .NET 11 und Umstellung der Sum-Types auf C#-15-Unions (ADR-S150-1)
**Fällig:** S155 – Spätestens-Termin; der Umbau ist entschieden (ADR-S150-1), offen ist allein, ob die Werkzeugkette ihn trägt
**Problem:** Das Projekt steht auf net10.0; LangVersion=latest liefert dort C# 14, also keine Union-Typen. Die Sum-Types laufen deshalb weiter über Server/Types/SumType.cs mit SumType.Unreachable-Armen, Stryker-Suppression und Coverage-Ausschluss (ADR-S040-1), obwohl ADR-S150-1 die Ablösung entschieden hat. Ungeprüft ist, ob Stryker.NET, EF Core/Npgsql und coverlet mit .NET 11 und der Union-Syntax schon funktionieren.
**Behebung:** Zuerst prüfen, ob Stryker.NET, EF Core/Npgsql, coverlet und die Analyzer .NET 11 und C# 15 tragen (Release Notes, dann ein Probe-Lauf auf einem Branch). Trägt die Kette: TargetFramework auf net11.0, jeden Sum-Type nach ADR-S150-1 umstellen (native union bei Referenztyp-Fällen, eigener Typ mit HasValue/TryGetValue bei Werttyp-Fällen), Unreachable-Arme samt Suppressionen entfernen, ADR-S040-1 auf Superseded. Trägt sie nicht: diesen Eintrag mit dem blockierenden Werkzeug als Auslöser neu terminieren. Beleg: dotnet-test und dotnet-stryker grün, 100 %.
**Aufschubgrund:** User – in S150 entschieden (offene Frage „native C#-Union-Types statt SumType.cs“, damit geschlossen): Richtung als ADR, Upgrade als eigener Schritt nach der Werkzeug-Prüfung, nicht im laufenden Szenario-Lauf

---

## TD-S150-2 — Navigationsleiste nicht bündig mit dem Seitenrumpf
**Fällig:** Phase:MVP – visuelle Politur, wenn das Layout der Seiten ohnehin überarbeitet wird
**Problem:** Client/src/components/AppLayout.tsx: Die Leiste ist vollbreit und linksbündig, der Seitenrumpf dagegen auf maxWidth="sm" zentriert. Gemessen (Wegwerf-Probe, Playwright-Desktop-Viewport, Breite nicht abgefragt): linke Kante von „Zutaten" x = 24 px, Seitentitel x = 364 px. Am Handy kommen laut UX-Review ca. 8 px Innenabstand des Text-Buttons hinzu (aus MUI-Defaults abgeleitet, nicht gemessen). Die Visuelle Baseline (CGU-visuelle-baseline) nennt gegeneinander versetzte Kanten ausdrücklich als Mangel.
**Behebung:** Leiste in denselben Container wie der Seitenrumpf (Toolbar disableGutters, Container maxWidth="sm" ohne vertikalen Theme-Abstand), Innenabstand des ersten Buttons ausgleichen; Bündigkeit in der Visuellen Baseline festhalten. Messen lässt sie sich nur im Browser – ein E2E-Messtest braucht ein Szenario (E2E-Szenario-Mapping-Hook), also vorher klären, ob Layout-Bündigkeit per Szenario oder nur per Augenschein geprüft wird.
**Aufschubgrund:** User – im Review-Loop von CROSS-navigation run-1 entschieden: Messung nur im Browser möglich, ein Szenario für ein Layout-Detail lohnt jetzt nicht

---

## TD-S150-3 — Kein automatischer Kontrast- und Fokus-Check für das Accessibility-NFR
**Fällig:** Phase:MVP – eigener fokussierter Schritt: neue Dev-Abhängigkeit und eine Suite über alle Seitenzustände
**Problem:** docs/process/nfr.md (Accessibility) verlangt ausreichende Kontraste; geprüft wird das nirgends – Client/e2e/accessibility.spec.ts misst nur Touch-Targets, eine axe-Prüfung gibt es nicht (geprüft: grep nach axe in Client/e2e und package.json, kein Treffer). Anlass: Die Navigationsleiste setzt weißen Text auf MUI-Primärblau, laut UX-Review rechnerisch ca. 4,6:1 (knapp über AA 4,5:1, nicht gemessen); ob der Tastatur-Fokus auf dem blauen Grund sichtbar ist, ist ungeprüft.
**Behebung:** axe-Prüfung (z. B. @axe-core/playwright) in die Accessibility-Suite aufnehmen, parametrisiert über die vorhandenen Seitenzustände (touchTargetPages); Fokus-Sichtbarkeit der Leiste gezielt prüfen. Vorher Dependency-ADRs prüfen (decisions list --tag tooling:dependencies).
**Aufschubgrund:** User – in der Abschluss-Triage von CROSS-navigation run-1 entschieden: neue Abhängigkeit plus Suite ist ein eigener Schritt

---

## TD-S150-4 — Fehlerseiten: Rückweg aus dem Kontext der Adresse
**Fällig:** Phase:MVP – im SKELETON genügt die Navigationsleiste als Rückweg
**Problem:** Regel des Users (Abschluss-Triage CROSS-navigation run-3): Eine Fehlerseite bietet einen Rückweg an, der sich aus der Adresse ableitet – ein Direktlink auf ein Rezept führt „Zur Rezept-Liste", ebenso für jede andere Seite, soweit möglich; ohne solchen Kontext ein Button zur Startseite. „Rezept nicht gefunden." (ADR-S135-5) tut das bereits; Client/src/pages/NotFoundPage.tsx („Seite nicht gefunden.") zeigt nur die Meldung, auch bei Pfaden mit Kontext wie /recipes/abc/x.
**Behebung:** Szenarien für die Fehlerseiten im MVP-Workshop (features/navigation.feature): Rückweg je Adress-Kontext und Button zur Startseite ohne Kontext; danach umsetzen, ggf. eine gemeinsame Fehlerseiten-Komponente mit „Rezept nicht gefunden.".
**Aufschubgrund:** User – in der Abschluss-Triage von CROSS-navigation run-3 als MVP eingestuft

---

## TD-S150-5 — Host-Header-Prüfung offen (AllowedHosts *)
**Fällig:** Phase:MVP – sobald die Anwendung über das Heimnetz hinaus oder dauerhaft im Netz betrieben wird
**Problem:** Server/appsettings.json setzt AllowedHosts auf "*": Der Server nimmt jeden Host-Header an. Seit das Backend auch die Oberfläche ausliefert (ADR-S150-2), ist der ganze Server unter jedem Namen erreichbar, unter dem er im Netz auftaucht (Befund des Sicherheits-Reviews zur SPA-Auslieferung).
**Behebung:** AllowedHosts auf die tatsächlichen Hostnamen des Deployments einschränken (je Umgebung in appsettings.<Umgebung>.json) und zusammen mit HTTPS und CSP aus nfr.md#NFR-security einführen.
**Aufschubgrund:** User – in der Abschluss-Triage als MVP-Thema vermerkt, in SKELETON läuft die Anwendung nur lokal im Heimnetz

---

---

## TD-S151-1 — Rezeptformular: keine Sperre und kein Ladezustand während des Speicherns
**Fällig:** Szenario:„Backend liefert Serverfehler beim Speichern – Formular bleibt offen", Phase:MVP – erstes Szenario, das das Formular nach einem laufenden Speichern beobachtet; es ist noch keinem Lauf zugeordnet, daher der Phasen-Backstop
**Problem:** ADR-S135-4 fordert, dass während des Speicherns „Speichern“, „Abbrechen“, die Felder, „Schritt hinzufügen“ und das Absenden per Enter gesperrt sind. Umgesetzt ist nur die Sperre der Navigation mit Eingaben (useDiscardQuestion, run-15). Folgen (geprüft am Code von Client/src/pages/CreateRecipePage.tsx, S151; nicht im Browser nachgestellt): Ein zweites Absenden während des Speicherns ist möglich (Doppel-Submit, zwei Rezepte); zwei Antworten können sich überholen; Klicks auf Navigationsleiste, Abbrechen oder Browser-Zurück tun mit Eingaben während des Speicherns still nichts, ohne sichtbaren Ladezustand.
**Behebung:** Szenarien für Sperre und Ladezustand ergänzen (gherkin-workshop), dann Felder und Schaltflächen während des Speicherns sperren und an „Speichern“ einen Ladezustand zeigen; die Querschnitts-Suite nach ADR-S112-5 dabei mitmigrieren.
**Aufschubgrund:** User – in der Abschluss-Triage von run-15 entschieden: braucht eigene Szenarien und die Migration der Querschnitts-Suite (ADR-S112-5)

---

## TD-S153-1 — Rückgängig-Toast: geteilte Umsetzung fehlt vor der zweiten Seite (ADR-S112-5 Schritte 4–6)
**Fällig:** Szenario:„Eine Vormerkung auf der Vorgemerkt-Seite entfernen" – die Vorgemerkt-Seite ist die zweite Seite mit Rückgängig-Toast; vorher als eigener Durchlauf
**Problem:** Löschen mit Rückgängig-Toast lebt nur in der Zutaten-Seite. Die parametrisierte Suite Client/e2e/interaction.spec.ts trägt noch US-904-Testnamen und `// Szenario:`-Verweise, die Szenarien stehen in features/ingredients.feature, und Client/e2e/pages/listPage.ts verlangt von jeder Seite alle Fähigkeiten (Anlege-Dialog inklusive). Ohne die Schritte 4–6 aus ADR-S112-5 baute die Vorgemerkt-Seite das Verhalten nach, statt es zu teilen.
**Behebung:** Eigener Durchlauf vor US-803 run-5: (4) Toast und Löschen-mit-Rückgängig aus der Zutaten-Seite in eine geteilte Umsetzung ziehen (useDeleteWithUndo<T>; Wiederherstellen als Parameter, weil Vormerkungen per PUT statt POST …/restore zurückkommen; Verb des Toasts je Seite). (5) Alle Szenarien, die interaction.spec.ts je Seite ausführt, nach features/interaction.feature umziehen (als SKELETON und umgesetzt), umtaggen, Tests umbenennen; Testnamens-Konvention für @CROSS-Szenarien entscheiden. (6) Import-Guard (ESLint no-restricted-imports) setzen. Dazu listPage.ts in Fähigkeiten aufteilen wie touchTargetPage.ts. Die Anmeldung der Vorgemerkt-Seite in listPages.ts gehört zu run-5.
**Aufschubgrund:** User – im Workshop von US-803 entschieden: der Umbau läuft als eigener Durchlauf unmittelbar vor dem Entfernen, nicht jetzt

---
