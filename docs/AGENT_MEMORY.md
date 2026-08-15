# Agent Memory – Mahl

**Phase:** SKELETON 🔄
**Aktuelle Story:** US-904 (Zutaten)
**Nächster Lauf:** {{NEXT_RUN}}

---

<!--
„Nächste Prioritäten" ist der **Terminplan**, nicht der Inhalt. Jeder Eintrag hat genau vier
Teile und passt in zwei bis drei Zeilen:

  - **<Titel>** — `Fällig: <Anker>` · Quelle: <Zeiger auf den besitzenden Tracker> · Done: <Kriterium>

  1. **Titel** – fettgesetzter Vorspann, wird von `session-agenda.py` als Kurzform gelesen.
  2. **Fällig** – dieselbe Anker-Grammatik wie in `docs/tech-debt.md` (kanonisch dort im Header
     und in `.claude/scripts/td_anchors.py`). `jetzt` = vor dem Beginn der nächsten Story.
  3. **Quelle** – ein Befehl oder Pfad, unter dem der Volltext liegt. **Kein Volltext hier.**
     Bis S116 trug diese Liste die vollständige Begründung jedes Punktes (6.395 Bytes, bei
     jedem Session-Start injiziert), obwohl je Session höchstens einer bearbeitet wird – und
     verletzte damit die Regel „Kurzzusammenfassung ja, Kopie nein" (OBS-S116-2).
  4. **Done** – woran man erkennt, dass der Punkt erledigt ist.

Ein Punkt mit `Fällig: jetzt` beansprucht die „Nächste Aufgabe" der Session (Rang 3, hinter
Retro und vollem OBS-Drain). Gezeigt wird dann der erste `jetzt`-Punkt in Dokumentreihenfolge
im Volltext, alle übrigen nur als Titel + Fälligkeit – die Reihenfolge hier ist also die
Auswahl. TD-Einträge mit
`**Fällig:** jetzt` MÜSSEN hier auftauchen – `check-td-capture.py` prüft das.
-->

## Nächste Prioritäten

- **Domänentypen für Ingredient-Name und -Einheit (TD-S118-2)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S118-2 · Done: Die Längengrenzen stehen im Feldtyp statt im Endpoint (ADR-S119-1), `Ingredient.Create` ist nicht mehr mit ungültigen Werten aufrufbar, `Collect` ersetzt die ausgepackte Fehlersammlung, der „Sollform"-Absatz in §2 ist bereinigt.
  **Zuerst OQ-S119-2 mit dem User klären** – ein geteiltes `Unit` kann keinen `IngredientValidationError` liefern; ohne die Antwort wird `Unit` zweimal gebaut. Prinzip ist in S119 verankert (`coding-guideline-csharp.md` §2), offen ist nur der Code. Danach TD-S118-1 (dieselben Signaturen).

- **Abschnitts-Anker einführen und Verweise prüfbar machen** — `Fällig: jetzt` · Quelle: `python3 .claude/scripts/obs.py get OBS-S112-7` (gekoppelt: OBS-S114-2) · Done: Verweise in lebenden Dokumenten zeigen auf Anker, der Prüfer läuft grün und meldet Brüche beim Editieren.
  Eigene Session (User-Entscheid S115: vollständig migrieren, zu groß für einen Drain-Block).

- **Querschnitts-Testfundament aufsetzen (ADR-S112-5, Schritte 2+3)** — `Fällig: jetzt` · Quelle: `python3 .claude/scripts/decisions.py get ADR-S112-5` · Done: Ein Page-Object-Interface existiert, die Suite läuft parametrisiert gegen die Zutaten-Seite, alle bisherigen Tests sind grün.
  Berührt nur Testcode. Jetzt, weil die Umformung teurer wird, sobald neue Seitenarbeit dazwischenliegt.

- **Backend-Branch-Coverage-Gate reaktivieren (TD-S089-1)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S089-1 · Done: `collect_coverage` ist reaktiviert und `dotnet-test.py` meldet 100% Branch-Coverage grün.

- **Theme-Foundation ziehen (TD-S083-2)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S083-2 · Done: Alle interaktiven Controls messen ≥ 44×44px, der Infra-Test hält das fest.

- **Nominale Brands für die Frontend-Domänentypen (TD-S083-4)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S083-4 · Done: `Client/src` führt in Domänentypen keine nackten `string`-Felder mehr, alle Tests grün.

- **Getypte Ingredient-Id + Wegwerf-ID beseitigen (TD-S118-1)** — `Fällig: jetzt` · Quelle: `docs/tech-debt.md` → TD-S118-1 · Done: `Ingredient` trägt keinen rohen `Guid` mehr, `ToDomain()` erzeugt keine ungelesene Id, alle Tests grün.

- **Zwei fehlende Szenarien mitschreiben: „DB nicht erreichbar" und Fehlerpfad Löschen/Undo** — `Fällig: Phase:MVP` · Quelle: `docs/tech-debt.md` → TD-S108-1 · Done: `features/resilience.feature` übt auch DELETE aus.
  Kein Workshop nötig – beide entstehen bei der Resilience-Arbeit ohnehin.

- **gherkin-workshop US-904, weitere Stufen** — `Fällig: Phase:MVP` · Quelle: `docs/stories/szenario_9_datenpflege.md` · Done: Feature-Datei trägt die MVP-Stufe (Modifier + Bearbeiten), Läufe sind geclustert.
  V1-Stufe danach: Tags für Zutaten (Grundlage für US-907/US-901).

- **Deep-Link-Anforderung klären** — `Fällig: US-602, Phase:V1` · Quelle: `docs/open-questions.md` · Done: Entschieden und als ADR festgehalten, welche Entitäten deep-linkbar sind.
  US-602 ist zugleich die erste Story mit zweiter Seite → Navigations-Szenario nach ADR-S103-1.

- **Visuelle Konsistenz-Guideline erweitern** — `Fällig: TD-S083-2` · Quelle: `docs/guidelines/coding-guideline-ux.md` · Done: Spacing/Hierarchie/Farbe sind dort geregelt.
  Das Theme aus TD-S083-2 ist der Mechanismus, den die Guideline vorschreiben würde.
