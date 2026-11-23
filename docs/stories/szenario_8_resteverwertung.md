# Szenario 8 – Die Resteverwertung (Planung)

> Teil von [docs/stories/user-stories.md](../docs/stories/user-stories.md).

## Inhalt

- Szenario-Narrativ (Rezept-Liste, Suche, Plan-Anpassung)
- US-801 (Rezept-Liste) [MVP]
- US-802 (Rezept-Suche & Filter) [V1]
- US-803 (Manuelle Plan-Anpassung) [SKELETON]
- US-804 (Kategorisierte Übersicht) [V2]

---

### Szenario 8: Die Resteverwertung (Planung)
> "Es ist Donnerstagabend, ich mache den Wochenplan. Ich schaue in den Kühlschrank und sehe noch einen halben Kürbis, der weg muss. Ich öffne die Rezeptsuche im Planungs-Modus und tippe 'Kürbis' ein. Die App zeigt mir alle Rezepte mit Kürbis. Ich filtere noch schnell nach 'Vegetarisch', weil ich für Dienstag noch ein fleischloses Gericht brauche. Ah, 'Kürbis-Risotto', das hatten wir lange nicht mehr. Ich ziehe es direkt auf den Dienstag im Plan."

**Abgeleitete User Stories:**

*   **US-801 (Rezept-Liste) [MVP]:** Als *Feierabend-Planer* möchte ich eine Liste aller meiner Rezepte sehen, um den Überblick zu behalten.
    *   **Akzeptanzkriterien:**
        *   Liste aller Rezepte.
        *   Klick auf ein Rezept öffnet die Detailansicht (bereichsweise bearbeitbar, siehe US-614).

*   **US-802 (Rezept-Suche & Filter) [V1]:** Als *Feierabend-Planer* möchte ich die Rezept-Liste nach Titel, Zutaten oder Tags filtern, um bestimmte Gerichte zu finden.
    *   **Akzeptanzkriterien:**
        *   Suchfeld (Titel). Die Suche findet Wortteile an beliebiger Stelle des Titels, z.B. findet „Spinat" auch „Nudeln mit Spinat-Mandel-Joghurt" – alphabetisch sortiert findet man ein Rezept sonst nur über sein erstes Wort.
        *   Zutaten-Filter.
        *   Tag-Filter (Mehrfachauswahl möglich).

*   **US-803 (Manuelle Plan-Anpassung) [SKELETON]:** Als *Feierabend-Planer* möchte ich Rezepte vormerken, um daraus meine Einkaufsliste zu erstellen.
    *   **Akzeptanzkriterien (SKELETON-Version - vereinfacht):**
        *   Umschalter „Vormerken“/„Vorgemerkt“ in jeder Zeile der Rezept-Liste und in der Rezept-Detailansicht
        *   Das Rezept wird zur *Vormerkung* (keine Tages-Zuordnung in SKELETON)
        *   Die Seite „Vorgemerkt“ zeigt eine flache Liste der vorgemerkten Rezepte mit "Entfernen"-Button
    *   **Akzeptanzkriterien (MVP-Version - mit Tagen):**
        *   Tage in derselben Ansicht: Kalender-/Wochendarstellung der *Vormerkungen*
        *   Drag & Drop von Vormerkungen auf Tage
        *   **Mengen-Anpassung:** Beim Zuordnen kann direkt die *Planungs-Portion* angepasst werden (Default: *Basis-Portion* des Rezepts)

*   **US-804 (Kategorisierte Übersicht) [V2]:** Als *Feierabend-Planer* möchte ich meine Rezepte in einer gruppierten Ansicht sehen (z.B. Hauptgerichte, Salate, Snacks), die meiner Nutzungshäufigkeit entspricht, um ohne Suche schnell Inspiration zu finden.
    *   **Akzeptanzkriterien:**
        *   Anzeige der Rezepte in definierten Sektionen (Reihenfolge konfigurierbar oder fest definiert: Hauptgericht Veggie/Fleisch, Salat, Suppe, etc.).
        *   Sektionen basieren auf Tag-Kombinationen.
        *   Diese Ansicht dient als Standard-Dashboard für die Rezept-Auswahl.
