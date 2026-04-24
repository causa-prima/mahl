# Szenario 9 – Datenpflege & Konfiguration

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Tag-Hierarchie, Einheiten, Vorrat, Tag-Sortierung, Backup)
- US-901 (Tag-Hierarchie) [V2]
- US-902 (Einheiten-Management) [MVP]
- US-903 (Profil-Verwaltung) [V2]
- US-904 (Zutaten-Verwaltung) [SKELETON]
- US-905 (Zutaten-Aliase) [V1]
- US-906 (Vorrats-Management) [MVP]
- US-907 (Tag-Sortierung) [V1]
- US-908 (Zutaten zusammenführen) [V2]
- US-909 (Backup erstellen) [V2]
- US-910 (Backup wiederherstellen) [V2]

---

### Szenario 9: Datenpflege & Konfiguration
> "Ich habe etwas Zeit und möchte meine Datenbank aufräumen. Ich sehe, dass ich viele Tags habe, die eigentlich zusammengehören. Ich ordne 'Rind', 'Schwein' und 'Geflügel' dem Ober-Tag 'Fleisch' zu. Jetzt greift meine Regel 'Kein Fleisch' automatisch auch für alle Hähnchen-Rezepte. Außerdem sehe ich, dass ich bei 'Mehl' noch keine Umrechnung habe. Ich trage ein: '1 EL = 12g', damit ich auch Rezepte nutzen kann, die diese Einheit nutzen. Schließlich markiere ich noch Salz und Öl als 'Immer vorrätig', damit diese Standard-Zutaten nicht ständig meine Einkaufsliste verstopfen.
>
> Danach kümmere ich mich um die Einkaufsliste: Ich möchte, dass sie so sortiert ist, wie ich durch meinen Stamm-Supermarkt laufe. Ich öffne die Einstellungen und schiebe die Tag-Gruppen in die richtige Reihenfolge: Erst 'Obst & Gemüse', dann 'Kühlregal', dann 'Trockensortiment'. Die App zeigt mir an, dass ich 'Getränke' vergessen habe, also füge ich das noch am Ende hinzu."

**Abgeleitete User Stories:**

*   **US-901 (Tag-Hierarchie) [V2]:** Als *Rezept-Sammler* möchte ich Tags strukturieren (z.B. "Kartoffel" gehört zu "Gemüse" UND "Sättigungsbeilage"), damit Regeln wie "Kein Fleisch" auch Unterkategorien erfassen (DAG-Struktur).
    *   **Akzeptanzkriterien:**
        *   Tag-Editor erlaubt Zuweisung von Eltern-Tags.
        *   Zyklen werden verhindert (Gerichteter azyklischer Graph).

*   **US-902 (Einheiten-Management) [MVP]:** Als *Rezept-Sammler* möchte ich Umrechnungsfaktoren für Zutaten definieren (z.B. EL -> Gramm), damit die Einkaufsliste korrekte Summen bilden kann.
    *   **Akzeptanzkriterien:**
        *   Eingabe von Faktor X Einheit A = Y Einheit B.

*   **US-903 (Profil-Verwaltung) [V2]:** Als *Feierabend-Planer* möchte ich Esser-Profile (z.B. "Kind 1") anlegen, damit ich für diese Personen spezifische Bewertungen und Vorlieben hinterlegen kann.
    *   **Akzeptanzkriterien:**
        *   CRUD für *Esser-Profile*.

*   **US-904 (Zutaten-Verwaltung) [SKELETON]:** Als *Rezept-Sammler* möchte ich neue Zutaten manuell anlegen und bearbeiten (Tags, Basiseinheit), damit ich sie in Rezepten nutzen kann.
    *   **Akzeptanzkriterien:**
        *   CRUD für Zutaten (Name, Einheit, Tags).

*   **US-905 (Zutaten-Aliase) [V1]:** Als *Rezept-Sammler* möchte ich Aliase für Zutaten definieren (z.B. "Möhre" -> "Karotte"), um den Import und die Suche robuster zu machen.
    *   **Akzeptanzkriterien:**
        *   Verwaltung von *Zutaten-Aliasen* in der Zutaten-Maske.

*   **US-906 (Vorrats-Management) [MVP]:** Als *Feierabend-Planer* möchte ich Standard-Zutaten (Salz, Öl) in den Stammdaten als "Immer vorrätig" markieren, damit sie standardmäßig nicht auf der Einkaufsliste erscheinen (außer man erzwingt es).
    *   **Akzeptanzkriterien:**
        *   Checkbox "Immer vorrätig" in den Zutaten-Stammdaten.
        *   Diese Zutaten werden beim Generieren der Einkaufsliste ignoriert.

*   **US-907 (Tag-Sortierung) [V1]:** Als *Feierabend-Planer* möchte ich die globale Reihenfolge der Tags für die Einkaufsliste definieren, um Laufwege zu optimieren.
    *   **Akzeptanzkriterien:**
        *   Liste aller bekannten Tags (Kategorien).
        *   Möglichkeit zum Ändern der Reihenfolge.
        *   **Coverage-Check:** Visueller Hinweis, ob alle Zutaten/Items durch die sortierten Tags abgedeckt sind (oder ob welche in "Unassigned" landen würden).

*   **US-908 (Zutaten zusammenführen) [V2]:** Als *Rezept-Sammler* möchte ich zwei Zutaten zusammenführen (eine bleibt, die andere wird Alias), um Duplikate in der Datenbank zu bereinigen.
    *   **Akzeptanzkriterien:**
        *   Auswahl von Quell-Zutat (wird gelöscht) und Ziel-Zutat (bleibt).
        *   Name der Quell-Zutat wird als *Zutaten-Alias* der Ziel-Zutat hinzugefügt.
        *   Alle Referenzen in Rezepten werden automatisch auf die Ziel-Zutat umgebogen.

*   **US-909 (Backup erstellen) [V2]:** Als *Rezepte-Sammler* möchte ich ein vollständiges Backup aller Anwendungsdaten erstellen (Rezepte, Zutaten, Bilder, Einstellungen), damit ich bei Datenverlust oder Umzug auf einen neuen Server wiederherstellen kann.
    *   **Akzeptanzkriterien:**
        *   Menü-Punkt "Backup erstellen" in den Einstellungen
        *   System erstellt ein Backup aller Anwendungsdaten (Datenbank + hochgeladene Dateien)
        *   Download als ZIP-Datei
        *   Backup enthält Timestamp im Dateinamen (z.B. `mahl-backup-2026-02-17-143000.zip`)

*   **US-910 (Backup wiederherstellen) [V2]:** Als *Rezepte-Sammler* möchte ich ein Backup wiederherstellen, um nach Datenverlust oder Migration auf einen neuen Server meine Daten zurückzuholen.
    *   **Akzeptanzkriterien:**
        *   Menü-Punkt "Backup wiederherstellen" in den Einstellungen
        *   Upload einer Backup-ZIP-Datei
        *   System prüft Backup-Integrität (enthält alle erforderlichen Komponenten?)
        *   Bestätigungsdialog: "Achtung: Alle aktuellen Daten werden überschrieben!"
        *   Nach Restore: Automatischer Neustart der App (oder Hinweis, dass User neu laden muss)
