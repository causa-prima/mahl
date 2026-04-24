# Szenario 5 – Das Kochen am Abend

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Auswahl, Kochmodus, Skalierung, Bewertung)
- US-501 (Pool-Liste) [MVP]
- US-502 (Smarte Sortierung) [MVP]
- US-503 (Entscheidungs-Hilfe) [V2]
- US-504 (Einkaufs-Warnung) [V2]
- US-505 (Zutaten-Übersicht) [MVP]
- US-506 (Koch-Start aus Pool) [MVP]
- US-507 (Koch-Start aus Suche) [V1]
- US-508 (Kochmodus) [MVP]
- US-509 (Schritt-Zutaten) [MVP]
- US-510 (Quellen-Zugriff) [MVP]
- US-511 (Ad-Hoc Skalierung) [V1]
- US-512 (Koch-Historie & Undo) [V2]
- US-513 (Rezept-Bewertung) [V2]
- US-514 (Sub-Rezepte) [V2]
- US-515 (Bewertungs-Historie & Erinnerung) [V2]
- US-516 (Intelligenter Wach-Modus) [V1]
- US-517 (Zeit-Tracking & Optimierung) [V2]

---

### Szenario 5: Das Kochen am Abend
> "Endlich Feierabend. Doch schon spät geworden, da muss ich gleich anfangen zu kochen. War für heute irgendetwas spezielles eingeplant? Ich schau mal die Liste durch.. mhm, gestern gab's schon Nudeln, also heute nicht nochmal. Dann bleibt nur Flammkuchen oder das Chili - für den Flammkuchen ist es jetzt aber schon zu spät, also das Chili. Okay, erstmal schauen, ob wir alles da haben. Ja, sieht gut aus, also los geht's! Erstmal Zwiebeln und Knoblauch schneiden, dann in Öl anbraten. Wie? Nein, ich koche gerade, da kann ich nicht mit Uno spielen. Du willst helfen? Du darfst hier umrühren, aber pass bitte auf, dass nichts daneben geht. Okay, wo war ich? Ach ja, Bohnen und Mais abgießen und in den Topf. Jetzt soll es erstmal köcheln. Da kann ich schonmal etwas aufräumen. So, erledigt. Nächster Schritt? Ah ja, nochmal abschmecken und Petersilie dazugeben. Schmeckt soweit, dann kann ja der Tisch gedeckt werden. Kinder, das Essen ist fertig!"

**Abgeleitete User Stories:**

*   **US-501 (Pool-Liste) [MVP]:** Als *pragmatischer Koch* möchte ich als Startseite den aktuellen *Wochen-Pool* als einfache Liste sehen, um schnell Zugriff auf die geplanten Gerichte zu haben.
    *   **Akzeptanzkriterien:**
        *   Dashboard zeigt Rezepte des aktuellen Zeitraums.

*   **US-502 (Smarte Sortierung) [MVP]:** Als *pragmatischer Koch* möchte ich, dass die Pool-Liste automatisch nach Eignung für heute sortiert ist.
    *   **Akzeptanzkriterien:**
        *   Sortierung priorisiert Rezepte, die *Tagesregeln* erfüllen, VOR Rezepten, die nur *Globale Regeln* erfüllen.

*   **US-503 (Entscheidungs-Hilfe) [V2]:** Als *pragmatischer Koch* möchte ich auf Wunsch sehen, warum ein Gericht vorgeschlagen wird (z.B. "Muss weg", "Passt zur Zeit"), um die Entscheidung besser nachvollziehen zu können.
    *   **Akzeptanzkriterien:**
        *   Info-Icon oder Text erklärt den Grund für die Sortierung.

*   **US-504 (Einkaufs-Warnung) [V2]:** Als *pragmatischer Koch* möchte ich im Wochenplan gewarnt werden, wenn für ein geplantes Rezept noch Zutaten auf der Einkaufsliste offen sind, damit ich nicht anfange zu kochen und dann Zutaten fehlen.
    *   **Akzeptanzkriterien:**
        *   Visueller Indikator am Rezept im Pool, falls zugehörige Items auf der Einkaufsliste noch nicht "erledigt" sind.
        *   Warnung beim Starten des Kochmodus, falls Zutaten fehlen.

*   **US-505 (Zutaten-Übersicht) [MVP]:** Als *pragmatischer Koch* möchte ich vor dem Kochen (im Rezept-View und als erste Seite im Kochmodus) eine Gesamtliste aller Zutaten sehen, um sicherzustellen, dass alles bereitsteht.
    *   **Akzeptanzkriterien:**
        *   Anzeige der aggregierten Zutatenliste in der Rezept-Detailansicht.
        *   Erster Schritt im *Kochmodus* ist die Zutaten-Übersicht.

*   **US-506 (Koch-Start aus Pool) [MVP]:** Als *pragmatischer Koch* möchte ich bei jedem Rezept im *Wochen-Pool* einen "Jetzt kochen"-Button haben, der den Kochmodus öffnet und das Gericht sofort als "gekocht" markiert.
    *   **Akzeptanzkriterien:**
        *   Button "Jetzt kochen" an Rezepten im *Wochen-Pool*.
        *   Startet Kochmodus.
        *   Rezept wird aus dem *Wochen-Pool* entfernt.
        *   Ein neuer Eintrag in der globalen *Koch-Historie* wird angelegt (Datum + Rezept).

