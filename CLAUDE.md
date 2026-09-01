# CLAUDE.md – Navigationszentrale

## WSL-native Toolchain

.NET und Node laufen **nativ in WSL** (Repo auf ext4). Details: `docs/process/dev-workflow.md` (Sektion "[WSL-native Toolchain](docs/process/dev-workflow.md#DEV-wsl-toolchain)").

---

## Navigation: Was lese ich für welche Aufgabe?

| Aufgabe | Lies |
|---------|------|
| Session starten / Status prüfen | `docs/AGENT_MEMORY.md` |
| Szenario implementieren | Skill `implementing-scenario` verwenden (ein Szenario pro Durchlauf, Double-Loop TDD) |
| Backend-Endpoint schreiben | `docs/reference/architecture.md` (inkl. [Hexagonal Architecture](docs/reference/architecture.md#ARC-hexagonal)) → `docs/reference/skeleton-spec.md` ([API-Sektion](docs/reference/skeleton-spec.md#SKE-api-routen)) |
| E2E Testing / BDD/Gherkin / Outside-In ATDD | `docs/process/e2e-testing.md` |
| C#-Code schreiben (Backend, Tests) | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-csharp.md` (enthält Verweise auf ROP/SumTypes/Stryker-Ergänzungen) |
| TypeScript/React-Code schreiben | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-typescript.md` |
| Python schreiben (Scripts, Hooks, Checks unter `.claude/**`) | `docs/guidelines/coding-guideline-general.md` → `docs/guidelines/coding-guideline-python.md` (andere Maßgaben als Produktcode – der Grund steht dort) |
| Frontend-UX / Interaction Design | `docs/guidelines/coding-guideline-ux.md` |
| Allgemeine Coding-Prinzipien (KISS, Naming, Komplexität) | `docs/guidelines/coding-guideline-general.md` |
| Datenbank-Schema ändern | [Datenbank-Workflow](docs/process/dev-workflow.md#DEV-datenbank-workflow) (Drop+Recreate vs. Migrations) → [Projekt-Struktur](docs/reference/architecture.md#ARC-projekt-struktur) (wo DbTypes liegen) |
| Domain-Logik / Fachbegriff | `docs/reference/glossary.md` → `docs/reference/architecture.md` |
| Code schreiben / TDD / Mutation Testing | `docs/process/tdd-process.md` (Red→Green→Refactor gilt immer) + `docs/process/dev-workflow.md` |
| Build / Run / Migration | `docs/process/dev-workflow.md` |
| Definition of Done / NFRs | `docs/process/nfr.md` |
| Autor-Self-Review | `docs/process/review-checklist.md` |
| Review-Agent beauftragen | Skill `review-code` (Scope-Matrix + Spawning via `subagent_type`) |
| Workflow-/Prozess-Audit durchführen | Skill `review-workflow` verwenden |
| Projektdokumentation prüfen | Skill `review-docs` verwenden |
| Learnings dokumentieren | `docs/kaizen/lessons_learned.md` (Format: `docs/kaizen/process.md`) |
| Tracker-Eintrag lesen/schreiben (OBS, LL, TD, OQ, ADR) | `python3 .claude/scripts/tracker.py` zeigt, welches Werkzeug welchen Tracker pflegt und welche Befehle es kennt – dann `obs.py` / `lessons.py` / `td.py` / `oq.py` / `decisions.py`, statt Read/Edit auf der ganzen Datei |
| Wohin geht das Read-/Token-Budget? | `python3 .claude/scripts/read-breakdown.py` (nach Session-Art), `tool-usage.py` |
| Hat ein Guard/Hook je angeschlagen – oder fällt er lautlos aus? | `python3 .claude/scripts/guard-stats.py` (Teil der Retro) |
| Wo fehlen Tests im Prozess-Code? | `python3 .claude/scripts/coverage-run.py` (Metrik, kein Gate – Teil der Retro) |
| Abschnitt einer Doku lesen (statt Volldatei) | `python3 .claude/scripts/doc.py toc <datei>` zeigt die Abschnitte, `doc.py get <ANKER>` holt einen davon |
| Abschnitt referenzieren / Anker prüfen | `python3 .claude/scripts/anchors.py list\|check\|refs <ANKER>`; Nummern statt Namen findet `ordinale.py` |
| Was steht schon in einer Testdatei? | `python3 .claude/scripts/test-inventory.py <datei>` – Testnamen mit Zeilenbereich |
| Verhaltensprinzipien (immer gültig) | `docs/kaizen/principles.md` |
| Maßnahmen-Tracking | `docs/kaizen/countermeasures.md` |
| Retro durchführen | Skill `kaizen` verwenden |
| Technische Schuld tracken | `docs/tech-debt.md` |
| Offene Fragen / geparkte Diskussionen | `docs/open-questions.md` |
| Wohin gehört dieser Eintrag – ADR, TD, OQ oder OBS/CM/LL? | Sektion "[Ablage: in welchen Tracker gehört dieser Eintrag?](#CLA-ablage)" (unten in dieser Datei) |
| Langsame Befehle dokumentieren | `docs/process/slow-commands.md` |
| Befehl ausführen (Timeout / Auswahl) | `docs/process/dev-workflow.md` (Sektion "[Befehlsauswahl & Timeouts](docs/process/dev-workflow.md#DEV-befehlsauswahl)") |
| Warum wurde X so entschieden? | `docs/history/adr.md` (via `python3 .claude/scripts/decisions.py`) |
| Was passierte in Session X? | `git log --grep='^Session-Ende: X$'` – die Commit-Nachricht **ist** die Session-Historie (Zwischen-Commits stehen davor, bis zur vorigen Marke). Wörtlicher Verlauf: Skill `recall-session` |
| Neuen Agenten beauftragen | `.claude/agents/` (bestehende Definitionen als Vorlage) + Skill `review-code` |
| Interface/API designen (Design It Twice) | Skill `design-an-interface` verwenden |
| Session abschließen | Skill `closing-session` verwenden |

---

<a id="CLA-ablage"></a>
## Ablage: in welchen Tracker gehört dieser Eintrag?

**Einstieg für alle Tracker.** Der erste Schnitt unten entscheidet Produkt vs. Prozess und gilt für
jeden Eintrag; die beiden folgenden führen die **produkt**-seitigen aus (ADR/TD/OQ). Fällt er auf
Prozess, geht es in [„Wann gehört etwas wohin?"](docs/kaizen/process.md#KPR-wohin) weiter (OBS/CM/LL) –
hier nicht wiederholt. Die Datei-Header aller Tracker tragen je die Aufnahmebedingung ihrer Datei und
verweisen hierher für die Abgrenzung untereinander.

Drei Trennschnitte, jeder für sich eindeutig:

| Schnitt | Trennt |
|---|---|
| **Produkt vs. Prozess** | ADR/TD/OQ ↔ OBS/CM/LL |
| **entschieden vs. offen** | ADR/TD ↔ OQ |
| **terminal vs. terminierend** | ADR ↔ TD |

**Schnitt „Produkt vs. Prozess".** Produkt ist der Code samt Build-/Test-Kette
(`stryker-config.json`, `playwright.config.ts`, `Directory.Build.props`) → ADR/TD/OQ.
Prozess ist, wie gearbeitet wird (`.claude/**`, `docs/process/`, `docs/kaizen/`) →
OBS/CM/LL; deren Taxonomie steht vollständig in
[„Wann gehört etwas wohin?"](docs/kaizen/process.md#KPR-wohin) und wird hier nicht wiederholt.

**Schnitt „entschieden vs. offen".** Steht die Antwort noch aus und ist sie mit dem User
zu klären → `docs/open-questions.md`. Alles Entschiedene fällt unter den nächsten Schnitt.

**Schnitt „terminal vs. terminierend".** Operativer Test:

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

**Ort der Regel – verworfene Alternativen (S118).** Die Übersicht steht hier, weil `CLAUDE.md` das
einzige Dokument mit garantiertem Lese-Trigger und ohnehin Routing-Zentrale ist; die
Aufnahmebedingung je Tracker steht zusätzlich in dessen Datei-Header. Verworfen: die Übersicht in
`docs/kaizen/process.md` – die dortige Tabelle ist die Kaizen-Taxonomie und dort vollständig, die
zunächst vermutete Lücke war ein Fehlschluss. Ebenfalls verworfen: eine eigene Datei – sie hätte
keinen Lese-Trigger.

---

## Globale Skills: Vorrang lokaler Regeln

Globale Skills (z.B. `tdd`) gelten als Baseline. Lokale Skills und Docs ergänzen sie und gewinnen bei Konflikten – insbesondere:
- TDD-Prozess: Skill `write-code` **ergänzt** den globalen `tdd`-Skill um Guideline-Pflichten, PFLICHT-OUTPUT und Selbst-Review; TDD läuft als Schritt [Implementieren via TDD](.claude/skills/write-code/SKILL.md#WRC-tdd) von `write-code`. Bei Konflikten gelten `write-code` und `docs/process/tdd-process.md`.

---

## Entscheidungsfreiheit

**Technische Details** (Validierungsregeln, Error Codes, Schema-Details, UI-Details) → **selbst entscheiden & in `docs/history/adr.md` dokumentieren**

**Business-Logic, Architektur-Änderungen, unklare Requirements** → **nachfragen**

Faustregel: Hat die Entscheidung Business-Impact? Nein → entscheide selbst. Ja → frage nach.