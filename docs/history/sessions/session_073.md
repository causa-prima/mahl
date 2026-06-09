# Session 073 – 2026-06-05

## Thema
Stryker-Tooling: Frontend-Backend-Angleichung, StrykerOutput-Reorganisation, implementing-scenario Skill-Verbesserungen

## Kontext
Ausgangspunkt: Frontend-Stryker-Script hatte keine Summary-Auswertung und keinen strukturierten Output. qa-check.py hatte alle Varianten noch nicht vollständig getestet. Der implementing-scenario Skill beschrieb SendMessage-Muster unvollständig.

## Umgesetzte Änderungen

### Stryker-Tooling

**StrykerOutput-Reorganisation:**
- `StrykerOutput/` aufgeteilt in `StrykerOutput/Backend/` und `StrykerOutput/Frontend/`
- `StrykerOutput/` in `.gitignore` ergänzt (war nur per Unterordner-gitignore abgesichert)
- `dotnet-stryker.py`: verschiebt nach dem Lauf den neu angelegten Timestamp-Ordner nach `StrykerOutput/Backend/` (Stryker.NET unterstützt kein `"output"`-Config-Key – dieser Ansatz war der Workaround)
- `stryker-frontend.py`: kopiert nach dem Lauf alle Dateien aus `Client/reports/mutation/` nach `StrykerOutput/Frontend/<timestamp>/reports/`, benennt `mutation.json` → `mutation-report.json` und `mutation.html` → `mutation-report.html` um

**Frontend-Stryker auf Backend-Niveau gebracht:**
- JSON-Reporter in `stryker.config.json` war bereits konfiguriert aber ungetestet → verifiziert funktionierend
- `stryker-frontend.py` ruft jetzt nach dem Lauf `stryker-summary.py` mit explizitem Report-Pfad auf
- `--detail` wird an `stryker-summary.py` durchgereicht (nicht mehr: mehr Raw-Ausgabe-Zeilen)
- `stryker-summary.py`: `find_latest_report()` sucht jetzt in `StrykerOutput/Backend/` statt `StrykerOutput/`; `short_path()` kennt `src/` als Anchor für Frontend-Pfade

**qa-check.py:**
- `_find_report()` angepasst: sucht in `StrykerOutput/Backend/*/` bzw. `StrykerOutput/Frontend/*/`
- Alle 4 Varianten (`--layer backend/frontend`, mit/ohne `--skip-stryker`) getestet
- Bug behoben: Frontend-Stryker-JSON enthält Mutanten in nicht-deterministischer Reihenfolge → Hash war instabil zwischen Läufen. Fix: JSON vor dem Hashen normalisieren (`sort_keys=True` + Mutanten nach `id` sortieren)
- **Check 5 neu:** Prüft ob neue Test-Methoden (`[Fact]`/`[Theory]` bzw. `it(`) `// Given`, `// When`, `// Then`-Kommentare enthalten

**`check-atdd-gate.py` (neu):**
- Prüft ob ein Gherkin-Szenario-Tag in `features/` existiert
- Gibt Background + vollständigen Szenario-Block aus wenn gefunden
- Exit 1 mit Fehlermeldung wenn nicht gefunden

### implementing-scenario Skill

- **SendMessage-Muster präzisiert:** Wann SendMessage (Subagent wartet auf Test-Review), wann neuer Spawn (Subagent abgeschlossen)
- **TDD-Korrekturloop:** "fixen lassen" → explizit via SendMessage; Subagent pausiert nach Korrektur erneut für Re-Review
- **Schritt 4 + Survivor-Check:** Findings gesammelt via SendMessage an bestehenden Subagenten übergeben (nicht neuer Spawn) – Subagent hat Kontext und kann Gegenargumente bringen
- **Triviale-Findings-Ausnahme entfernt:** war Kompromiss aus der Zeit vor SendMessage-Wiederaufnahme, nicht mehr nötig
- **ATDD-Gate:** jetzt als Script-Aufruf statt manueller Suche
- **Check 5 in Schritt 4** dokumentiert

### DEV_WORKFLOW.md
- `stryker-frontend.py --detail`-Kommentar korrigiert (war: "mehr Output-Zeilen", ist: "alle nicht-getöteten Mutanten")
- Hinweis auf `StrykerOutput/Frontend/<timestamp>/` und `StrykerOutput/Backend/<timestamp>/` ergänzt

## Probleme / Erkenntnisse

**Stryker.NET `"output"`-Config-Key:** Beim Versuch `"output": "StrykerOutput/Backend"` in `stryker-config.json` einzutragen schlug der Lauf fehl – der Key ist nicht in der allowed-keys-Liste. Lösung: Post-run-Move in `dotnet-stryker.py`.

**StrykerJS nicht-deterministische Mutanten-Reihenfolge:** Erst beim zweiten Verifikationslauf aufgefallen (Hashes wichen ab). Diagnose über temporäres `compare-reports.py`-Script: Mutanten 8 und 9 in `IngredientsPage.tsx` tauschten zwischen Läufen Array-Position. Fix: JSON normalisieren vor SHA-256.

## Offene Punkte
- decisions.md IDs (DEC-XXX): Voraussetzung für Check-atdd-gate DEC-XXX-Cross-Reference-Check (Schritt 4 Kandidat)
- US-904 Szenario 2 Neuimplementierung steht noch aus
