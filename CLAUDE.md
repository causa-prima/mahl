# CLAUDE.md – Navigationszentrale

## WSL-native Toolchain

.NET und Node laufen **nativ in WSL** (Repo auf ext4). Details: `docs/process/dev-workflow.md` (Sektion "WSL-native Toolchain").

---

## Navigation: Was lese ich für welche Aufgabe?

| Aufgabe | Lies |
|---------|------|
| Session starten / Status prüfen | `docs/AGENT_MEMORY.md` |
| Szenario implementieren | Skill `implementing-scenario` verwenden (ein Szenario pro Durchlauf, Double-Loop TDD) |
| Backend-Endpoint schreiben | `docs/reference/architecture.md` (inkl. Sektion 0c Hexagonal Architecture) → `docs/reference/skeleton-spec.md` (API-Sektion) |
| E2E Testing / BDD/Gherkin / Outside-In ATDD | `docs/process/e2e-testing.md` |
| C#-Code schreiben (Backend, Tests) | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-csharp.md` (enthält Verweise auf ROP/SumTypes/Stryker-Ergänzungen) |
| TypeScript/React-Code schreiben | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-typescript.md` |
| Frontend-UX / Interaction Design | `docs/guidelines/coding-guideline-ux.md` |
| Allgemeine Coding-Prinzipien (KISS, Naming, Komplexität) | `docs/guidelines/coding-guideline-general.md` |
| Datenbank-Schema ändern | `docs/process/dev-workflow.md` → `docs/reference/skeleton-spec.md` (DB-Sektion) |
| Domain-Logik / Fachbegriff | `docs/reference/glossary.md` → `docs/reference/architecture.md` |
| Code schreiben / TDD / Mutation Testing | `docs/process/tdd-process.md` (Red→Green→Refactor gilt immer) + `docs/process/dev-workflow.md` |
| Build / Run / Migration | `docs/process/dev-workflow.md` |
| Definition of Done / NFRs | `docs/process/nfr.md` |
| Autor-Self-Review | `docs/process/review-checklist.md` |
| Review-Agent beauftragen | Skill `review-code` (Scope-Matrix + Spawning via `subagent_type`) |
| Workflow-/Prozess-Audit durchführen | Skill `review-workflow` verwenden |
| Projektdokumentation prüfen | Skill `review-docs` verwenden |
| Learnings dokumentieren | `docs/kaizen/lessons_learned.md` (Format: `docs/kaizen/process.md`) |
| Tracker-Eintrag lesen/schreiben (OBS, LL) | `python3 .claude/scripts/obs.py` bzw. `lessons.py` – statt Read/Edit auf der ganzen Datei |
| Wohin geht das Read-/Token-Budget? | `python3 .claude/scripts/read-breakdown.py` (nach Session-Art), `tool-usage.py` |
| Was steht schon in einer Testdatei? | `python3 .claude/scripts/test-inventory.py <datei>` – Testnamen mit Zeilenbereich |
| Verhaltensprinzipien (immer gültig) | `docs/kaizen/principles.md` |
| Maßnahmen-Tracking | `docs/kaizen/countermeasures.md` |
| Retro durchführen | Skill `kaizen` verwenden |
| Technische Schuld tracken | `docs/tech-debt.md` |
| Offene Fragen / geparkte Diskussionen | `docs/open-questions.md` |
| Wohin gehört dieser Eintrag – ADR, TD, OQ oder OBS/CM/LL? | Sektion "Ablage: in welchen Tracker gehört dieser Eintrag?" (unten in dieser Datei) |
| Langsame Befehle dokumentieren | `docs/process/slow-commands.md` |
| Befehl ausführen (Timeout / Auswahl) | `docs/process/dev-workflow.md` (Sektion "Befehlsauswahl & Timeouts") |
| Warum wurde X so entschieden? | `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`) |
| Was passierte in Session X? | `docs/history/sessions/index.md` → ggf. spezifische Session-Datei |
| Neuen Agenten beauftragen | `.claude/agents/` (bestehende Definitionen als Vorlage) + Skill `review-code` |
| Interface/API designen (Design It Twice) | Skill `design-an-interface` verwenden |
| Session abschließen | Skill `closing-session` verwenden |

---

## Ablage: in welchen Tracker gehört dieser Eintrag?

**Einstieg für alle sechs Tracker.** Schnitt 1 unten entscheidet Produkt vs. Prozess und gilt für
jeden Eintrag; Schnitt 2 und 3 führen die **produkt**-seitigen aus (ADR/TD/OQ). Fällt Schnitt 1 auf
Prozess, geht es in `docs/kaizen/process.md`, Sektion „Wann gehört etwas wohin?" weiter (OBS/CM/LL) –
hier nicht wiederholt. Die Datei-Header aller sechs tragen je die Aufnahmebedingung ihrer Datei und
verweisen hierher für die Abgrenzung untereinander.

Drei Trennschnitte, jeder für sich eindeutig:

| Schnitt | Trennt |
|---|---|
| **Produkt vs. Prozess** | ADR/TD/OQ ↔ OBS/CM/LL |
| **entschieden vs. offen** | ADR/TD ↔ OQ |
| **terminal vs. terminierend** | ADR ↔ TD |

**Schnitt 1 – Produkt vs. Prozess.** Produkt ist der Code samt Build-/Test-Kette
(`stryker-config.json`, `playwright.config.ts`, `Directory.Build.props`) → ADR/TD/OQ.
Prozess ist, wie gearbeitet wird (`.claude/**`, `docs/process/`, `docs/kaizen/`) →
OBS/CM/LL; deren Taxonomie steht vollständig in `docs/kaizen/process.md`
(Sektion "Wann gehört etwas wohin?") und wird hier nicht wiederholt.

**Schnitt 2 – entschieden vs. offen.** Steht die Antwort noch aus und ist sie mit dem User
zu klären → `docs/open-questions.md`. Alles Entschiedene fällt unter Schnitt 3.

**Schnitt 3 – terminal vs. terminierend.** Operativer Test:

> *"Ist die Sache erledigt – bleibt dann etwas zu erklären übrig, das ohne diesen Eintrag
> unverständlich wäre?"*

- **Ja → ADR** (`docs/history/adr.md`). Der Eintrag wird `Superseded` und bleibt stehen.
- **Nein → TD** (`docs/tech-debt.md`). Der Eintrag verschwindet mit der Behebung ersatzlos.

**Keine Hybride.** Eine ADR trägt keinen Aufschub. Ist eine Entscheidung teils terminal, teils
aufgeschoben, wird der Aufschub-Teil ein eigener TD-Eintrag; die ADR behält nur den terminalen
Rest. Bleibt kein terminaler Rest, war es nie eine ADR. Formulierungen wie "aufgeschoben",
"vorerst", "bis zur Erweiterung", "technische Schuld" in einer ADR sind das Warnzeichen –
bei **neu** erfassten Einträgen blockt `.claude/hooks/check-adr-capture.py` sie mechanisch
(Escape für bewusste Einzelfälle: `adr-ok`-Marker im Eintrag). Bestehende Einträge bleiben
frei änderbar, sonst wäre Aufräumen unmöglich.

**Lifecycle – bewusste Abweichung von der Lehrmeinung.** Der Mainstream kennt kein Löschen von
ADRs (immutable, nur `Superseded`). Hier gilt: Eine ADR, die je **gegolten** hat, bleibt als
`Superseded` stehen, weil sie Projekthistorie erklärt – auch wenn keine Anwendungsstelle mehr
existiert. Eine ADR, die **nie** angewendet wurde, erklärt nichts und wird gelöscht (Präzedenz
S108: ADR-S000-3). Im Zweifel behalten. Kein `Rejected`-Archiv.

Herleitung und verworfene Alternativen: `docs/history/sessions/session_118.md`, Abschnitt E1.

---

## Globale Skills: Vorrang lokaler Regeln

Globale Skills (z.B. `tdd`) gelten als Baseline. Lokale Skills und Docs ergänzen sie und gewinnen bei Konflikten – insbesondere:
- TDD-Prozess: Skill `write-code` **ergänzt** den globalen `tdd`-Skill um Guideline-Pflichten, PFLICHT-OUTPUT und Selbst-Review; TDD läuft als Schritt 2 von `write-code`. Bei Konflikten gelten `write-code` und `docs/process/tdd-process.md`.

---

## Entscheidungsfreiheit

**Technische Details** (Validierungsregeln, Error Codes, Schema-Details, UI-Details) → **selbst entscheiden & in `docs/history/adr.md` dokumentieren**

**Business-Logic, Architektur-Änderungen, unklare Requirements** → **nachfragen**

Faustregel: Hat die Entscheidung Business-Impact? Nein → entscheide selbst. Ja → frage nach.