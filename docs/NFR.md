# Non-Functional Requirements & Definition of Done

<!--
wann-lesen: Nach jedem Feature und vor einem Phasen-Abschluss (Definition of Done), bei Fragen zu Performance/Security/Accessibility
kritische-regeln:
  - Alle 4 Gates der Definition of Done sind Pflicht – kein Gate darf übersprungen werden
  - Mutation Testing 100% ist Teil von Gate 1 (Suppressions für strukturell unerreichbaren Code erlaubt)
  - Gate 4 (Learnings & Dokumentation) ist kein optionaler Nachklapp – er ist Pflicht
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| Definition of Done | 4 Gates: Implementierung → Autor-Review → Review-Agenten → Learnings/Doku; Periodisches Review | Nach jedem Feature und bei Phasen-Abschluss |
| Performance | Metrik-Tabelle: Seitenwechsel, Button-Feedback, API-Latenzen, Lighthouse | Bei Performance-Fragen oder -Optimierungen |
| Accessibility | Best Practices: semantisches HTML, Touch-Targets, Kontraste | Bei Frontend-Implementierungen |
| Browser & Device Compatibility | Unterstützte Browser, Viewport-Prioritäten | Bei Frontend-Implementierungen |
| Security | HTTPS, Hashing, SQL-Injection, XSS, CSRF | Bei Auth/Security-relevantem Code |
| Reliability | ACID, Offline-Queue, Fehlermeldungen | Bei Fehlerbehandlung oder Offline-Features |
| Code-Qualität | Nullable Reference Types, Cyclomatic Complexity, Duplicate Code | Als Hintergrund zu Review-Findings |

> **Wann lesen:** Als Checkliste vor einem PR / Phasen-Abschluss, oder bei Fragen zu Performance/Security/Accessibility.

---

## Definition of Done

Ein Feature gilt als "Done" wenn **alle** Punkte abgehakt sind. Kein Punkt darf übersprungen werden.

### Gate 1: Implementierung

- [ ] **TDD Phase 1 (RED):** Test geschrieben und Fehlschlag bestätigt (*"schlägt fehl mit: ..."*)
- [ ] **TDD Phase 2 (GREEN):** Minimale Implementierung, Tests grün bestätigt
- [ ] **TDD Phase 3 (REFACTOR):** Refactoring-Checkliste durchgegangen, Ergebnis dokumentiert
- [ ] Unit Tests grün, Integration Tests grün (falls API-Endpoint)
- [ ] Mutation Testing durchgeführt (Ziel: 100%; Suppressions für strukturell unerreichbaren Code mit Begründung erlaubt)
- [ ] API in Swagger dokumentiert (falls Endpoint)
- [ ] Frontend-UI implementiert (falls relevant)
- [ ] Manueller Smoke-Test

### Gate 2: Autor-Review (vor Review-Agent)

- [ ] Autor-Checkliste aus `docs/REVIEW_CHECKLIST.md` (Teil A) vollständig durchgegangen
- [ ] Alle ❌-Findings sofort gefixt

### Gate 3: Review-Agenten (PFLICHT, kein Überspringen)

Immer laufen: Code Quality Agent, Functional Agent, Test Quality Agent.
Nur bei Frontend: UX/UI Agent. Nur bei Auth/Sicherheit: Security Agent.
Begründung angeben, wenn ein Agent ausgelassen wird.

- [ ] Alle relevanten Agenten beauftragt (Prompts: `docs/LLM_PROMPT_TEMPLATE.md` – Sektion "Agents")
- [ ] Nach jeder Code-Änderung: betroffene Agenten erneut ausgeführt (mit Begründung für ausgelassene)
- [ ] Wiederholung bis kein Agent mehr ❌-Findings hat
- [ ] ⚠️-Findings: gefixt ODER als technische Schuld in `docs/AGENT_MEMORY.md` eingetragen

### Gate 4: Learnings & Dokumentation (PFLICHT)

