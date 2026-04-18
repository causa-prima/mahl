# Countermeasures

<!--
wann-lesen: In jeder Retro – AKTIV/OFFEN auf Wirksamkeit prüfen, BEWÄHRT auf Regressionen scannen.
wann-schreiben: Nach KRITISCH- oder HOCH-Finding sofort; nach Retro wenn Muster in MITTEL/GERING erkannt.

Status-Lifecycle: OFFEN → [IN UMSETZUNG] → AKTIV → BEWÄHRT
  OFFEN: Problem bekannt, Maßnahme noch nicht definiert oder noch nicht implementiert.
  IN UMSETZUNG: (optional) Maßnahme definiert, Umsetzung dauert mehrere Sessions.
  AKTIV: Maßnahme live – Wirksamkeit wird beobachtet.
  BEWÄHRT: In einer Retro explizit erklärt (Kriterium: docs/kaizen/PROCESS.md).
           Bleibt in dieser Datei (unterer Abschnitt) – für Regressions-Erkennung.
           Regression = neues Finding das inhaltlich passt → zurück auf AKTIV.

Kontext-Spalte:
  Welche Kontext-Tags (aus PROCESS.md) diese Maßnahme abdeckt.
  Leer = Wildcard (Maßnahme gilt für alle Kontexte dieser Schwere+Kategorie).
  Mehrere Werte kommasepariert: z.B. "Agent-Prompt, Review"
  Wann leer lassen: Maßnahme ist generisch genug, dass der konkrete Kontext keine Rolle spielt
    (z.B. "Guidelines nicht angewandt" trifft auf TDD, C#-Code, TS-Code gleichermaßen zu).
  Wann befüllen: Problem ist klar auf bestimmte Kontexte beschränkt und würde bei anderen
    Kontexten zu False-Positives im Pattern-Kandidaten-Report führen.

Reaktionsregeln je Schwere: docs/kaizen/PROCESS.md
-->

## Aktive Maßnahmen

| Problem | Schwere | Kategorie | Kontext | Maßnahme | Status | Seit Session |
|---------|---------|-----------|---------|----------|--------|--------------|
| Ad-hoc-Bash-Befehle statt erlaubter Befehle aus DEV_WORKFLOW.md (S53: `npx playwright test`) | MITTEL | TOOLING | Tooling | `check-bash-permission.py` umgebaut: auto-deny, `# --allow-once`-Marker, Log in `.claude/tmp/denied-commands.log`, Smart-Hints, neue Allow-Patterns (npx, dotnet run). DEV_WORKFLOW.md aktualisiert. | AKTIV | 056 |
| Review-Agent-Output blind übernommen (semantisch falsch) | HOCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert; Prüf-Schritt in `review-code` Skill ergänzt | AKTIV | 047 |
| Guidelines gelesen aber nicht auf konkreten Fall angewandt (Rückfall S53: YAGNI) | HOCH | PROZESS | | `write-code` Skill: Pflicht-Schritt "Guidelines lesen" + explizite Per-Member-YAGNI-Frage: „Welcher aktuell rote Test fordert genau das?" | AKTIV | 047 |
| Behauptungen über externes Tool-Verhalten als gesichertes Wissen präsentiert (S061, S063) | HOCH | AGENT | Tooling | Regel in `principles.md` dokumentiert ✓. Selbst-Check vor jeder Tool-Verhaltensbehauptung: „Basiert das auf einem Tool-Call dieser Session?" Falls nein: explizit als unverified kennzeichnen und Verifizierung anbieten. | AKTIV | 064 |
| Infrastruktur-Fehler oder Tooling-Trivia als lessons_learned dokumentiert (S061 ×2, S063, S053, S052) | MITTEL | QUALITÄT | Tooling | Filter-Test in `docs/kaizen/PROCESS.md` und im lessons_learned-Header ergänzt. Preprocessing-Schritt im `kaizen`-Skill (vor retro_report.py): Noise-Review von lessons_learned + Archiv mit User-Freigabe. | AKTIV | 064 |
| Neue Guideline wird nicht in bestehende Skills und Feature-Files integriert (S063: UX-Guideline) | MITTEL | PROZESS | Doku | Beim Einführen einer neuen Guideline: explizit prüfen welche Skills sie referenzieren sollen + ob bestehende Feature-Files einen Retrofit-Workshop brauchen. Hinweis als Pflicht-Schritt in `closing-session` Skill ergänzt. | AKTIV | 064 |

---

## Bewährte Maßnahmen

> Nur auf Regressionen prüfen: Gibt es ein neues Finding in `lessons_learned.md`, das inhaltlich
> zu einem Eintrag hier passt? Falls ja → zurück in "Aktive Maßnahmen" mit Status AKTIV.

| Problem | Schwere | Kategorie | Kontext | Maßnahme | Status | Seit Session |
|---------|---------|-----------|---------|----------|--------|--------------|
| Reviewer mit Iterations-Vorwissen beauftragt | KRITISCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert ✓; Pflicht-Hinweis in `review-code` SKILL.md Schritt 3 ergänzt: keine früheren Findings, keine false-positive-Labels übergeben | BEWÄHRT | 047 |
