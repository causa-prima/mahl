# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss archivieren (Reihenfolge): Offene Fragen → `decisions.md` | Abgeschlossene Schuld → `decisions.md` | Alte Prioritäten → `lessons_learned.md`
> Vollständige Session-Logs: `docs/history/sessions/` | Alle Entscheidungen: `docs/history/decisions.md`

**Letzte Aktualisierung:** 2026-03-26 (Session 042)

---

## Aktueller Stand

**Phase:** SKELETON 🔄 – Neustart beschlossen

**Letzter Stand (Session 042, 2026-03-26):** Dokumentations-Großüberarbeitung abgeschlossen.

---

## Was ist implementiert

Backend (C#, PostgreSQL, EF Core) vorhanden – wird nverworfen. Frontend noch nicht implementiert. Hooks bleiben erhalten, werden aber auf Redundanz mit statischer Codeanalyse geprüft (siehe Technische Schuld).

---

## Nächste Prioritäten (Reihenfolge bindend)

1. **Neustart**: Backend verwerfen, mit BDD/Gherkin + Outside-In ATDD neu beginnen
2. **STJ/Deserialisierung verifizieren** (bleibt relevant für Neustart): (a) 400 oder 500 bei ungültigem URI-String? (b) STJ serialisiert `Uri` via `OriginalString`?
3. **CA1062**: HTTP-Grenz-Validierung (Model Validation oder FluentValidation)

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch |
| CA1062 | HTTP-Grenz-Validierung (null-DTOs trotz NRT) | Hoch |
| Neustart | Backend verwerfen + ATDD-Neustart | Hoch |
| Hooks-Review | Prüfen ob Hooks durch statische Analyse (Session 035) obsolet geworden sind | Mittel – blockiert durch CA1062 |
| Dependency-Hook | Hook implementieren der package.json/.csproj-Änderungen mit nicht-gelisteten Paketen blockiert (Allowlist: `docs/DEPENDENCIES.md`) | Mittel – vor oder beim Rewrite |

---

## Offene Fragen

_Keine._
