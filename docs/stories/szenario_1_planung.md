# Szenario 1 – Die Planung am Donnerstagabend

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Planung am Abend, Wizard, Regeln)
- US-101 (Planungs-Wizard) [V1]
- US-102 (Muss-Zutaten) [V2]
- US-103 (Muss-Rezepte) [MVP]
- US-104 (Session-Regeln) [V2]
- US-105 (Automatische Vorschläge & Regeln) [MVP]
- US-106 (Besuchs-Planung) [MVP]
- US-107 (Tagesregeln) [V2]
- US-108 (Zeit-Budget) [V2]
- US-109 (Konfliktlösung) [V2]
- US-110 (Vorschlag ändern) [V2]

---

### Szenario 1: Die Planung am Donnerstagabend
> "Es ist Donnerstag Abend. Nach einem langen Tag sind die Kinder endlich im Bett. Oh nein, morgen muss ja für die kommende Woche eingekauft werden! Ich starte den Planungs-Assistenten. Er fragt mich zuerst, bis wann ich planen möchte und schlägt er mir nächsten Donnerstag vor. Dann fragt er: 'Muss etwas weg?'. Ich schaue in den Kühlschrank: 'Ja, der halbe Kürbis!'. Ich gebe 'Kürbis' ein. Nächste Frage: 'Gibt es Wünsche?'. Ich denke an den Geburtstag am Samstag und füge eine Maitorte und Blätterteigschnecken als Snacks hinzu. Dabei erhöhe ich gleich die Menge der Blätterteigschnecken für den Besuch. Nächste Frage: 'Welche Regeln soll ich beachten'? Ich sehe die Regeln für nur einmal Fleisch in der Woche, kurze Rezepte am Dienstag (da ist Fußball) und das Pfannkuchen-Frühstück am ersten Sonntag im Monat - das passt! Er generiert einen Vorschlag, der den Kürbis verwertet und den Rest auffüllt. Perfekt!"

**Abgeleitete User Stories:**

*   **US-101 (Planungs-Wizard) [V1]:** Als *Feierabend-Planer* möchte ich durch einen Assistenten geführt werden (Enddatum -> Reste -> Wünsche -> Regeln -> Generierung), damit ich nichts vergesse und der Prozess strukturiert ist.
    *   **Akzeptanzkriterien:**
        *   Der Wizard zeigt einen Eingabedialog für das "Enddatum" (Default: 7 Tage nach dem aktuellen Datum).
        *   Bestehende Rezepte im *Wochen-Pool* bleiben erhalten; nur leere Slots bis zum Enddatum werden aufgefüllt.
        *   Validierung: Wenn bis zum Enddatum keine Slots frei sind, erscheint eine Meldung (Optionen: Enddatum anpassen oder Abbrechen).
        *   Abbruch des Wizards verwirft den temporären *Planungs-Pool*.
        *   Abschluss ("Plan übernehmen") speichert die generierten Einträge in den *Wochen-Pool*.

*   **US-102 (Muss-Zutaten) [V2]:** Als *Feierabend-Planer* möchte ich Zutaten angeben, die verbraucht werden müssen (Reste), damit der Algorithmus passende Rezepte priorisiert.
    *   **Akzeptanzkriterien:**
        *   Eingabe von Zutaten über Suche/Autocomplete.
        *   Der Algorithmus priorisiert Rezepte, die diese Zutaten enthalten (höherer Score).
        *   Wenn keine Rezepte gefunden werden, wird der Nutzer informiert.

*   **US-103 (Muss-Rezepte) [MVP]:** Als *Feierabend-Planer* möchte ich Rezepte vorab festlegen (z.B. für Geburtstag), um die der restliche Plan herumgebaut wird.
    *   **Akzeptanzkriterien:**
        *   Nutzer kann spezifische Rezepte für bestimmte Tage pinnen.
        *   **Mengen-Anpassung:** Beim Auswählen kann direkt die *Planungs-Portion* angepasst werden (Default: *Basis-Portion* des Rezepts).
        *   Gepinnte Rezepte werden vom Generator nicht überschrieben.

