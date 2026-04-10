# Session 045 – 2026-04-02 – Prozess-Arbeit (Gherkin-Workshop + TDD-Klarstellungen)

## Was wurde gemacht

### Test-Infrastruktur aufgebaut (bleibt stehen)
- `Client/vite.config.ts` – Vite mit React-Plugin, Proxy /api → localhost:5059, Build-Output → Server/wwwroot
- `Client/playwright.config.ts` – Playwright mit Chromium, webServer auto-start, testDir: ./e2e
- `Client/tsconfig.playwright.json` – separates tsconfig für E2E-Tests
- `Client/tsconfig.json` – Playwright-Referenz ergänzt
- `Client/index.html`, `Client/src/main.tsx`, `Client/src/App.tsx` – minimales Bootstrap für Vite dev server
- `Client/e2e/ingredients.spec.ts` – erster E2E-Test (@US-904-happy-path, "Neue Zutat anlegen")
- Playwright Chromium installiert, E2E-Test **ROT bestätigt** (Button nicht gefunden)

### Prozess-Analyse und Korrekturen
- **ATDD-vs-Guidelines-Spannung** identifiziert und aufgelöst: E2E-Test = äußerer Loop (treibt Komponenten/Routing), Unit-Tests = innerer Loop (treibt Domain-Typen, Validierung). Branded Types in TypeScript sind Guideline-Pflicht, aber sie brauchen eigene Unit-Tests im inneren Loop, bevor sie implementiert werden.
- **TDD-Verstoß erkannt:** Implementierung (domain/ingredient.ts) vor rotem Unit-Test begonnen. Sofort korrigiert.
- **Gherkin-Vollständigkeitslücke** für US-904 identifiziert: Fehlende Szenarien (leere Liste, alphabetische Sortierung mit mehreren Einträgen, soft-deleted nie anzeigen).
- **Prozesslücke** dokumentiert: `implementing-feature` hat keinen Gherkin-Review-Schritt vor der Implementierung.
- **Szenario-Reihenfolge** als undokumentierter Standard identifiziert: happy-path → error → edge-case; innerhalb happy-path trivialster → komplexester Fall.

### TypeScript-Guideline aktualisiert
- `ValidationError`-Typ eingeführt: `{ readonly message: string }` statt rohem `string` als Fehlertyp in `Result<T, E>`
- Alle Beispiele in `CODING_GUIDELINE_TYPESCRIPT.md` auf `ValidationError` umgestellt

### Neuer Skill: `gherkin-workshop`
- Skill erstellt: `.claude/skills/gherkin-workshop/SKILL.md`
- Prozess: 6 Schritte – Kontext laden → Dialog mit User (Tracer Bullets + grill-me) → 3 parallele RE-Agenten (Example Mapping, State-Transition, Input-Partition) → Synthese → Review-Loop → Feature-File & Freigabe
- Durch skill-creator reviewt (1 Runde): alle HIGH/MEDIUM-Findings eingearbeitet
- **Verbleibend:** Skill braucht weitere Review-Runden (nur 1 von n durchgeführt)

### Diskutiert, aber nicht umgesetzt

#### SKELETON_SPEC.md / MVP_SPEC.md Audit (verschoben)

Diese Dateien sind historisch gewachsene „Entscheidungs-Logs ohne besseren Container". Sie
mischen vier konzeptuell verschiedene Typen von Inhalten, die unterschiedliche Heimaten haben:

| Typ | Beispiele aus den Specs | Richtiger Ort |
|-----|------------------------|---------------|
| **Explizite Entscheidung** | „IDs sind UUIDs (UUIDv7)", „Soft-Delete-Pattern", konkrete Fehlermeldungstexte wie `"Name darf nicht leer sein."`, „409-Varianten mit Code `ingredient_soft_deleted`" | `docs/history/decisions.md` |
| **Architektur-Constraint** | „Alle Listen alphabetisch sortiert nach Name", „kein PUT-Endpoint im SKELETON", „AlwaysInStock im SKELETON ohne Wirkung" | `docs/ARCHITECTURE.md` |
| **Behavioral Expectation** | „POST /api/ingredients gibt 409 bei Duplikat", „DELETE gibt 404 auch bei bereits soft-deleted", „GET-Listen überspringen korrupte Records" | Gherkin-Szenario – entsteht im `gherkin-workshop`, braucht keinen eigenen Spec-Container |
| **Abgeleitetes Impl.-Detail** | Exakte DTO-Feldnamen und -Typen, HTTP-Status-Codes die direkt aus den API-Guidelines folgen, Tabellen-/Spaltennamen die aus dem Domain-Modell emergieren | Emergiert aus Tests – braucht keinen eigenen Container; steht ggf. im Code |

