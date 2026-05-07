# Szenario 3 – Der schnelle Einkauf (Mittagspause)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (eiliger Einkauf, Non-Food-Items, Offline, Ersatz)
- US-301 (Intelligente Artikelerfassung) [MVP]
- US-302 (Laufweg-Sortierung) [V1]
- US-303 (Artikel abhaken) [SKELETON]
- US-304 (Visuelle Darstellung & Varianten) [OBSOLET]
- US-305 (Ersatz-Vorschläge) [PARKING]
- US-306 (Offline-Verfügbarkeit) [MVP]
- US-307 (Nicht-Zutaten) [MVP]

---

### Szenario 3: Der schnelle Einkauf (Mittagspause)
> "Kurze Mittagspause, da möchte ich den Wocheneinkauf erledigen. Ach ja, Toilettenpapier ist alle, also noch schnell auf die Liste und los in den Laden. Erstmal das Gemüse: Ein Bund Zwiebeln eingepackt, 300 g Tomaten brauchen wir auch noch. Mhm, es gibt nur 250g-Packungen - wofür brauchten wir das noch gleich? Dann eben zwei Packungen. Okay, weiter zu den Milchprodukten. Mist, es gibt keinen Schmelzkäse - wofür war der nochmal gedacht? Oder kann ich den mit was anderem ersetzen? Okay, nehmen wir halt das. So weiter zu den Tiefkühlprodukten, dann zur Kasse und schnell wieder nach Hause."

**Abgeleitete User Stories:**

*   **US-301 (Intelligente Artikelerfassung) [MVP]:** Als *eiliger Einkäufer* möchte ich Artikel über ein smartes Suchfeld hinzufügen, das mir bereits beim Tippen passende Vorschläge macht, um Dopplungen zu vermeiden und schnell zu sein.
    *   **Akzeptanzkriterien:**
        *   **Eingabe & Vorschläge:** Während der Texteingabe werden passende Vorschläge aus den Stammdaten und der aktuellen Liste als Kacheln angezeigt. Die Kachelfarbe spiegelt den Listenstatus wider, konsistent zur Listenansicht selbst: offene Artikel in der Listen-Farbe, bereits abgehakte und neue Artikel in der Abgehakt-Farbe.
        *   **Modifizierer-Trennschärfe:** Gleiche Zutat mit unterschiedlichen Modifizierern (z.B. Dose vs. Frisch) sind getrennte Einträge – werden nicht zusammengeführt.
        *   **Antippen fügt hinzu:** Antippen einer Kachel fügt den Artikel zur Einkaufsliste hinzu, setzt das Eingabefeld zurück und setzt den Fokus darauf, damit direkt der nächste Artikel eingegeben werden kann.
        *   **Mengen-Parsing:** Enthält die Eingabe eine Menge und Einheit (z.B. "300g Tomaten"), wird die Menge beim Hinzufügen automatisch übernommen.
        *   **Neuen Artikel anlegen:** Die letzte Kachel in der Vorschlagsliste ist immer "Neu anlegen: [Eingabe]" – für Artikel die noch nicht in den Stammdaten existieren.
        *   **Menge anpassen (langer Druck):** Langer Druck auf einen Listeneintrag öffnet eine Detail-Ansicht mit editierbarer Menge und der Liste der zugehörigen Rezepte mit Teilmengen (Kontext für Substitutionsentscheidungen).

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
    *   **Implementierungshinweis:** Teilt die Listenkomponente mit US-201. Beim Implementieren: Tests für den "im Laden"-Kontext schreiben.

*   **US-304 (Visuelle Darstellung & Varianten) [OBSOLET]:** Aufgelöst – drei Bedenken wurden getrennt behandelt:
    *   **Kachel-Design (Layout):** Designprinzip ab SKELETON – in `docs/history/decisions.md` (Abschnitt "Einkaufsliste UX-Referenz: Bring!") dokumentiert.
    *   **Modifizierer-Trennschärfe:** Als AK in US-301 aufgenommen.
    *   **Langklick-Kontext:** Als AK in US-301 aufgenommen.

*   **US-305 (Ersatz-Vorschläge) [PARKING]:** Als *eiliger Einkäufer* möchte ich bei fehlenden Artikeln (kein Schmelzkäse) sehen, welche Alternativen möglich wären, damit ich das Rezept retten kann.
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
