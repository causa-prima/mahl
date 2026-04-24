# Szenario 6 – Das neue Lieblingsrezept (Erfassung & Pflege)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Import, manuelle Erfassung, Sub-Rezepte, Pflege)
- US-601 (Rezept-Import) [V2]
- US-602 (Manuelle Erfassung & Anhänge) [SKELETON]
- US-603 (Sub-Rezepte) [V2]
- US-604 (Zutaten-Mapping) [V2]
- US-605 (Schritte anlegen) [MVP]
- US-606 (Erweiterter Schritt-Editor) [V2]
- US-607 (Zutaten-Zuordnung) [MVP]
- US-608 (Auto-Tagging) [V2]
- US-609 (Manuelles Tagging) [MVP]
- US-610 (Gesamtzeit) [MVP]
- US-611 (Detaillierte Zeit-Erfassung) [V2]
- US-612 (Rezept-Notizen & Varianten) [V1]
- US-613 (Validierung) [V2]
- US-614 (Rezept-Korrektur) [MVP]
- US-615 (Änderungshistorie) [V2]
- US-616 (Rezept-Löschen) [MVP]
- US-617 (Schritt-Typisierung) [V2]

---

### Szenario 6: Das neue Lieblingsrezept (Erfassung & Pflege)
> "Ich habe auf Chefkoch ein tolles Rezept für 'Linsen-Dal' gefunden. Ich kopiere die URL in die App. Die App erkennt Titel, Zutaten und Schritte. Bei den Zutaten verknüpfe ich 'rote Linsen' mit meiner Datenbank-Zutat 'Linsen (rot)'. Die Schritte teile ich auf, ordne die Zutaten zu, vergebe noch den Tag "Abendessen" und speichere das Rezept.
>
> Jetzt möchte ich noch Omas Apfelkuchen erfassen. Ich habe keine URL, also tippe ich den Titel ein und fotografiere das handgeschriebene Rezept einfach ab und hänge das Foto an.
>
> Und für die Lasagne am Sonntag: Ich erstelle ein neues Rezept 'Lasagne'. Als Zutat füge ich auch mein bereits gespeichertes Rezept 'Béchamelsauce' hinzu. Die App weiß dann automatisch, dass sie Milch, Mehl und Butter für die Sauce auf die Einkaufsliste setzen muss."

**Abgeleitete User Stories:**

*   **US-601 (Rezept-Import) [V2]:** Als *Rezept-Sammler* möchte ich Rezepte einfach per URL importieren, damit ich nicht alles abtippen muss.
    *   **Akzeptanzkriterien:**
        *   Eingabe einer URL.
        *   Scraper extrahiert Titel, Zutatenliste und Zubereitungstext.
        *   Eingegebene URL wird als Rezept-Quelle gesetzt.

*   **US-602 (Manuelle Erfassung & Anhänge) [SKELETON]:** Als *Rezept-Sammler* möchte ich Rezepte manuell anlegen und Fotos (z.B. aus Büchern) als Quelle anhängen können, um auch analoge Rezepte zu digitalisieren.
    *   **Akzeptanzkriterien:**
        *   Leeres Formular für neues Rezept.
        *   Upload/Kamera-Funktion für Bilder.
        *   Hochgeladenes Bild wird als Rezept-Quelle gesetzt.

*   **US-603 (Sub-Rezepte) [V2]:** Als *Rezept-Sammler* möchte ich andere Rezepte als Zutat verwenden (z.B. Saucen), damit die Einkaufsliste automatisch alle Unter-Zutaten enthält.
    *   **Akzeptanzkriterien:**
        *   Suche nach Zutaten findet auch Rezepte.
        *   Hinzufügen eines Rezepts als Zutat möglich.
        *   Menge des *Sub-Rezepts* kann angegeben werden (z.B. "2 Portionen").
        *   Zutaten des *Sub-Rezepts* werden entsprechend der angegebenen Menge skaliert in die Einkaufsliste übernommen.

*   **US-604 (Zutaten-Mapping) [V2]:** Als *Rezept-Sammler* möchte ich importierte Zutaten meinen bekannten Datenbank-Zutaten zuordnen (Synonyme) und ggf. Modifizierer (z.B. "stückig") wählen, damit die Einkaufsliste sauber und präzise bleibt.
    *   **Akzeptanzkriterien:**
        *   UI zeigt importierten Text vs. Datenbank-Zutat.
        *   Auswahl von *Zutaten-Modifizierern* möglich.
        *   Erstellung neuer *Zutaten-Aliase* direkt im Workflow.

*   **US-605 (Schritte anlegen) [MVP]:** Als *Rezept-Sammler* möchte ich Rezept-Schritte manuell anlegen und bearbeiten, damit ich eine Anleitung habe.
    *   **Akzeptanzkriterien:**
        *   Erstellen, Bearbeiten und Löschen von einzelnen Schritten.

*   **US-606 (Erweiterter Schritt-Editor) [V2]:** Als *Rezept-Sammler* möchte ich Schritte komfortabel verwalten (Sortieren, Splitten, Zusammenführen), um Texte schnell zu strukturieren (z. B. beim Import).
    *   **Akzeptanzkriterien:**
        *   Textfeld kann an Cursor-Position gesplittet werden.
        *   Schritte können zusammengeführt werden.
        *   Reihenfolge der Schritte änderbar.

