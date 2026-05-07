# Session 067 – 2026-05-07

**Phase:** SKELETON (Requirements-Sanitization)

## Kontext

Fortsetzung der Requirements-Sanitization (Musk-Algorithmus Schritte 1+2) aus der Vorherigen Session. Vollständige Einarbeitung aller Tier-Änderungen in die Story-Dateien, Reformulierung US-301, npm-Updates.

## Umgesetzt

### User Stories – Tier-Änderungen

**USER_STORIES.md:** Vollständige Phasendefinitionen (SKELETON/MVP/V1/V2/PARKING) ergänzt.

**Szenario 1 – Planung:**
- US-102, US-103, US-107: V1 (war teils MVP)
- US-105: AK-Split in MVP-Version (Harte Regeln + Zufallsauswahl) und V1-Erweiterung (Sortier- & Tagesregeln)
- US-106: [OBSOLET]-Header-Eintrag wieder ergänzt (war nach vorheriger Session gelöscht – Konsistenz mit US-304)

**Szenario 3 – Einkauf:**
- US-301: vollständig neu formuliert (6 AK: Eingabe & Vorschläge mit Farbkonsistenz, Modifizierer-Trennschärfe, Antippen fügt hinzu + Fokus-Reset, Mengen-Parsing, Neu anlegen, Menge anpassen via Langdruck)
- US-304: [OBSOLET] mit Auflösungsnotiz (Layout → decisions.md, Modifizierer-Trennschärfe → US-301, Langklick → US-301)
- US-305: [PARKING]

**Szenario 5 – Kochen:**
- US-505/506/508/509: MVP → V1 (Kochmodus-Features; MVP = Wochenplan+Einkauf, nicht Kochmodus)
- US-513/515/517: V2 → PARKING (Bewertung und Zeit-Tracking)

**Szenario 6 – Rezept-Erfassung:**
- US-606/608: V2 → PARKING
- US-616: MVP → V1, AK-Split aufgelöst (flache Liste)

**Szenario 0, 2, 4, 7, 9:** Tier-Korrekturen aus Vorherigen Phasen bereits eingearbeitet.

### decisions.md

- **Einkaufsliste UX-Referenz: Bring!** ergänzt (Kachel-Design als Designprinzip ab SKELETON, Begründung für US-304-Auflösung)

### Tooling / Hook

- `check-bash-permission.py`: npm-Hint für WSL-Direktaufruf ergänzt (`_SMART_DENY_HINTS`)
- `check-bash-permission.py`: `npm outdated` via cmd.exe in ALLOW_PATTERNS aufgenommen
- `test-bash-permission.py`: Tests für `npm outdated` (allow via cmd.exe, deny WSL-direkt) ergänzt
- Alle Hook-Tests grün

### npm-Updates

- Patch/Minor: react, react-dom, @mui/material (patch), @tanstack/react-query, vite, vitest, msw, react-router, happy-dom, typescript u.a.
- Major: MUI v7 → v9 (kein v8; Versionsalignment mit MUI X; MD3-Support bleibt erhalten)
- Major: ESLint v9 → v10, eslint-plugin-functional v7 → v9, eslint-plugin-react-hooks v5 → v7, globals v15 → v17
- postcss-Vulnerability (moderate) via `npm audit fix` behoben
- Alle Frontend-Tests nach Updates grün

## Diskussionen / Entscheidungen

- **US-304 OBSOLET vs. Löschen:** OBSOLET gewählt für Traceability, konsistent mit US-106-Pattern
- **US-106 Header-Eintrag:** Wieder eingefügt (war nach vorheriger Session entfernt) – Konsistenz: OBSOLET-Einträge bleiben in der Inhaltsliste sichtbar
- **Modifizierer-Trennschärfe (US-304):** Entscheidung für Option B (AK in US-301), nicht eigenständige Story oder pure Datenmodell-Entscheidung
- **DokuWiki-Migrationsstrategie:** Kein decisions.md-Eintrag – Migration ist ein einmaliger LLM-gestützter Import bei MVP-Start (DB-Reset), kein App-Scope
- **MUI v7 → v9:** Upgrade jetzt (SKELETON mit minimalem Code), nicht später; v9 ist "Foundations"-Release ohne Design-Redesign
- **UX Guideline 8 (Fokus-Management):** Abgelehnt – zu spezifisch für eine eigenständige Guideline auf diesem Abstraktionsniveau

## Offene Punkte

Keine.
