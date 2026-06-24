# Session 095 – 2026-06-24

**Phase:** SKELETON
**Fokus:** Kaizen-Retro über Periode S085–094 (Jenga ≤ 0 ausgelöst). Kein Produktionscode.

## Retro-Ergebnisse (S085–094)

### Noise-Review
- **LL-S090-1** (MUI-Dialog `aria-hidden` → Rollen-Queries) als „statische Tatsache" (Frage 3 Grenzfall) **verschoben** statt gelöscht: Komponententest-Teil (`{ hidden: true }`) → `coding-guideline-typescript.md` §6 (bei Z.377 Dialog-Zustandsübergänge); E2E-Teil (`{ includeHidden: true }`) → `e2e-testing.md` (neue Sektion „Rollen-Queries bei offenem Dialog/Overlay", schloss dort eine echte Lücke). LL-Eintrag entfernt.

### Prinzipien (`principles.md`) + CM-Schatten
- **A1 „Vollständige Zerlegung vor Schluss/Empfehlung"** neu (Quantoren/Kostenpfade als eigene Prüfdimension) → **CM-S095-2** (aus LL-S087-2 + LL-S088-2).
- **CM-S095-1** als fehlender Schatten für das S094-Prinzip „Referenzen volatil→stabil" (war ohne CM, unsichtbar fürs Script).

### Modellwahl (OBS-S085-8 + S093-2 erledigt)
- Layer-Implementer-Default `inherit` → **`model: sonnet`** (beide Frontmatter); Opus-Eskalation **pro Schicht**.
- **Schritt-0-Punkt 5** „Modell-Eignung je geplanter Schicht" in `implementing-scenario` (positiv formuliert, ohne volatile OBS-Referenz).

### Countermeasures
- **BEWÄHRT:** CM-S070-2 (Stryker-Full-Run via qa-check) + CM-S084-1 (Playwright besitzt Backend-Lifecycle) – strukturell, ≥3× sauber (S83/S89/S90/S91).
- **AKTIV, Rückfall:** CM-S064-1 (LL-S086-1/S093-1), CM-S086-1 (LL-S094-3).
- **AKTIV, Abdeckungs-Erweiterung (kein Rückfall):** CM-S070-5 (LL-S094-1 – Formular-UX-Baseline war nie enumeriert; in S094 erweitert).
- **CM-S070-3:** DLL-Lock-Teil obsolet (S089 WSL-nativ).
- **CM-S070-1 (KRITISCH):** bleibt AKTIV (konservativ; 3× sauber, aber teils prozedural) statt BEWÄHRT.
- **CM-S070-4:** bleibt AKTIV (nicht BEWÄHRT) – Evidenz unterschied Subagent/Orchestrator-Feedback nicht; Beobachtbarkeit direkt erhöht (s.u.).
- **CM-S078-2 VERWORFEN** (Eskalation 2. Retro): in 2 Perioden kein HOCH-ohne-CM-Fehlausgang → weiche Prüfung reicht. Neue Konvention: VERWORFEN/OBSOLET-CMs bleiben in-file (Abschnitt „Verworfene / Obsolete Maßnahmen"), kein CM-Archiv (`process.md` ergänzt).

### Quelle-Pflicht (Beobachtbarkeit Subagent-Feedback)
- LL/OBS-`Quelle` von optional → **Pflicht** `User | Subagent | Orchestrator` (LL-Header + Template + `process.md`; closing-session-Hinweis entfällt als redundant). `implementing-scenario` Schritt 6.1: Subagent-Feedback **pro Subagent explizit** ausweisen (inkl. „keine").

### Referenz-Richtung (stabil↛volatil)
- Empirie: 5 Bestands-Verstöße in 3 stabilen Dateien. **2 bereinigt** (`review-code`, `review-workflow`: OBS-Tags raus). Die 3 TS-Guideline-LSP-Pilot-Refs bleiben als **dokumentierte Ausnahme** (LSP-Pilot OBS-S085-4 kann mangels Nutzungsdaten nicht abschließen).

### OBS-Backlog
- **Neu:** OBS-S095-1 (Backlog-Prozess – **eigene Session**, Diagnose festgehalten), -2 (review-docs Low-Value-Check), -3 (Referenz-Richtungs-Poka-Yoke-Hook, build-ready), -4 (Lead-Developer-Subagent).
- **OBS-S085-3** wiederaufgegriffen (IN BEOBACHTUNG): D-Analyse zeigt Wrapper-Filtern zerfällt in 3 Klassen → **kein pauschales Deny**, erst Wrapper fixen.
- **Direkt-Entscheid (vor nächstem Szenario, nicht beobachten):** Wrapper-Output-Fixes OBS-S091-1 (`dotnet-test` RED-Assertion-Details) + OBS-S091-3 (vitest Filter-Zählung).
- **Archiviert** (UMGESETZT): OBS-S085-1/-7/-8/-14/-16, OBS-S093-2 → `observations_archive.md`.

### Archivierung
- `lessons_learned.md` (S085–094) → `archive/session_085_to_094.md`; frische Datei aus Template (mit Quelle-Pflicht).

## Probleme / Rework dieser Session
- **OBS-S085-3 fälschlich archiviert:** Status-*Feld* stand auf „UMGESETZT", nur eine Prosa-Notiz sagte „IN BEOBACHTUNG" → Bulk-Skript keyte aufs Feld. Von Hand zurückgeholt + Status-Feld korrigiert (LL-S095-1).
- Mehrere Formulierungen brauchten User-Korrektur (BEWÄHRT-Evidenz CM-S070-4, frischer OBS-Ref im Skill, Rückfall-Fehlklassifikation, Quelle-Optionalität) → LL-S095-2/-3/-4.

## Offen
- **OBS-S095-1 Backlog-Prozess** → eigene Session (Design).
- **Wrapper-Output-Fixes** (OBS-S091-1/-3) vor dem nächsten US-904-Szenario.
- Reference-Richtungs-Hook (OBS-S095-3) – Bau-Zeitpunkt hängt am Backlog-Prozess-Ergebnis.