*   **US-607 (Zutaten-Zuordnung) [MVP]:** Als *Rezept-Sammler* möchte ich Zutaten den Schritten zuordnen, damit ich beim Kochen die richtige Info zur richtigen Zeit habe.
    *   **Akzeptanzkriterien:**
        *   Liste der *Rezept-Zutaten* ist neben den Schritten sichtbar.
        *   Drag & Drop (oder Klick-Zuordnung) verknüpft Zutat mit Schritt.

*   **US-608 (Auto-Tagging) [V2]:** Als *Rezept-Sammler* möchte ich, dass Tags wie "Vegetarisch" automatisch anhand der Zutaten-Tags erkannt werden, um Pflegeaufwand zu sparen.
    *   **Akzeptanzkriterien:**
        *   System prüft Tags aller Zutaten.
        *   Wenn alle Zutaten Tag X haben (oder kein Ausschluss-Tag Y), wird Rezept-Tag gesetzt.

*   **US-609 (Manuelles Tagging) [MVP]:** Als *Rezept-Sammler* möchte ich manuelle Tags (z.B. "Hauptgericht") vergeben, um Rezepte besser zu strukturieren.
    *   **Akzeptanzkriterien:**
        *   Tag-Auswahlfeld im Rezept-Editor.

*   **US-610 (Gesamtzeit) [MVP]:** Als *Rezept-Sammler* möchte ich die ungefähre Gesamtdauer eines Rezepts erfassen, um danach filtern zu können.
    *   **Akzeptanzkriterien:**
        *   Eingabefeld für Gesamtzeit.

*   **US-611 (Detaillierte Zeit-Erfassung) [V2]:** Als *Rezept-Sammler* möchte ich die Zeit detailliert aufschlüsseln (Vorbereitung, Kochen, Backen, Ruhen), wenn ich es genauer weiß.
    *   **Akzeptanzkriterien:**
        *   Eingabefelder für die vier Komponenten.
        *   Gesamtzeit errechnet sich automatisch aus der Summe (überschreibt manuelle Gesamtzeit oder ist read-only wenn Details da sind).

*   **US-612 (Rezept-Notizen & Varianten) [V1]:** Als *Rezept-Sammler* möchte ich allgemeine Notizen und Varianten eines Rezepts erfassen, um Abwandlungen oder Tipps festzuhalten.
    *   **Akzeptanzkriterien:**
        *   Allgemeines Notizfeld am Rezept.
        *   Varianten werden als spezifische Notizen abgebildet (z.B. "Variante Vegetarisch: Speck weglassen").

*   **US-613 (Validierung) [V2]:** Als *Rezept-Sammler* möchte ich beim Speichern gewarnt werden, wenn ich importierte Zutaten noch keinem Schritt zugeordnet habe, damit das Rezept vollständig ist.
    *   **Akzeptanzkriterien:**
        *   Warnmeldung bei nicht zugeordneten Zutaten.
        *   Speichern ist trotzdem möglich (Warnung, kein Blocker).

*   **US-614 (Rezept-Korrektur) [MVP]:** Als *Rezept-Sammler* möchte ich bestehende Rezepte jederzeit bearbeiten können (Mengen, Texte, Zuordnungen), um Fehler zu korrigieren oder Verbesserungen einzutragen.
    *   **Akzeptanzkriterien:**
        *   Alle Felder editierbar.

*   **US-615 (Änderungshistorie) [V2]:** Als *Rezept-Sammler* möchte ich sehen, wer wann was am Rezept geändert hat, um im Zweifel alte Stände wiederherstellen zu können.
    *   **Akzeptanzkriterien:**
        *   Liste der Änderungen (Datum, Nutzer, Feld) einsehbar.
        *   (Optional) Wiederherstellen alter Versionen.

*   **US-616 (Rezept-Löschen) [MVP]:** Als *Rezept-Sammler* möchte ich Rezepte archivieren können, wenn sie doppelt sind oder nicht geschmeckt haben, um meine Sammlung sauber zu halten.
    *   **Akzeptanzkriterien:**
        *   Archivieren-Funktion mit Sicherheitsabfrage.
        *   Archivierte Rezepte können im Admin-Bereich aus dem Archiv wiederhergestellt werden.
        *   Archivierte Rezepte werden in der Anwendung nur im Admin-Bereich angezeigt und werden ansonsten vom System ignoriert.

*   **US-617 (Schritt-Typisierung) [V2]:** Als *Rezept-Sammler* möchte ich Schritten eine Aktivitätsart (Vorbereitung, Kochen, Backen, Ruhen) zuweisen, um die Zeiten genauer zu kalkulieren und das Tracking (siehe US-517) zu ermöglichen.
    *   **Akzeptanzkriterien:**
        *   Auswahlfeld "Aktivitäts-Typ" pro Schritt im Editor.
        *   Standard-Typ ist "Vorbereitung" oder "Kochen".
