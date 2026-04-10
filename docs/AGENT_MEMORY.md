# Agent Memory – Mahl

> **Working Memory:** Immer aktuell. **Limit: ≤ 4 KB** (Hard-Grenzwert).
> Bei Überschuss: Mit User klären was wohin ausgelagert werden soll – sollte aber nie vorkommen.
> Session-Logs: `docs/history/sessions/` | Entscheidungen: `docs/history/decisions.md`
> Kaizen: `docs/kaizen/` (lessons_learned, principles, countermeasures, PROCESS)

**Letzte Aktualisierung:** 2026-04-10 (Session 052)

---

## Aktueller Stand

**Phase:** SKELETON 🔄 – Feature-File freigegeben, US-904 bereit zur Implementierung

**Letzter Stand (Session 052, 2026-04-10):**
- review-docs: 7 Findings behoben (Jenga-Trigger, Review-Scope, TDD Value-Type-Timing, kaizen-Kopf)
- retro_report.py: Archiv-Umbenennung, periodenbasierte Pattern-Erkennung, logarithmische Trendanalyse mit Farbkodierung
- Hooks-Review abgeschlossen: kein Hook durch Session-035-Analyzer obsolet

---

## Was ist implementiert

Kein Anwendungscode. Infrastruktur:
- `mahl.sln` + 3 `.csproj`-Projekte (Infrastructure, Server, Server.Tests)
- `Client/` mit allen Paketen, Vite+Playwright-Konfiguration, minimalem Bootstrap
- `features/ingredients.feature` (Gherkin, 23 Szenarien US-904 – freigegeben)
- Skill: `gherkin-workshop` (3 Review-Zyklen ohne skill-creator-Prinzipien)
- Skill: `implementing-scenario` (neu, kein Review-Zyklus)
- Skill: `kaizen` (reviewt, 6 Zyklen abgeschlossen)

---

## Nächste Prioritäten (Reihenfolge bindend)

1. **US-904 implementieren:** `implementing-scenario` je Szenario, beginnend mit erstem happy-path.
2. **gherkin-workshop US-904 V1:** Vor V1-Implementierung – Update (Bearbeiten) + Tags in `features/ingredients.feature` ergänzen.

---

## Technische Schuld

| Bereich | Problem | Priorität |
|---------|---------|-----------|
| STJ/Deserialisierung | 400 vs. 500 bei ungültigem URI; STJ via OriginalString unverifiziert | Hoch – erst ab US-602 relevant |

---

## Offene Fragen

_Keine._
