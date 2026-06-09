# Session 074 – 2026-06-08

## Ziel

ADR-System vollständig einführen: decisions.md → adr.md migrieren, decisions.py-Script implementieren, alle Skills/Agenten/Docs auf das neue System umstellen.

## Ergebnisse

### ADR-System eingeführt

- `docs/history/decisions.md` → `docs/history/adr.md` (Rename + Neuformat)
  - 63 Einträge im ADR-Format mit session-basierten IDs (`ADR-SXXX-N`)
  - Pro Eintrag: Status-Feld, Tag-Metadaten (zweistufig: `category:value`)
  - 49/63 Einträge mit verifizierten Quell-Session-Belegen; 14 als `ADR-S000-N` (Herkunft unbekannt)
  - Lifecycle-Suffix in ID (`-DEP`, `-SUP`) als bewusstes friction-Signal für stale Code-Kommentare

- `.claude/scripts/decisions.py` – neu:
  - `list [--tag TAG] [--status STATUS] [--full]` – Suche/Filter über alle ADRs
  - `get <ID...>` – Einzelabruf (akzeptiert `S041-1` oder `ADR-S041-1`)
  - `check` – scannt Server/ und Client/src/ auf `// ADR-SXXX-N` Kommentare, verifiziert Existenz
  - `tags [--category C]` – live approved tag list mit Counts
  - `refs [ID...]` – gruppiert Code-Referenzen nach ADR-ID

### Skills + Agenten migriert

- `implementing-scenario/SKILL.md`: `DEC-XXX` → `ADR-SXXX-N`, decisions.md → adr.md, Verifikation via `decisions.py refs`
- `gherkin-workshop/SKILL.md` + `references/agent-review.md`: decisions.md → adr.md (alle Vorkommen)
- `review-docs/SKILL.md`: decisions.md → adr.md
- `backend-layer-implementer.md` + `frontend-layer-implementer.md`: ADR-Referenz-Pflicht + cross-cutting lookup via `decisions.py list --tag scope:cross-cutting`

### qa-check.py erweitert

- CHECK 6 (ADR-Referenzen): ruft `decisions.py check` auf, stale Referenzen werden gefunden
- CHECK 6 fließt in Verifikations-Hash ein

### Docs migriert

`CLAUDE.md`, `ARCHITECTURE.md`, `CODING_GUIDELINE_CSHARP.md`, `CSharp-Stryker.md`, `DEV_WORKFLOW.md`, `REVIEW_CHECKLIST.md`, `SKELETON_SPEC.md`, `TDD_PROCESS.md`, `DEPENDENCIES.md`, `docs/stories/szenario_3_einkauf.md` – alle `decisions.md`-Referenzen auf `adr.md` umgestellt.

## Probleme

### Subagenten-Rename-Script: Sortier-Bug → korrupte ADR-IDs

Beim Umbenennen der Einträge von Temp-IDs auf finale ADR-IDs schrieb der Subagent ein Python-Script mit Two-Pass-Replacement, sortierte die Keys aber **nicht longest-first in Pass 2**. Ergebnis: ~30 ADR-IDs korrupt (z.B. `ADR-TEMP-10` → `ADR-S000-24` statt `ADR-S041-1`).

Fix: Eigenes `adr_fix.py` mit korrekter `sorted(..., key=len, reverse=True)` in beiden Passes. Script manuell geschrieben und ausgeführt, danach gelöscht.

### git index.lock beim Commit-Versuch

Stale `.git/index.lock` von einem vorherigen Prozess blockierte `git add`. Manuell entfernt.

### DEPENDENCIES.md Hook-Schutz

Der Dependency-Prozess-Hook blockiert alle direkten Edits auf `DEPENDENCIES.md` – auch reine String-Replacements ohne Paketänderung. User musste die drei verbleibenden `decisions.md`-Vorkommen manuell fixen.

## Offene Punkte

- `review-docs` in neuer Session starten: implementing-scenario SKILL + Subagenten besonders prüfen (die meisten Änderungen dort)
