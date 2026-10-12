# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-602 (Rezept-Erfassung)
**Nächster Lauf:** {{NEXT_RUN}}

---

<!--
„Nächste Prioritäten" ist der **Terminplan**, nicht der Inhalt. Jeder Eintrag hat genau vier
Teile und passt in zwei bis drei Zeilen:

  - **<Titel>** — `Fällig: <Anker>` · Quelle: <Zeiger auf den besitzenden Tracker> · Done: <Kriterium>

**TD-Punkte stehen kurz** – nur ID und Done-Kriterium, den Rest löst `session-agenda.py`
beim Rendern aus `tech-debt.md` auf (`td_entry.memory_aufloesen`):

  - TD-S089-1 · Done: <Kriterium>

  Titel und Fälligkeit stünden sonst hier ein zweites Mal und könnten driften; beim Beheben
  der Schuld wären zwei Dateien zu räumen (OBS-S118-1). Was hier bleibt, ist genau das, was
  es nur hier gibt: die **Rangfolge** (durch die Position in der Liste) und das
  **Done-Kriterium** (im TD-Format kein Feld). Erzeugt und entfernt wird der Punkt von
  `td.py add|set|remove` – nicht von Hand. Folge: Der Punkt trägt den Titel des TD-Eintrags,
  nicht einen eigens formulierten; die Handlungsrichtung gehört ins Done-Kriterium.
  Ein Platzhalter ohne TD-Eintrag wird beim Rendern sichtbar als Warnung ausgewiesen.

Alle übrigen Punkte (OBS, ADR, Story, offene Fragen) stehen weiterhin voll ausgeschrieben:

  1. **Titel** – fettgesetzter Vorspann, wird von `session-agenda.py` als Kurzform gelesen.
  2. **Fällig** – dieselbe Anker-Grammatik wie in `docs/tech-debt.md` (kanonisch dort im Header
     und in `prozesscode/td_anchors.py`), inklusive der Bedeutung von `jetzt` („sofort" –
     kein Ereignis steht mehr aus). Hier steuert der Anker zusätzlich die Vorlage: Nur ein
     Punkt mit `jetzt` kann den Aufgaben-Slot beanspruchen. Er bedeutet **nicht**, dass der
     Punkt überfällig sei – dass er hinter Retro und OBS-Drain wartet, ist die designte
     Rangfolge.
  3. **Quelle** – ein Befehl oder Pfad, unter dem der Volltext liegt. **Kein Volltext hier.**
     Bis S116 trug diese Liste die vollständige Begründung jedes Punktes (6.395 Bytes, bei
     jedem Session-Start injiziert), obwohl je Session höchstens einer bearbeitet wird – und
     verletzte damit die Regel „Kurzzusammenfassung ja, Kopie nein" (OBS-S116-2).
  4. **Done** – woran man erkennt, dass der Punkt erledigt ist.

Ein Punkt mit `Fällig: jetzt` beansprucht die „Nächste Aufgabe" der Session (hinter
Retro und vollem OBS-Drain). Gezeigt wird dann der erste `jetzt`-Punkt in Dokumentreihenfolge
im Volltext, alle übrigen nur als Titel + Fälligkeit – die Reihenfolge hier ist also die
Auswahl. TD-Einträge mit
`**Fällig:** jetzt` MÜSSEN hier auftauchen – `check-td-capture.py` prüft das.
-->

## Nächste Prioritäten

- TD-S136-1 · Done: Beide Schalter in Directory.Build.props aktiv, Build und Backend-Tests grün, jede verwendete Bibliothek ist im nutzenden Projekt direkt referenziert
- **Visuelle Konsistenz-Guideline erweitern** — `Fällig: Phase:MVP` · Quelle: `docs/guidelines/coding-guideline-ux.md` → Visuelle Baseline · Done: Spacing/Hierarchie/Farbe sind dort als System geregelt und im Theme verankert.
