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
| Reviewer mit Iterations-Vorwissen beauftragt | KRITISCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert ✓; noch offen: Review-Skill-Prompts prüfen ob Iterations-Kontext explizit ausgeschlossen ist | OFFEN | 047 |
| Review-Agent-Output blind übernommen (semantisch falsch) | HOCH | AGENT | Agent-Prompt, Review | Regel in `principles.md` dokumentiert; Prüf-Schritt in `review-code` Skill ergänzt | AKTIV | 047 |
| Guidelines gelesen aber nicht auf konkreten Fall angewandt | HOCH | PROZESS | | `write-code` Skill hat Pflicht-Schritt "Guidelines lesen" – Wirksamkeit beobachten | AKTIV | 047 |

---

## Bewährte Maßnahmen

> Nur auf Regressionen prüfen: Gibt es ein neues Finding in `lessons_learned.md`, das inhaltlich
> zu einem Eintrag hier passt? Falls ja → zurück in "Aktive Maßnahmen" mit Status AKTIV.

_Noch keine bewährten Maßnahmen._
