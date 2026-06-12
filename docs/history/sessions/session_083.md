# Session 083 – US-904 „Zutat anlegen" (erster Full-Stack-Durchstich mit Persistenz)

**Datum:** 2026-06-12
**Phase:** SKELETON (US-904 Szenario – Full-Stack)
**Schwerpunkt:** Fünftes US-904-Szenario „Zutat anlegen" via `implementing-scenario` end-to-end (Frontend + Backend + erste EF-Migration); erster GET mit echten DB-Rows. Daraus: ETag-Scope-Klärung, Mutation-State-YAGNI-Entscheidung, Review-Loop mit 5 Auditoren, drei ADRs.

## Umgesetzt – Szenario

`@US-904-happy-path` „Zutat anlegen" als erster echter Full-Stack-Durchstich (vorher war der Backend nur Skelett: GET hartkodiert leer, `IngredientDbType` nur `Id`, keine Migration, keine Domain-Typen).

**Frontend** (gegen MSW, dann real):
- Dialog aus dem Empty-State-Branch **herausgezogen** (jetzt in befüllter UND leerer Liste verfügbar), `DialogTitle`/`DialogContent`, „Speichern" → POST → bei Erfolg Dialog schließen + `invalidateQueries` (Invalidate+Refetch, kein optimistic update).
- Liste rendert Name (primary) + Einheit (secondary) via `List`/`ListItem`/`ListItemText`.
- Neue Hooks `useResultQuery`/`useResultMutation` – **minimal/YAGNI** (nur success-Zweig bzw. Erfolgs-Seiteneffekt; keine 4er-`MutationState`-Union, kein `matchState`). Migration der Seite darauf löst den `useQuery`-eslint-disable auf.
- Die **3 zeitlich begrenzten Stryker-Suppressions** auf dem Non-Empty-Listen-Pfad: **entfernt** (das Szenario rendert erstmals eine befüllte Liste). `fetchIngredients` plain Promise → `ResultAsync`.

**Backend** (ersetzt die MSW-Mocks):
- `NonEmptyTrimmedString`-Value-Object (ROP, `OneOf<_, Error>`), `Ingredient`-Domain (`readonly record struct`, Defensive-Guards), `IngredientDbType` +Name/+DefaultUnit, DTOs, `OneOfExtensions` (existierte trotz Doc-Referenz nicht – neu angelegt).
- `POST /api/ingredients` → 201 + Body `{id,name,defaultUnit}` + Location (ADR-S068-1), `Guid.CreateVersion7()` serverseitig (ADR-S030-1); `GET` liest echt aus DB.
- Erste EF-Migration `InitialCreate` (Ingredients-Tabelle, `text` NOT NULL).
- `TestWebApplicationFactory` auf `InMemoryDatabaseRoot` umgestellt (ADR-S000-11, für POST→GET-Full-State-Assertion).

Beide Schichten Stryker **100 %**; Frontend-Hash `f4a00675504549ee`, Backend-Hash `2193a04058fe88c6`. E2E **grün** (warm).

## Entscheidungen

- **Mutation-State Minimal/YAGNI** (User): nur die Zweige, die das Szenario ausübt – keine spekulative `pending|error|idle`-Union. → **ADR-S083-2**.
- **ETag bewusst verschoben** (User, nach Klärung): ADR-S000-12/S058-1/S058-3 terminieren Collection-ETag für genau diesen „ersten GET mit echten Rows" – aber ETag ist ein technischer Caching-Concern ohne aktuellen Konsumenten (react-query macht keine Conditional-Requests). → eigener Folgezyklus (Frontend-Conditional-Layer + Backend-Collection-ETag), getrieben durch Service-Client-/Integrationstests, NICHT E2E.
- **GET mappt DB→DTO direkt** (kein `ToDomain()`-Roundtrip): DB-Inkonsistenz-Fehlerzweig aufs dedizierte Szenario verschoben (analog Recipes ADR-S039-3). → **ADR-S083-1**.
- **ADR-S000-3** als „noch nicht implementiert" klargestellt (Soft-Delete-Filter/`DeletedAt` existieren bewusst noch nicht – YAGNI).

## Review-Loop (5 Auditoren, ohne Iterations-Vorwissen)

Kein ❌-Defekt am Szenario. ❌-eingestufte Findings waren Doku-/Foundation-Entscheidungen (ADR-Drift, projektweite UX-Foundation). Umgesetzt (günstig, vom User freigegeben):
- **Test F1:** POST-Kontrakt-Assertion (Content-Type/Body) aus dem MSW-Handler in den Then-Block gezogen (Capture-Pattern) – läuft sonst still nie.
- **Test F17:** `body.Should().NotBeNull()` vor `body!`-Zugriffen (sprechende Meldung statt NRE).
- Hooks-Kommentare um ADR-S083-2-Referenz ergänzt.
Beide Schichten danach re-verifiziert (100 %).

## Probleme / Friktion

- **Cold-Start-Race im E2E:** Der initiale Listen-GET (JIT-Warmup ~2,3 s) war noch *in flight*, als der POST/Invalidate feuerte → react-query koalesziert und nutzt das stale leere Ergebnis (kein zweiter GET). Test-Umgebungs-Artefakt (warmer Server → kein Race), aber legt einen realen Robustheits-Punkt offen → Fix gehört zum pending-State-Szenario. E2E mit warmem Backend + sauberer DB grün.
- **Dev-Postgres-Schema-Drift:** veraltete `Ingredients`-Tabelle (alter `EnsureCreated`) vs. leere Migrations-History → `relation already exists`. Volume-Reset (`docker-compose down -v`) + Migration löste es.
- **qa-check gibt bei DLL-Lock/Build-Fehler still einen veralteten Report-Hash aus** (verwaister `mahl.Server`-Prozess sperrte `mahl.Infrastructure.dll`) → könnte als gültige Übergabe fehlinterpretiert werden.
- Konkurrierende Stryker-Läufe teilen `.claude/tmp/stryker_frontend_out.txt` → File-Lock-Race.
- Stryker-disable-Kategorien unterspezifiziert (ADR-S041-9 tief in adr.md; `Conditional` für Ternär-`default(T)`-Guard fehlt in der Kategorien-Tabelle).
- Session-Limit (Reset 17:00) blockierte die erste Review-Agenten-Runde temporär.

## Offene Punkte

- **Nächstes:** ETag-Querschnitts-Zyklus (s. AGENT_MEMORY) inkl. ADR-S041-5-Addendum (nicht-E2E-beobachtbare Anforderungen auf der obersten beobachtbaren Schicht testen) + ADR-S000-12-Präzisierung.
- Danach @US-904-error-Szenarien (erzwingen die `NonEmptyTrimmedString`-Validierung → ADR-S000-4-Suppression fällt weg).
- **Geparkte Diskussionen** (mit User): (1) ADR vs. technische Schuld – Taxonomie (dauerhafte Architekturentscheidung = ADR; Doku konkreter Code-Ausnahmen = Tech-Debt; ADR-S000-3/S000-4/S083-1/2 ggf. eher Tech-Debt). (2) Getypte IDs (`IngredientId` vs. rohes `Guid`) + ADR-S030-1-Neuformulierung; „kanonisches Beispiel ist kein Dogma".