**Vorgehen beim Audit (ein Eintrag nach dem anderen):**
1. Jeden Abschnitt der Spec lesen und dem Typ oben zuordnen
2. Typ **Explizite Entscheidung** → in `decisions.md` übertragen (Format: Entscheidung, Begründung, Datum/Session)
3. Typ **Architektur-Constraint** → in `ARCHITECTURE.md` an passender Stelle einbauen
4. Typ **Behavioral Expectation** → als offene Aufgabe markieren: „braucht Gherkin-Szenario im nächsten Workshop"
5. Typ **Abgeleitetes Impl.-Detail** → löschen (kein separater Container nötig)
6. Nach vollständigem Audit: SKELETON_SPEC.md / MVP_SPEC.md stark eindampfen oder löschen

**Wichtig:** Die Specs enthalten wertvolles Wissen aus früheren Diskussionen. Nichts löschen,
bevor es kategorisiert und ggf. migriert wurde. MVP_SPEC.md analog behandeln.

**Abgrenzung zu ARCHITECTURE.md:** Die Architektur selbst (Hexagonal Architecture, Schichten,
Dependency Rules) soll aus den Guidelines und Anforderungen emergieren – nicht vorspezifiziert
werden. ARCHITECTURE.md beschreibt nur Constraints, die explizit entschieden wurden und die
Gherkin-Szenarien und Implementierung rahmen.

#### `implementing-feature` → `implementing-scenario` (Umbau-Spezifikation)

**Warum:** Der aktuelle Skill implementiert eine gesamte User Story in einem Durchlauf.
„Wiederhole den Zyklus für jedes Verhalten der Story" ist unrealistisch: US-904 hat 6 Szenarien,
jedes mit E2E-Test, Backend-Test und Implementierung. Das sprengt jeden Kontext. Außerdem fehlt
die explizite Double-Loop-Struktur (äußerer E2E-Loop vs. innerer Unit-Test-Loop).

**Konkreter Umbau – was ändert sich:**

| Aspekt | Heute (`implementing-feature`) | Zukünftig (`implementing-scenario`) |
|--------|-------------------------------|-------------------------------------|
| **Input** | User Story ID (z.B. `US-904`) | Szenario-Tag (z.B. `@US-904-happy-path Scenario: Neue Zutat anlegen`) |
| **Scope** | Alle Verhaltensweisen einer Story | **Ein** Szenario pro Durchlauf |
| **Voraussetzung** | Gherkin-Check in Schritt 0 | Explizite Pflicht: `gherkin-workshop` muss zuerst gelaufen sein; Feature-File muss das Szenario enthalten |
| **TDD-Zyklus** | „Wiederhole für jedes Verhalten" (implizit) | Double-Loop explizit: äußerer Loop = E2E-Test (Playwright), innerer Loop = Unit-Tests je Schicht (Domain → Service → Komponente); jeder innere Test muss rot sein bevor Code geschrieben wird |
| **Done-Kriterium** | Alle Verhaltensweisen grün | Dieses eine Szenario grün; nächstes Szenario = neuer Skill-Aufruf |
| **AGENT_MEMORY** | Story-Status | Szenario-Status: welches Szenario abgeschlossen, welches ist als nächstes dran |

**Was bleibt gleich:** Architektur-Check (Schritt 0), Autor-Review, Review-Agenten, Learnings & Dokumentation – Struktur der 6 Schritte bleibt erhalten, nur Scope und TDD-Sektion ändern sich.

**Innerer Loop explizit (neu in Schritt 1–3):**
```
Für jede Implementierungsschicht, die das Szenario berührt:
  1. Schreibe den Test auf der passenden Ebene (Unit / Integration / E2E)
  2. Bestätige: Test ist rot
  3. Schreibe minimalen Produktionscode
  4. Bestätige: Test ist grün
  5. Refactor
  6. Weiter mit nächster Schicht
Ebenen-Reihenfolge (outside-in): E2E → Backend-Integration → Domain → (Service/Komponente)
```

**Aufruf-Konvention:**
```
/implementing-scenario @US-904-happy-path "Neue Zutat anlegen"
```

#### Weitere verschobene Punkte
- TDD_PROCESS.md: innerer Loop expliziter – Pflicht für Unit-Tests auch bei Domain-Typen/Services
- Gherkin US-904 Feature-File aktualisieren – wartet auf gherkin-workshop Durchlauf

## Offene Punkte für nächste Session

1. **gherkin-workshop weitere Review-Runden** – Skill ist noch nicht vollständig reviewt (nur 1 Runde)
2. **gherkin-workshop für US-904 anwenden** – Feature-File vervollständigen (fehlende Szenarien)
3. **TDD_PROCESS.md** ergänzen: innerer Loop / Unit-Test-Pflicht für Domain-Typen explizit
4. **`implementing-feature` → `implementing-scenario`** umbauen: ein Szenario pro Durchlauf
5. **SKELETON_SPEC.md Audit** – Entscheidungen vs. Implementation-Details trennen
6. **US-904 Implementierung** – erst nach gherkin-workshop und feature-file-Freigabe starten
