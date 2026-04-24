# Szenario 3 – Der schnelle Einkauf (Mittagspause)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (eiliger Einkauf, Non-Food-Items, Offline, Ersatz)
- US-301 (Intelligente Artikelerfassung) [MVP]
- US-302 (Laufweg-Sortierung) [V1]
- US-303 (Artikel abhaken) [SKELETON]
- US-304 (Visuelle Darstellung & Varianten) [V1]
- US-305 (Ersatz-Vorschläge) [V2]
- US-306 (Offline-Verfügbarkeit) [MVP]
- US-307 (Nicht-Zutaten) [MVP]

---

### Szenario 3: Der schnelle Einkauf (Mittagspause)
> "Kurze Mittagspause, da möchte ich den Wocheneinkauf erledigen. Ach ja, Toilettenpapier ist alle, also noch schnell auf die Liste und los in den Laden. Erstmal das Gemüse: Ein Bund Zwiebeln eingepackt, 300 g Tomaten brauchen wir auch noch. Mhm, es gibt nur 250g-Packungen - wofür brauchten wir das noch gleich? Dann eben zwei Packungen. Okay, weiter zu den Milchprodukten. Mist, es gibt keinen Schmelzkäse - wofür war der nochmal gedacht? Oder kann ich den mit was anderem ersetzen? Okay, nehmen wir halt das. So weiter zu den Tiefkühlprodukten, dann zur Kasse und schnell wieder nach Hause."

**Abgeleitete User Stories:**

*   **US-301 (Intelligente Artikelerfassung) [MVP]:** Als *eiliger Einkäufer* möchte ich Artikel über ein smartes Suchfeld hinzufügen, das mir bereits beim Tippen passende Vorschläge macht, um Dopplungen zu vermeiden und schnell zu sein.
    *   **Akzeptanzkriterien:**
        *   **Live-Suche:** Suche in Stammdaten und aktueller Liste während des Tippens.
        *   **Status-Anzeige:** Bereits auf der Liste befindliche Artikel werden optisch hervorgehoben.
        *   **Interaktion:** Tippen fügt hinzu (oder erhöht Menge), langes Drücken öffnet Details.
        *   **Erstellung:** Letzter Eintrag der Vorschlagsliste ist immer ein Eintrag zum Neu erstellen der aktuellen Eingabe als Titel (mit Parsing von Menge/Einheit).

*   **US-302 (Laufweg-Sortierung) [V1]:** Als *eiliger Einkäufer* möchte ich, dass die Liste nach Tags sortiert ist, die meinem Weg durch den Laden entsprechen (Gemüse -> Milch -> TK), damit ich nicht zurücklaufen muss.
    *   **Akzeptanzkriterien:**
        *   Items werden nach ihren *Tags* gruppiert.
        *   Reihenfolge der Tags ist global konfigurierbar (siehe US-907).
        *   Items ohne passenden Tag landen im Bereich "Nicht zugeordnet" am Ende der Liste.

*   **US-303 (Artikel abhaken) [SKELETON]:** Als *eiliger Einkäufer* möchte ich Artikel, die ich in den Wagen gelegt habe, als "gekauft" markieren, damit die Liste übersichtlich bleibt.
    *   **Akzeptanzkriterien:**
        *   Klick auf Artikel markiert ihn als "gekauft".
        *   Gekaufte Artikel werden ans Ende der Liste in einen eigenen Bereich "Zuletzt gekauft" verschoben.
        *   Gekaufte Artikel lassen sich einfach von noch nicht gekauften Artikeln unterscheiden

*   **US-304 (Visuelle Darstellung & Varianten) [V1]:** Als *eiliger Einkäufer* möchte ich Artikel als Kacheln mit Icon und Text sehen, wobei unterschiedliche Zustände (z.B. "Tomaten" vs. "Tomaten, stückig") als separate Einträge behandelt werden.
    *   **Akzeptanzkriterien:**
        *   **Layout:** Kachel-Design mit Icon (Strichzeichnung) und zweizeiligem Text (Name (inkl. Modifizierer) + Menge).
        *   **Trennschärfe:** Gleiche Zutat mit unterschiedlichen Modifizierern (z.B. Dose vs. Frisch) sind getrennte Einträge.
        *   **Kontext:** Langer Klick auf Item zeigt Liste der zugehörigen Rezepte mit Teilmengen.

*   **US-305 (Ersatz-Vorschläge) [V2]:** Als *eiliger Einkäufer* möchte ich bei fehlenden Artikeln (kein Schmelzkäse) sehen, welche Alternativen möglich wären, damit ich das Rezept retten kann.
    *   **Akzeptanzkriterien:**
        *   Anzeige von Zutaten mit expliziten Alternativen oder ähnlichen Tags.

*   **US-306 (Offline-Verfügbarkeit) [MVP]:** Als *eiliger Einkäufer* möchte ich meine Einkaufsliste auch im Supermarkt ohne Internetempfang vollständig nutzen und abhaken können, damit ich nicht blockiert bin.
    *   **Akzeptanzkriterien:**
        *   App lädt auch im Flugmodus.
        *   Alle Lese- und Schreiboperationen funktionieren offline (Sync bei Wiederverbindung).

*   **US-307 (Nicht-Zutaten) [MVP]:** Als *eiliger Einkäufer* möchte ich schnell freie Artikel (z.B. Toilettenpapier) auf die Einkaufsliste setzen, ohne ein Rezept oder eine Zutat anlegen zu müssen.
    *   **Akzeptanzkriterien:**
        *   Freitext-Eingabe möglich.
        *   Keine Validierung gegen Zutaten-DB erforderlich.
        *   Eingegebene Freitexte werden als *Non-Food-Items* gespeichert und bei zukünftigen Eingaben als Autocomplete-Vorschlag angeboten.