- [ ] Eintrag in `docs/history/lessons_learned.md` erstellt ("keine Learnings" nur mit Begründung akzeptabel)
- [ ] **Dokumentations-Änderungsvorschläge:** Für jede Kern-Dokument-Datei explizit geprüft: Anpassung nötig? Falls ja: Änderung dem User **vorschlagen** und auf Bestätigung warten – nicht eigenständig anpassen.
- [ ] `docs/AGENT_MEMORY.md` aktualisiert (Status, technische Schuld, offene Fragen)
- [ ] Commit mit aussagekräftiger Message (`US-XXX: ...`)
- [ ] Migrations erstellt (falls DB-Änderungen)

### Periodisches Review (Phasen-Abschluss)

Am Ende jeder Phase (SKELETON, MVP, V1, ...) zusätzlich:

- [ ] **Großes Code-Review:** Alle Review-Agenten auf das gesamte neue Code-Delta der Phase laufen lassen (nicht nur geänderte Dateien)
- [ ] **Lessons Learned Review:** Alle bisherigen Einträge in `docs/history/lessons_learned.md` durchsehen – wiederkehrende Muster → strukturelle Lösung vorschlagen
- [ ] **Dokumentations-Konsistenz:** Alle Kern-Dokumente auf Veralterung prüfen (Specs, Glossar, Architecture)

### Non-Functional (gilt immer)

- [ ] Performance: UI-Interaktionen < 100ms (Optimistic UI)
- [ ] Responsiveness: Mobile getestet (375px–428px)
- [ ] Error Handling: Nutzerfreundliche Fehlermeldungen (kein Stack-Trace für User)
- [ ] Security: Input-Validierung, keine XSS/SQL-Injection-Risiken

---

## Performance

| Metrik | Ziel |
|--------|------|
| Seitenwechsel | < 300ms (Optimistic UI, Skeleton Screens) |
| Button-Feedback | < 100ms |
| GET /shopping-list | < 200ms (p95) |
| Planungs-Algorithmus | < 2000ms (p95) |
| Einkaufsliste offline | Instant (IndexedDB, kein Server-Roundtrip) |
| First Contentful Paint | < 1.5s |
| Lighthouse Score | > 90 |

**Best Practices:** Optimistic UI, Code-Splitting per Route, Lazy Loading, Debouncing bei Suchen.

---

## Accessibility

Kein WCAG-Compliance-Ziel – aber Best Practices als Nebeneffekt guten Designs:
- Semantisches HTML (`<button>`, `<nav>`, `<main>`)
- Touch-Targets ≥ 44×44px (besser: 80×80px für Einkaufslisten-Kacheln)
- Ausreichende Kontraste für Lesbarkeit
- Keyboard-Navigation in logischer Reihenfolge

---

## Browser & Device Compatibility

**Unterstützte Browser:** Chrome/Edge (letzte 2), Firefox (letzte 2), Safari iOS (letzte 2). Kein IE11.

| Gerät | Viewport | Priorität |
|-------|---------|-----------|
| Smartphones | 320–767px | Primär (Einkauf + Kochen) |
| Tablets | 768–1023px | Sekundär |
| Desktop | 1024px+ | Funktional |

---

## Security

- HTTPS erzwungen (Produktion); localhost ohne HTTPS OK (Development)
- Passwort-Hashing: ASP.NET Core Identity Defaults (PBKDF2)
- SQL-Injection: EF Core parametrisiert automatisch
- XSS: Framework-Defaults + Content Security Policy
- CSRF: ASP.NET Core Anti-Forgery Tokens
- Sensitive Daten nicht loggen

---

## Reliability

- ACID-Transaktionen für DB-Operationen
- Offline-Queue synchronisiert bei Reconnect (ab MVP)
- Frontend zeigt nutzerfreundliche Fehlermeldungen, keine technischen Stack-Traces
- Bei Netzwerk-Fehler: Offline-Bereich zeigt Hinweis, crasht aber nicht

---

## Code-Qualität

- **Nullable Reference Types** – aktiviert global, Warnings als Errors
- **Cyclomatic Complexity** < 10 pro Methode
- **Keine** Duplicate Code Blocks > 5 Zeilen
- `Directory.Build.props` erzwingt Latest C# Language Version
