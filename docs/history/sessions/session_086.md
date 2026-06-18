# Session 086 – 2026-06-17

**Phase:** SKELETON
**Fokus:** OBS-Evaluierung (S085-Backlog) + Sofort-Block + Bookkeeping

## Implementiert

### OBS-Evaluierung (gesamter S085-Backlog)
Alle offenen OBS aus dem S085-Backlog gemeinsam mit dem User evaluiert (außer OBS-S085-2 = Spike, OBS-S085-10 = deferred). Entscheidungen in `docs/kaizen/observations.md` festgehalten. Drei Punkte brauchten Faktenklärung per Recherche:
- **Claude-Code-Hooks:** PreToolUse kann via `updatedInput` den Befehl umschreiben (relevant für OBS-1).
- **Agent-Modell-Override:** `Agent`-`model`-Param übersteuert Frontmatter → Frontmatter = Default, kein Deckel (OBS-8).
- **LSP:** Claude Code v2.1.172 unterstützt LSP; C# hat offene Showstopper im LSP-Client (claude-plugins-official#1359, claude-code#38683), TS ist Pilot-Kandidat (OBS-4, Impact GERING→MITTEL/HOCH revidiert).

### Sofort-Block (umgesetzt + getestet)
- **OBS-15+5:** Prinzip „Single Source of Truth: Information am passendsten Ort, sonst referenzieren" in `principles.md` (Abschnitt „Doku & Referenzen") + Spiegel-CM in `countermeasures.md` (S086, AKTIV).
- **OBS-13:** `kaizen` SKILL Schritt 5 – vier Facetten pro Finding (Problem/Warum-jetzt/Vorschlag/Alternativen, auch als Tabellen-Spalten in A); leere Abschnitte nicht still weglassen.
- **OBS-6:** LL-Format kanonisch im `lessons_learned.md`-Header (+ gefülltes Beispiel); `process.md` §Eintrag-Format, `closing-session` Schritt 5 und das Template referenzieren nur noch den Header (Single Source gegen Drift). Präzisierte Ursache: die LL-Datei wird zum Edit ohnehin gelesen – die echte Verschwendung war ein *separater* `process.md`-Read.
- **OBS-9:** Soft-Ziel 150 / harter Cap 300 Zeichen für Index-Kurzfassungen. Geteilte Logik `_index_length.py`; `check-index-length.py` als CLI-Report **und** PreToolUse-Hook (in `settings.json` registriert, grandfathered: nur neueste/geänderte Zeilen, History read-only). S76–S85 gekürzt. Drift per Plot als Verbosity-Ratchet belegt (nicht Scope-Wachstum). Hook **live** verifiziert (deny/allow/grandfather).

### Bookkeeping
- 6 aufgelöste OBS (5/6/9/11/13/15) nach `observations_archive.md` verschoben.
- `observations.md`: verbliebene OBS (1/3/4/7/8/14/16) mit Entscheidung + Status aktualisiert; OBS-2/10 als ausgenommen markiert; OBS-12 IN BEOBACHTUNG.
- `AGENT_MEMORY.md`: „Nächste Prioritäten" um die offenen OBS-Umsetzungen ergänzt; „Letzte Aktualisierung" auf S086.

## Probleme / Findings
- **LL-S086-1 (MITTEL):** Bei OBS-1 Kandidat A (Hook-Umschreiben) als „gefährlich" bewertet + B empfohlen, ohne die Hook-Fähigkeit (`updatedInput`) zu verifizieren – Gefahr war überzogen. Rückfall auf Verifikations-CM (S064).
- **LL-S086-2 (MITTEL):** OBS-S085-4 war falsch erfasst (Missverständnis „languageServer buggy" vs. „nutzen keinen") – musste reframed werden.
- **Hook-Reload:** `settings.json`-Hook-Änderungen werden erst nach Claude-Code-Neustart aktiv (live bestätigt – der erste Live-Hook-Test schlug vor dem Neustart fehl). Bewusst nicht dokumentiert (Scripte ändern wir oft, Hook-Registrierung selten).

## Neue Beobachtungen (User-Feedback, → Retro)
OBS-S086-1 (Kandidaten gemeinsam statt eigenmächtig), -2 (Verständnis vor Erfassung, ggf. grill-me), -3 (Findings kategorie-/blockweise), -4 (`--allow-once`-Notwendigkeits-/Gefahr-Hinweise), -5 (Session-Datei-Scope).

## Offene Punkte
- OBS-Umsetzungen 1/3/4/7/8/14/16 (je eigener Block, s. AGENT_MEMORY).
- Feedback zur globalen `CLAUDE.md`-Nummerierungsregel (natürliche IDs wie OBS-/ADR-IDs wiederverwenden statt A1/B2) – dem User zur Entscheidung vorgelegt.
