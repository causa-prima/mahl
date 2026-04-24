# Szenario 8 – Die Resteverwertung (Planung)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

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
        *   Klick auf ein Rezept öffnet die Detailansicht (Ansichts-Modus).

*   **US-802 (Rezept-Suche & Filter) [V1]:** Als *Feierabend-Planer* möchte ich die Rezept-Liste nach Titel, Zutaten oder Tags filtern, um bestimmte Gerichte zu finden.
    *   **Akzeptanzkriterien:**
        *   Suchfeld (Titel).
        *   Zutaten-Filter.
        *   Tag-Filter (Mehrfachauswahl möglich).

*   **US-803 (Manuelle Plan-Anpassung) [SKELETON]:** Als *Feierabend-Planer* möchte ich Rezepte zum Wochen-Pool hinzufügen, um meine Einkaufsliste zu erstellen.
    *   **Akzeptanzkriterien (SKELETON-Version - vereinfacht):**
        *   Button "Zum Pool hinzufügen" bei jedem Rezept in der Rezept-Detailansicht
        *   Rezept wird dem *Wochen-Pool* hinzugefügt (keine Datums-Zuordnung in SKELETON)
        *   Pool-Ansicht zeigt flache Liste der hinzugefügten Rezepte mit "Entfernen"-Button
    *   **Akzeptanzkriterien (MVP-Version - mit Kalender):**
        *   Kalender-Darstellung mit Wochenansicht
        *   Drag & Drop von Rezepten auf Wochentage
        *   **Mengen-Anpassung:** Beim Zuordnen kann direkt die *Planungs-Portion* angepasst werden (Default: *Basis-Portion* des Rezepts)

*   **US-804 (Kategorisierte Übersicht) [V2]:** Als *Feierabend-Planer* möchte ich meine Rezepte in einer gruppierten Ansicht sehen (z.B. Hauptgerichte, Salate, Snacks), die meiner Nutzungshäufigkeit entspricht, um ohne Suche schnell Inspiration zu finden.
    *   **Akzeptanzkriterien:**
        *   Anzeige der Rezepte in definierten Sektionen (Reihenfolge konfigurierbar oder fest definiert: Hauptgericht Veggie/Fleisch, Salat, Suppe, etc.).
        *   Sektionen basieren auf Tag-Kombinationen.
        *   Diese Ansicht dient als Standard-Dashboard für die Rezept-Auswahl.
