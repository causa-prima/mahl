# Session 094 – 2026-06-24

**Phase:** SKELETON
**Fokus:** US-904 Formular-/Dialog-UX-Baseline – **Spec + Prozess-Härtung** (keine Implementierung; TDD folgt in Folge-Sessions via `implementing-scenario`)

## Implementiert (Spec/Doku, kein Produktionscode)

### Feature-Datei (`features/ingredients.feature`)
- **B1 Affordance** – neues Happy-Path-Szenario „Pflichtfelder im Dialog sind als solche markiert" (getestet beim Öffnen).
- **B2 Autofokus** – neues Happy-Path-Szenario „Beim Öffnen … Fokus auf dem ersten Feld" (inkl. „erstes Eingabefeld"-Assert, E2E visuell-erstes).
- **B3 Fokus aufs erste Fehlerfeld** – Asserts an **bestehende** Error-Szenarien: „leere Einheit" → Fokus Einheit (Diskriminator), „beide leer" → Fokus Name (erstes). Minimal-Treiber-Menge, kein Retrofit aller Error-Szenarien.

### Guidelines / Skill / Review
- **`coding-guideline-ux.md` Prinzip 8 „Formular-/Dialog-Baseline"** neu: Custom (mit Szenario) vs. framework-geliefert (Guideline+Review). Enter-Submit via echtem `<form>` (einzeilig submit / mehrzeilig Newline), Escape/Fokus-Falle/Fokus-Rückkehr via MUI `Dialog`.
- **`gherkin-workshop/SKILL.md`** – Checklisten-Lücke geschlossen: Schritt 0.E um Prinzip 1 (Affordance); Schritt-1-UI-Checkliste um 4 Baseline-Items + **Träger-Regel** (framework→Guideline, custom→Szenario/Assert).
- **Review-Enforcement:** `review-checklist.md` (UI/UX-Punkt) + `ux-ui-auditor` (Prüfpunkt 5).

### ADR / Open Questions / Principles
- **ADR-S090-1 geschärft:** Client-Validierungs-Deferral steht jetzt auf **YAGNI** (nicht „Drift unlösbar"), inkl. front-loaded Argumentkette (nur Required lohnt; Drift via backend-getriebener Metadaten lösbar; Fokus-Code bleibt custom; Contract-Test braucht geteilte Fixture).
- **`open-questions.md`:** OQ-S094-1 (Client-Validierung, verweist auf ADR-S090-1) + OQ-S094-2 (Mobile-Szenarien, MVP/V1).
- **`principles.md`:** Referenz-Stabilitätsrichtung (volatil → stabil, nie umgekehrt).

## Diskussion & Entscheidungen (Kern der Session)
- **Root-Cause:** Der gherkin-workshop hatte keine Slots für Affordance/Fokus/Tastatur → Form-UX-Mechanik rutschte als Implementierungsdetail durch. Der Fokus-Mangel wurde von einem **UX-Review** (S090-Finding F1) statt vom Workshop entdeckt – Signatur einer Checklisten-Lücke.
- **Framework-vs-custom-Klassifikation** (User-Prinzip): framework-/HTML-nativ geliefert → Guideline + Review, **kein** Szenario; eigene Logik → Szenario/Assert.
- **B1-Träger = eigenes Szenario** (gegen „Assert im Error-Szenario"): Cardinal Rule of BDD (one behavior / single reason to fail); ausschlaggebend CA3 (Affordance ist statisch/pre-error → im Error-Szenario falscher Zeitpunkt) + CA4 (Fehl-Attribution korrumpiert Spec-als-Doku). „B" ist Pareto-dominiert (A bei Design, C bei echtem Anti-Drift).
- **B3 ist custom** genau weil Validierung server-only ist (ADR-S090-1); mit nativer Client-Validierung wäre der Fokus gratis.
- **Client-Validierung bleibt aufgeschoben** – nur Required lohnt realistisch; Uniqueness erzwingt ohnehin server-seitigen 422 + custom Fokus.

## Audit Ist-Zustand `IngredientsPage.tsx` (gegen Prinzip 8)
- B1 (markiert) ❌, B2 (autoFocus) ❌, B3 (Fokus aufs Fehlerfeld) ❌ → die offene Szenario-Arbeit.
- **B4 (Enter-Submit) ❌ + B5 (Escape) ❌ nicht verdrahtet** – kein `<form>`, kein `onClose`. Framework-Items, die im Code fehlen → die neuen Review-Checks greifen.
- B6 (Fokus-Falle) ✅, B7 (Fokus-Rückkehr) ✅ (MUI-Default).

## Offene Punkte (Implementierung folgt)
- B1/B2 rücken automatisch nach vorn (`{{NEXT_SCENARIO}}` → „Pflichtfelder … markiert"); verifiziert.
- **B3/B4/B5 werden NICHT vom Platzhalter gesurfaced** (Asserts an erledigten Szenarien / Nicht-Szenario-Items) → explizit in AGENT_MEMORY getrackt, bei der Baseline-Umsetzung (derselbe Dialog) mit-fixen.
- Mobile-Szenarien: OQ-S094-2 (MVP/V1).
