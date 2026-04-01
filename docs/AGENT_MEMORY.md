# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss archivieren (Reihenfolge): Offene Fragen → `decisions.md` | Abgeschlossene Schuld → `decisions.md` | Alte Prioritäten → `lessons_learned.md`
> Vollständige Session-Logs: `docs/history/sessions/` | Alle Entscheidungen: `docs/history/decisions.md`

**Letzte Aktualisierung:** 2026-04-01 (Session 043)

---

## Aktueller Stand

**Phase:** SKELETON 🔄 – Neustart in Arbeit

**Letzter Stand (Session 043, 2026-04-01):** Gesamter Anwendungscode gelöscht (Backend + Frontend). Nur Qualitäts-Configs behalten. Dependency-Hook implementiert. Bereit für ersten Gherkin-Einstieg (US-904).

---

## Was ist implementiert

Nichts. Sauberer Neustart. Hooks, Skills, Agents, Docs und Qualitäts-Configs sind vorhanden.

---

## Nächste Prioritäten (Reihenfolge bindend)

1. **US-904** (Zutaten CRUD): Gherkin → E2E-Test (rot) → Backend-Test (rot) → Implementierung (grün)
2. **STJ/Deserialisierung verifizieren**: (a) 400 oder 500 bei ungültigem URI-String? (b) STJ serialisiert `Uri` via `OriginalString`?
3. **CA1062**: HTTP-Grenz-Validierung (Model Validation oder FluentValidation)

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch |
| CA1062 | HTTP-Grenz-Validierung (null-DTOs trotz NRT) | Hoch |
| Hooks-Review | Prüfen ob Hooks durch statische Analyse (Session 035) obsolet geworden sind | Mittel – blockiert durch CA1062 |

---

## Offene Fragen

_Keine._
