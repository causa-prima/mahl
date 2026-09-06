# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)
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

- **Querschnitts-Testfundament aufsetzen (ADR-S112-5: Page-Object-Interface definieren, bestehende Tests überführen)** — `Fällig: jetzt` · Quelle: `python3 -m prozesscode.decisions get ADR-S112-5` · Done: Ein Page-Object-Interface existiert, die Suite läuft parametrisiert gegen die Zutaten-Seite, alle bisherigen Tests sind grün.
  Berührt nur Testcode. Jetzt, weil die Umformung teurer wird, sobald neue Seitenarbeit dazwischenliegt.

- TD-S089-1 · Done: `collect_coverage` ist reaktiviert und `dotnet-test.py` meldet 100% Branch-Coverage grün.

- TD-S083-2 · Done: Alle interaktiven Controls messen ≥ 44×44px, der Infra-Test hält das fest.

- TD-S083-4 · Done: `Client/src` führt in Domänentypen keine nackten `string`-Felder mehr, alle Tests grün.

- TD-S108-1 · Done: `features/resilience.feature` übt auch DELETE aus.
  Kein Workshop nötig – beide entstehen bei der Resilience-Arbeit ohnehin.

- **gherkin-workshop US-904, weitere Stufen** — `Fällig: Phase:MVP` · Quelle: `docs/stories/szenario_9_datenpflege.md` · Done: Feature-Datei trägt die MVP-Stufe (Modifier + Bearbeiten), Läufe sind geclustert.
  V1-Stufe danach: Tags für Zutaten (Grundlage für US-907/US-901).

- **Deep-Link-Anforderung klären** — `Fällig: US-602, Phase:V1` · Quelle: `docs/open-questions.md` · Done: Entschieden und als ADR festgehalten, welche Entitäten deep-linkbar sind.
  US-602 ist zugleich die erste Story mit zweiter Seite → Navigations-Szenario nach ADR-S103-1.

- **Visuelle Konsistenz-Guideline erweitern** — `Fällig: TD-S083-2` · Quelle: `docs/guidelines/coding-guideline-ux.md` · Done: Spacing/Hierarchie/Farbe sind dort geregelt.
  Das Theme aus TD-S083-2 ist der Mechanismus, den die Guideline vorschreiben würde.
