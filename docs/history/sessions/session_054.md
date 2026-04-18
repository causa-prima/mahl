# Session 054 – 2026-04-12

## Themen

1. **Retro-Script: Severity-Gewichte auslagern**
2. **Resilience-Architektur definieren**
3. **features/resilience.feature anlegen und reviewen**
4. **gherkin-workshop erweitern**

---

## Retro-Script Refactoring

- `kaizen_constants.py` neu angelegt mit `SCHWERE_WEIGHTS`
- `jenga_score.py`: `DEDUCTIONS`-Dict durch Import ersetzt, Variable direkt durch `SCHWERE_WEIGHTS` ersetzt (kein Alias)
- `retro_report.py`: Zeitreihen, Kategorie-Stack und Trendanalyse nutzen jetzt Schwere-Score statt Anzahl; Chart-Titel aktualisiert

## Resilience-Architektur

- Mini-Workshop US-904: kein story-spezifisches Resilience-Verhalten → keine neuen Szenarien für ingredients.feature
- grill-me: querschnittliche Fehlerbehandlung vollständig entschieden:
  - 3 Fehler-Kategorien: Netzwerkfehler (TypeError + 504), Serverfehler (500/502/503), Auth (401/403)
  - Toast-Texte, Console.error-Format (`[API Error] METHOD /path | Status: NNN | TraceId: xxx`)
  - Pessimistisches UI, kein automatisches Retry
  - ProblemDetails: Standard für Exceptions, `errorCode` + `detail` für Domain-Fehler
  - Draft-Saving-Prinzip: per Feature, nicht global
  - Logging: Applikationslogs und Access Logs getrennt; Serilog/Produktion → MVP-Scope
- Entscheidungen in `docs/history/decisions.md` (neuer Abschnitt "Querschnittliche Fehlerbehandlung") dokumentiert

## features/resilience.feature

- 5 Szenarien angelegt: Netzwerkfehler/Serverfehler je für Laden und Speichern + Auth-Redirect
- Zwei Review-Durchläufe (angepasster Review-Agent-Prompt mit decisions.md als Kontext):
  - Iteration 1: 2 CRITICAL (Tag-Konvention), 3 HIGH (UI-Zustand, Auth, vager When-Schritt) behoben
  - Iteration 2: 2 MEDIUM (Given/When-Reihenfolge Speichern-Szenarien, Auth-Szenario-Struktur) behoben
- E2E_TESTING.md: `@NFR-<domain>` und `@NFR-<domain>-<typ>` als eigene Tag-Klasse dokumentiert

## gherkin-workshop Erweiterungen

- Schritt 1, Frage-Kategorien: „Technische Fehler" und „Draft-Saving" neu hinzugefügt
- Abschluss-Bedingungen Schritt 1: beide Kategorien als Pflicht-Checkpoint
- Review-Agent-Prompt (`references/agent-review.md`): zwei neue Kontext-Felder (Resilience-Entscheidung, Draft-Saving-Entscheidung)

---

## Offene Punkte

Keine.
