# Session 078 – 2026-06-10

**Phase:** SKELETON (Kaizen-Retro + Taxonomie-Revision) – kein Produktionscode.

## Retro S070–S077 (Skill `kaizen`)

- **Noise-Review** (frischer Subagent gegen geschärfte Kriterien): 2 Einträge gelöscht – S077 „StrykerJS JSX-Disable" + S055 „VS-MSBuild/SDK" (statische Tool-/Infra-Fakten ohne Agenten-Verhaltensklasse).
- **Filter-Kriterien geschärft** (`process.md` + `kaizen`-SKILL + Template): 3-Fragen-Test (1: Config-Fix-resistent? 2: wiederkehrende Tätigkeits-Klasse? 3: Verhalten/Urteil vs. statische Tatsache?), `.legacy` out-of-scope, **CM-Eingangs-Gate** (keine CM für Einmal-Situationen), **Messwerkzeug-Check** bei CM-Definition, **principle⇄CM-Konvention** (jedes Prinzip braucht CM-Schatten), **harte Daten** statt Selbstbericht für nicht-selbstberichtete Verhaltens-CMs.
- **Maßnahmen:** A1 (Selbst-Artefakt-Verifikation) → keine neue, durch bestehendes Prinzip/CM gedeckt, beobachten. A2 (Gate-Enforcement) → verworfen (redundant + scheitert am CM-Gate). **Ad-hoc-Bash bleibt AKTIV** (Deny-Log zeigt ungebrochenes Verhalten – BEWÄHRT auf weicher Evidenz revidiert).
- Archiviert → `archive/session_070_to_077.md`, frische `lessons_learned.md`, Retro-Trigger entfernt.

## Kaizen-Tooling (`retro_report.py`, `jenga_score.py`)

- **Parser-Fix:** Finding-Titel mit `*` (z.B. JSX `/* */`) fielen still durch FINDING_RE → behoben. War die Ursache des „Off-by-one" im Gesamtzähler.
- **Severity-agnostisches CM-Matching** probiert (Option A) → empirisch **über-maskiert** (Wildcard-PROZESS-CM + überladener TOOLING/Tooling-Bucket verschluckten distinkte Muster) → **revertiert**. Falsch-COVERED ist schlimmer als Falsch-NEU.
- **Erstmals Tests** für beide Scripts (`test_retro_report.py`, `test_jenga_score.py`, 12 grün).

## Bucket-Reevaluierung (Taxonomie)

Datenanalyse (79 Findings): `TOOLING/Tooling` war mit 13× überladen – `Tooling` existierte als Kategorie **und** Kontext (redundant). Revision:

- **`Tooling` (Kontext) aufgelöst** → `Bash/Permission` (5) · `Mutation-Testing` (5) · `Hook/Script` (4).
- **`Session-Struktur`** (1 Eintrag) → `Sonstiges`.
- **`Kommunikation`** neu (2 fehl-getaggte `[AGENT][Tooling]`-Einträge + bestehendes „Unterstützt ≠ beweist"-Prinzip).
- **`Sonstiges`** als explizite Staging-Area dokumentiert (dünne Cluster wie Build/Deps, Harness-Tool-Bedienung parken, bis Muster wächst).
- Tag-Namen mit `/` → 2 Regexes (`[\w/-]+`) + Tests.
- **Retaggt:** 22 Archiv-Einträge (Subagent, verifiziert: 0 verbleibende `[Tooling]`-Header, Counts exakt) + 1 Session-Struktur-Eintrag + 4 CMs (`Bash/Permission`, `Kommunikation`, `Sonstiges`, Multi `Bash/Permission, Mutation-Testing`) + 4 Archiv-Header + process.md-Tabelle + Template/lessons-Header.
- **Ergebnis:** 4 Kategorien × 13 Kontext-Tags. Zuvor vergrabene Muster (`Hook/Script`, `Mutation-Testing`) surfacen jetzt als distinkte Kandidaten.

## Probleme / Learnings (Details in lessons_learned)

- Option A theoretisch plausibel, empirisch schädlich – Matching-Heuristiken am echten Datensatz gegenprüfen, nicht nur am Einzelfall.
- „wc nicht erlaubt" behauptet ohne `--list`-Check (Rückfall-Datenpunkt zur Tool-Verhaltens-Verifikation).
- Retag-Migration zunächst nur auf `[Tooling]` skopiert → `[Session-Struktur]`-Eintrag vergessen (S076-Muster: alle Verweis-/Tag-Formen abdecken).

## Offene Punkte

- Uncommittete Änderungen (Doku/Scripts/Tests/Archive) – Commit ausstehend.
- US-904 weiter (nächstes Szenario aus `features/ingredients.feature`) – unverändert.
