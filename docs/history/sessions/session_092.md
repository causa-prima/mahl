# Session 092 – 2026-06-22

**Phase:** SKELETON
**Fokus:** US-904-Szenario `@US-904-error` „Zutat mit Namen aus nur Leerzeichen anlegen schlägt fehl" (Trim-Variante) + vertiefte Stryker-Mutation-Level-Analyse

## Implementiert

### Szenario (via implementing-scenario)
- **Befund Schritt 0:** Das Szenario ist **bereits vollständig durch existierenden Code erfüllt**. `NonEmptyTrimmedString.Create` trimmt vor der Validierung (`input?.Trim()`, ADR-S051-1) → `"   "` wird leer → `NameEmpty` → feld-keyed 422. Frontend hat keine clientseitige Validierung (sendet roh). E2E-Test war beim ersten Lauf **grün** (empirisch verifiziert) – **keine RED-Phase, kein Produktionscode**, reiner Regressions-Pin (GRUNDSATZ-Abweichung, mit User abgestimmt).
- **Tests (Pin):** E2E `WhitespaceName` + Backend-Integrationstest hinzugefügt. Beide grün, Backend-Stryker 100% (unverändert, kein Prodcode).

### Test-Refactoring (aus Review-Round-1, Finding valide)
- **Backend parametrisiert:** Die drei `[Fact]`-Fehlertests (EmptyName/WhitespaceName/EmptyUnit) → ein `[Theory]` mit `[InlineData]` (`US904_Error_CreateIngredient_InvalidInput_Returns422WithFieldKeyedError`). Exakt das Beispiel aus `tdd-process.md` „Parametrisierte Tests".
- **E2E DRY:** Dreifach kopierter Setup-Block (networkidle + includeHidden-Locator + Count + Kommentar) in Helper `captureIngredientList(page)` extrahiert. **Keine** Loop-Parametrisierung der E2E-Tests: ADR-S041-7 / `check-e2e-scenario-ref.py` verlangen pro Gherkin-Szenario einen `// Szenario:`-Kommentar über `test(` (DONE-Backbone) – ein Loop bricht den Poka-Yoke-Hook (`_has_szenario_comment_above` stoppt an der `for`-Zeile). F1-für-E2E daher begründet abgelehnt.

## Vertiefung: Stryker & `.Trim()` (zwei User-Fragen)
- **Warum 100% Mutation Score trotz fehlendem Trim-Test?** `.Trim()` wird im Default-Level „Standard" **nicht** mutiert (String-Methods erst ab Advanced). Branch Coverage ist blind (Trim sitzt auf nicht-verzweigender Anweisung; die `IsNullOrEmpty`-Branches deckt `""`/valide längst). Empirisch: Stryker auf der Datei = 3 Mutanten, alle killed, 0 Survivor → kein Trim-Removal-Mutant existiert. → LL-S092-1.
- **Gold-Plating-Befund:** Git zeigt `.Trim()` seit Skeleton-Baseline (`e7686c4`) – vor jedem treibenden Szenario, ungetestet/ungetrieben über mehrere Commits, von keinem Gate gefangen.
- **`Trim() → ""` ist ein schwacher Mutant:** Identität (`x.Trim() → x`) wäre aussagekräftig. gh-Recherche: Mutator stammt aus Issue #2868 (0 Kommentare, ungeprüft gemerged via PR #2904); kein Issue diskutiert die Wahl. Upstream-Schwäche, für uns irrelevant (P4 verworfen).
- **Mutation-Level-Entscheidung:** Standard bleiben (nicht Advanced). Advanced schließt den Trim-Blindspot nicht (`Trim()→""` trivial vom Happy-Path getötet) und verteuert das 100%-Gate. Complete ist laut Doku ≡ Advanced (verifiziert). → ADR-S092-1.

## Doku / Tracking
- **ADR-S092-1** angelegt (Mutation-Level Standard beibehalten; Revisit-Trigger sourceUrl-Regex / Duplikat-Casing).
- **LL-S092-1** (Mutation/Coverage blind für Datentransformations-Korrektheit).
- **OBS-S092-1** (doppelte LL/OBS-Erfassung implementing-scenario 6.1 ↔ closing-session).

## Probleme / Findings
- **Review-Round-1:** valides ❌ (Parametrisierungs-Pflicht) → behoben.
- **Review-Round-2:** ❌ FE-2 (Helper koppele an MUI) als **false positive** abgelehnt – `includeHidden` ist nötig, weil der Dialog im Fehlerfall offen bleibt (Hintergrund aria-hidden); die vorgeschlagene Alternative greift nicht. ⚠️ BE-2/FE-4 als schwach abgelehnt (Guideline-Vorlage nutzt selbst generischen Theory-Namen; `itemsBefore` ist treuer zu „bleibt unverändert" als `0`). FE-7 (Kommentar-Klarstellung) angewendet.
- ESLint: Helper-Param brauchte `Readonly<Page>` (`functional/prefer-immutable-types`).

## Entscheidungen
- Szenario als reiner Test-Pin behandeln (kein Prodcode, keine RED-Phase) – mit User abgestimmt.
- Backend parametrisieren; E2E bewusst NICHT (ADR-S041-7-Vorrang).
- Mutation-Level Standard beibehalten (ADR-S092-1).

## Nachtrag (gleiche Session)
- **„Einheit aus nur Leerzeichen" ✅** – identische Trim-Faltung: ein `[InlineData("Salz","   ",…)]` im Backend-`[Theory]` + ein E2E-Test (Klon des Einheit-Falls). Kein Prodcode, Stryker 100% (25/25). Eigener Commit.

## Offene Punkte
- `@US-904-error` weiter: „beide Pflichtfelder leer" (= collect-all-Merge, TD-S090-1), Duplikat-/Reaktivierungs-Szenarien.
- OBS-S092-1 (+ offene S090/S091-OBS) für die nächste Retro.