*   **US-104 (Session-Regeln) [V2]:** Als *Feierabend-Planer* möchte ich im Wizard die Regeln für diese spezifische Planung anpassen (z.B. "Dienstag fällt Fußball aus, also gehen auch längere Rezepte"), ohne die globalen Einstellungen zu ändern.
    *   **Akzeptanzkriterien:**
        *   Wizard-Schritt zur Übersicht der aktiven Regeln (Global & Tagesregeln).
        *   Möglichkeit, Regeln für diesen Lauf zu deaktivieren oder temporäre Regeln hinzuzufügen.

*   **US-105 (Automatische Vorschläge & Regeln) [MVP]:** Als *Feierabend-Planer* möchte ich, dass der Rest des Plans automatisch basierend auf Regeln (Abwechslung, Beliebtheit, Dienstag=Schnell, Sonntag=Pfannkuchen) aufgefüllt wird.
    *   **Akzeptanzkriterien:**
        *   Leere Slots werden automatisch gefüllt.
        *   Global definierte *Harte Regeln* (z.B. "Max 2x Fleisch") werden strikt eingehalten.
        *   *Tagesregeln* (z.B. "Dienstag < 30min") werden eingehalten.

*   **US-106 (Besuchs-Planung) [MVP]:** Als *Feierabend-Planer* möchte ich für den kommenden Samstag die Portionsanzahl erhöhen (Besuch), damit die Einkaufsliste automatisch stimmt.
    *   **Akzeptanzkriterien:**
        *   Die *Planungs-Portion* kann pro *Plan-Eintrag* individuell gesetzt werden.
        *   Default ist die *Basis-Portion* des Rezepts.

*   **US-107 (Tagesregeln) [V2]:** Als *Feierabend-Planer* möchte ich Regeln für spezifische Tage definieren können (z.B. "1. Sonntag im Monat = Pfannkuchen"), damit wiederkehrende Rituale automatisch eingeplant sind.
    *   **Akzeptanzkriterien:**
        *   Regeln können an Wochentage oder Datums-Muster (z.B. "jeden 1. Sonntag") gebunden werden.

*   **US-108 (Zeit-Budget) [V2]:** Als *Feierabend-Planer* möchte ich sicherstellen, dass an stressigen Tagen (Dienstag = Fußball) nur schnelle Rezepte vorgeschlagen werden, damit das Kochen in den Tagesablauf passt.
    *   **Akzeptanzkriterien:**
        *   Rezepte haben eine detaillierte Zeit-Erfassung: Vorbereitungszeit, Kochzeit, Backzeit, Ruhezeit.
        *   Regeln können auf die Gesamtdauer oder einzelne Komponenten (z.B. "Aktive Arbeitszeit") filtern.

*   **US-109 (Konfliktlösung) [V2]:** Als *Feierabend-Planer* möchte ich informiert werden, wenn meine Regeln zu streng sind (keine Vorschläge gefunden), und gefragt werden, welche Regel ich temporär lockern möchte.
    *   **Akzeptanzkriterien:**
        *   Bei leerer Ergebnismenge wird eine Fehlermeldung angezeigt.
        *   Der Nutzer kann wählen, welche *Harte Regel* ignoriert werden soll.

*   **US-110 (Vorschlag ändern) [V2]:** Als *Feierabend-Planer* möchte ich einen Vorschlag im generierten Plan ändern, falls er mir nicht zusagt.
    *   **Akzeptanzkriterien:**
        *   Option A: "Slot leeren" (entfernt Eintrag, Slot ist frei für neue manuelle Zuordnung).
        *   Option B: "Alternative vorschlagen" (ersetzt Eintrag durch den nächstbesten Kandidaten aus dem Algorithmus).