*   **US-507 (Koch-Start aus Suche) [V1]:** Als *pragmatischer Koch* möchte ich auch aus der allgemeinen Rezept-Liste/Suche heraus den Kochmodus starten können (z.B. für spontanes Kochen ohne Planung).
    *   **Akzeptanzkriterien:**
        *   Button "Jetzt kochen" in der Rezept-Detailansicht (außerhalb des Pools).
        *   Startet Kochmodus.
        *   Ein neuer Eintrag in der globalen *Koch-Historie* wird angelegt (Datum + Rezept).

*   **US-508 (Kochmodus) [MVP]:** Als *pragmatischer Koch* möchte ich eine Schritt-für-Schritt-Ansicht haben, die mir genau sagt, was ich jetzt tun muss ("Zwiebeln schneiden"), damit ich auch nach Unterbrechungen (Uno spielen) sofort weiß, wo ich war.
    *   **Akzeptanzkriterien:**
        *   Vollbild-Modus.
        *   Navigation zwischen Schritten (Vor/Zurück).
        *   Aktueller Schritt ist hervorgehoben.

*   **US-509 (Schritt-Zutaten) [MVP]:** Als *pragmatischer Koch* möchte ich bei jedem Schritt sehen, welche Zutaten *genau jetzt* benötigt werden, damit ich nicht in der langen Gesamtliste suchen muss.
    *   **Akzeptanzkriterien:**
        *   Pro Schritt werden nur die zugeordneten Zutaten angezeigt.
        *   Mengen sind auf die *Planungs-Portion* skaliert.

*   **US-510 (Quellen-Zugriff) [MVP]:** Als *pragmatischer Koch* möchte ich die Original-Quelle eines Rezepts (URL oder angehängtes Bild) direkt öffnen können, um im Zweifel Details im Original nachzulesen.
    *   **Akzeptanzkriterien:**
        *   Link zur Quell-URL öffnet sich in einem neuen Browser-Tab.
        *   Angehängte Dateien/Bilder können in einer Vorschau geöffnet werden.

*   **US-511 (Ad-Hoc Skalierung) [V1]:** Als *pragmatischer Koch* möchte ich die Portionsanzahl (Standard: "Personen") direkt im Kochmodus ändern können (z.B. "heute essen 5 statt 4 Personen"), wobei alle Mengen sofort umgerechnet werden.
    *   **Akzeptanzkriterien:**
        *   Eingabefeld für *Planungs-Portion* im Rezept (Default-Einheit: "Personen").
        *   Alle Zutatenmengen aktualisieren sich sofort.

*   **US-512 (Koch-Historie & Undo) [V2]:** Als *pragmatischer Koch* möchte ich ein versehentlich als "gekocht" markiertes Gericht wieder in den Pool zurückholen können, falls sich der Plan spontan geändert hat.
    *   **Akzeptanzkriterien:**
        *   Liste der gekochten Gerichte des aktuellen Tages einsehbar.
        *   Funktion "Nicht gekocht" fügt ein Rezept wieder dem *Wochen-Pool* hinzu.

*   **US-513 (Rezept-Bewertung) [V2]:** Als *pragmatischer Koch* möchte ich nach dem Essen das Rezept für einzelne Profile bewerten (z.B. "Kind 1: 1 Stern"), damit die App beim nächsten Mal bessere Vorschläge macht.
    *   **Akzeptanzkriterien:**
        *   Bewertungs-Dialog über Button am Rezept aufrufbar.
        *   Sterne-Vergabe pro *Esser-Profil*.
        *   Anzeige des Durchschnitts der vergebenen Bewertungen.
        *   Einzelne Bewertungen über Button anzeig- und änderbar.

*   **US-514 (Sub-Rezepte) [V2]:** Als *pragmatischer Koch* möchte eingebettete Rezepte einfach zubereitet.
    *   **Akzeptanzkriterien:**
        *   Schritte von als "Zutat" ausgewählten Rezepten können optional im Kochmodus als Teil des aktuellen Rezepts angezeigt werden.

*   **US-515 (Bewertungs-Historie & Erinnerung) [V2]:** Als *pragmatischer Koch* möchte ich an die Bewertung erinnert werden und eine Historie der Bewertungen pro Profil sehen, um schwankende Vorlieben (z.B. bei Kindern) besser einschätzen zu können.
    *   **Akzeptanzkriterien:**
        *   Speicherung einer Bewertungshistorie (Datum + Wertung) pro *Esser-Profil*.
        *   Push-Benachrichtigung zur ca. 30 Min. nach Beenden des Kochmodus (oder Display-Aus).
        *   Klick auf Benachrichtigung öffnet Dialog zur schnellen Bewertung für alle Profile.
        *   Auswertung zeigt Verlauf/Trend anstatt nur Durchschnitt.

*   **US-516 (Intelligenter Wach-Modus) [V1]:** Als *pragmatischer Koch* möchte ich, dass das Display während der aktiven Zubereitung an bleibt, damit ich es nicht mit schmutzigen Händen entsperren muss.
    *   **Akzeptanzkriterien:**
        *   Wake-Lock ist im Kochmodus aktiv.
        *   Dauer des Wake-Locks beschränkt auf `Vorbereitungszeit + Kochzeit` (oder `Gesamtzeit`), danach System-Timeout (Akku-Schutz).

*   **US-517 (Zeit-Tracking & Optimierung) [V2]:** Als *pragmatischer Koch* möchte ich, dass die App misst, wie lange ich für Schritte brauche, um meine Zeitangaben im Rezept automatisch zu korrigieren.
    *   **Akzeptanzkriterien:**
        *   Kochmodus misst Verweildauer pro Schritt im Hintergrund.
        *   Nach Abschluss: Vorschlag zur Aktualisierung der Metadaten (Vorbereitungszeit/Kochzeit) basierend auf gemessenen Werten (nur für aktive Schritt-Typen).
