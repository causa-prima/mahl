# Szenario 5 – Das Kochen am Abend

> Teil von [docs/stories/user-stories.md](../docs/stories/user-stories.md).

## Inhalt

- Szenario-Narrativ (Auswahl, Kochmodus, Skalierung, Bewertung)
- US-501 (Pool-Liste) [MVP]
- US-502 (Smarte Sortierung) [V1]
- US-503 (Entscheidungs-Hilfe) [V2]
- US-504 (Einkaufs-Warnung) [V2]
- US-505 (Zutaten-Übersicht) [V1]
- US-506 (Koch-Start aus Pool) [V1]
- US-507 (Koch-Start aus Suche) [V1]
- US-508 (Kochmodus) [V1]
- US-509 (Schritt-Zutaten) [V1]
- US-510 (Quellen-Zugriff) [MVP]
- US-511 (Ad-Hoc Skalierung) [V1]
- US-512 (Koch-Historie & Undo) [V2]
- US-513 (Rezept-Bewertung) [PARKING]
- US-514 (Sub-Rezepte) [V2]
- US-515 (Bewertungs-Historie & Erinnerung) [PARKING]
- US-516 (Intelligenter Wach-Modus) [V1]
- US-517 (Zeit-Tracking & Optimierung) [PARKING]
- US-518 (Vorlauf-Hinweis) [PARKING]
- US-519 (Schritt-Timer) [PARKING]

---

### Szenario 5: Das Kochen am Abend
> "Endlich Feierabend. Doch schon spät geworden, da muss ich gleich anfangen zu kochen. War für heute irgendetwas spezielles eingeplant? Ich schau mal die Liste durch.. mhm, gestern gab's schon Nudeln, also heute nicht nochmal. Dann bleibt nur Flammkuchen oder das Chili - für den Flammkuchen ist es jetzt aber schon zu spät, also das Chili. Okay, erstmal schauen, ob wir alles da haben. Ja, sieht gut aus, also los geht's! Erstmal Zwiebeln und Knoblauch schneiden, dann in Öl anbraten. Wie? Nein, ich koche gerade, da kann ich nicht mit Uno spielen. Du willst helfen? Du darfst hier umrühren, aber pass bitte auf, dass nichts daneben geht. Okay, wo war ich? Ach ja, Bohnen und Mais abgießen und in den Topf. Jetzt soll es erstmal köcheln. Da kann ich schonmal etwas aufräumen. So, erledigt. Nächster Schritt? Ah ja, nochmal abschmecken und Petersilie dazugeben. Schmeckt soweit, dann kann ja der Tisch gedeckt werden. Kinder, das Essen ist fertig!"

**Abgeleitete User Stories:**

*   **US-501 (Pool-Liste) [MVP]:** Als *pragmatischer Koch* möchte ich als Startseite den aktuellen *Wochen-Pool* als einfache Liste sehen, um schnell Zugriff auf die geplanten Gerichte zu haben.
    *   **Akzeptanzkriterien:**
        *   Dashboard zeigt Rezepte des aktuellen Zeitraums.

*   **US-502 (Smarte Sortierung) [V1]:** Als *pragmatischer Koch* möchte ich, dass die Pool-Liste automatisch nach Eignung für heute sortiert ist.
    *   **Akzeptanzkriterien:**
        *   Sortierung priorisiert Rezepte, die *Tagesregeln* erfüllen, VOR Rezepten, die nur *Globale Regeln* erfüllen.

*   **US-503 (Entscheidungs-Hilfe) [V2]:** Als *pragmatischer Koch* möchte ich auf Wunsch sehen, warum ein Gericht vorgeschlagen wird (z.B. "Muss weg", "Passt zur Zeit"), um die Entscheidung besser nachvollziehen zu können.
    *   **Akzeptanzkriterien:**
        *   Info-Icon oder Text erklärt den Grund für die Sortierung.

*   **US-504 (Einkaufs-Warnung) [V2]:** Als *pragmatischer Koch* möchte ich im Wochenplan gewarnt werden, wenn für ein geplantes Rezept noch Zutaten auf der Einkaufsliste offen sind, damit ich nicht anfange zu kochen und dann Zutaten fehlen.
    *   **Akzeptanzkriterien:**
        *   Visueller Indikator am Rezept im Pool, falls zugehörige Items auf der Einkaufsliste noch nicht "erledigt" sind.
        *   Warnung beim Starten des Kochmodus, falls Zutaten fehlen.

*   **US-505 (Zutaten-Übersicht) [V1]:** Als *pragmatischer Koch* möchte ich vor dem Kochen (im Rezept-View und als erste Seite im Kochmodus) eine Gesamtliste aller Zutaten sehen, um sicherzustellen, dass alles bereitsteht.
    *   **Akzeptanzkriterien:**
        *   Anzeige der aggregierten Zutatenliste in der Rezept-Detailansicht.
        *   Erster Schritt im *Kochmodus* ist die Zutaten-Übersicht.

*   **US-506 (Koch-Start aus Pool) [V1]:** Als *pragmatischer Koch* möchte ich bei jedem Rezept im *Wochen-Pool* einen "Jetzt kochen"-Button haben, der den Kochmodus öffnet und das Gericht sofort als "gekocht" markiert.
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

*   **US-508 (Kochmodus) [V1]:** Als *pragmatischer Koch* möchte ich eine Schritt-für-Schritt-Ansicht haben, die mir genau sagt, was ich jetzt tun muss ("Zwiebeln schneiden"), damit ich auch nach Unterbrechungen (Uno spielen) sofort weiß, wo ich war.
    *   **Akzeptanzkriterien:**
        *   Vollbild-Modus.
        *   Navigation zwischen Schritten (Vor/Zurück).
        *   Aktueller Schritt ist hervorgehoben.

*   **US-509 (Schritt-Zutaten) [V1]:** Als *pragmatischer Koch* möchte ich bei jedem Schritt sehen, welche Zutaten *genau jetzt* benötigt werden, damit ich nicht in der langen Gesamtliste suchen muss.
    *   **Akzeptanzkriterien:**
        *   Pro Schritt werden nur die zugeordneten Zutaten angezeigt.
        *   Mengen sind auf die *Planungs-Portion* skaliert.

*   **US-510 (Quellen-Zugriff) [MVP]:** Als *pragmatischer Koch* möchte ich die Original-Quelle eines Rezepts (URL oder angehängtes Bild) direkt öffnen können, um im Zweifel Details im Original nachzulesen.
    *   **Akzeptanzkriterien:**
        *   Die Quelle besteht aus einem Freitext (z.B. „Blitzrezepte, S. 106", „Rezept von Marc", „Ricotta-Packung"), keiner, einer oder mehreren URLs und angehängten Bildern – jeder Teil ist optional.
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

*   **US-513 (Rezept-Bewertung) [PARKING]:** Als *pragmatischer Koch* möchte ich nach dem Essen das Rezept für einzelne Profile bewerten (z.B. "Kind 1: 1 Stern"), damit die App beim nächsten Mal bessere Vorschläge macht.
    *   **Akzeptanzkriterien:**
        *   Bewertungs-Dialog über Button am Rezept aufrufbar.
        *   Sterne-Vergabe pro *Esser-Profil*.
        *   Anzeige des Durchschnitts der vergebenen Bewertungen.
        *   Einzelne Bewertungen über Button anzeig- und änderbar.

*   **US-514 (Sub-Rezepte) [V2]:** Als *pragmatischer Koch* möchte eingebettete Rezepte einfach zubereitet.
    *   **Akzeptanzkriterien:**
        *   Schritte von als "Zutat" ausgewählten Rezepten können optional im Kochmodus als Teil des aktuellen Rezepts angezeigt werden.

*   **US-515 (Bewertungs-Historie & Erinnerung) [PARKING]:** Als *pragmatischer Koch* möchte ich an die Bewertung erinnert werden und eine Historie der Bewertungen pro Profil sehen, um schwankende Vorlieben (z.B. bei Kindern) besser einschätzen zu können.
    *   **Akzeptanzkriterien:**
        *   Speicherung einer Bewertungshistorie (Datum + Wertung) pro *Esser-Profil*.
        *   Push-Benachrichtigung zur ca. 30 Min. nach Beenden des Kochmodus (oder Display-Aus).
        *   Klick auf Benachrichtigung öffnet Dialog zur schnellen Bewertung für alle Profile.
        *   Auswertung zeigt Verlauf/Trend anstatt nur Durchschnitt.

*   **US-516 (Intelligenter Wach-Modus) [V1]:** Als *pragmatischer Koch* möchte ich, dass das Display während der aktiven Zubereitung an bleibt, damit ich es nicht mit schmutzigen Händen entsperren muss.
    *   **Akzeptanzkriterien:**
        *   Wake-Lock ist im Kochmodus aktiv.
        *   Dauer des Wake-Locks beschränkt auf `Vorbereitungszeit + Kochzeit` (oder `Gesamtzeit`), danach System-Timeout (Akku-Schutz).

*   **US-517 (Zeit-Tracking & Optimierung) [PARKING]:** Als *pragmatischer Koch* möchte ich, dass die App misst, wie lange ich für ein Rezept brauche, damit die Zeitangabe stimmt, ohne dass ich sie pflege.
    *   **Akzeptanzkriterien:**
        *   Der Kochmodus misst je Kochvorgang die Zeit, in der man arbeitet – vom Start bis zum Abschluss. Der letzte Schritt trägt statt „Weiter" gut sichtbar „Kochen abschließen", damit das Ende nicht vergessen wird.
        *   Wartezeiten, in denen etwas ohne Aufsicht backt, gart oder geht (oft am Ende, wenn niemand mehr die App öffnet), werden nicht gemessen, sondern von Hand erfasst; sie zählen nicht zur gemessenen Zeit, stehen aber daneben.
        *   Ab genug Messungen zeigt das Rezept die Zeit als „ca. X Minuten" (Median) samt Spanne; bis dahin gilt die von Hand erfasste Zeit (US-610).
        *   Weicht eine neue Messung stark vom Median ab, warnt die App sofort und bietet passende Aktionen an (verwerfen, korrigieren, übernehmen), damit die Datenbasis sauber bleibt.
        *   Eine Historie der Messungen je Rezept lässt sich bearbeiten: ein Kochvorgang mit Unterbrechung wird korrigiert oder gelöscht.
        *   Begriffe, Zusammenspiel mit US-610/US-611/US-617 und Wartezeiten mitten im Rezept: offene Frage zum Zeitmodell in `docs/open-questions.md`, fällig im Workshop von US-610.
        *   Bewusst nicht je Schritt gemessen: Schritte laufen oft parallel („In der Zwischenzeit …" – in 18 von 114 Rezepten der bisherigen Sammlung). Die Verweildauer eines Schritts sagt dann nichts über seine Dauer – während des Backens steht man längst beim nächsten Schritt –, die Summe aller Verweildauern ist aber genau die Gesamtdauer.

*   **US-518 (Vorlauf-Hinweis) [PARKING]:** Als *Feierabend-Planer* möchte ich sehen, welche Rezepte im Pool schon am Vortag oder Stunden vorher begonnen werden müssen (Teig über Nacht, Kühlzeit), damit ich rechtzeitig anfange.
    *   **Akzeptanzkriterien:**
        *   Ein Rezept kann einen Vorlauf tragen (z.B. „am Vortag", „12 Stunden").
        *   Rezepte mit Vorlauf sind im Pool hervorgehoben. Eine Erinnerung zu einem Zeitpunkt ist nicht vorgesehen – der Pool kennt keine Tages-Zuordnung.
    *   **Anlass:** In der bisherigen Sammlung u.a. Pizzateig (24 h), Coleslaw (12 h), Cheesecake und Frankfurter Kranz (über Nacht bzw. am Vorabend).

*   **US-519 (Schritt-Timer) [PARKING]:** Als *pragmatischer Koch* möchte ich bei einem Schritt mit Wartezeit („20 Minuten backen") einen Timer im Kochmodus starten, damit ich währenddessen etwas anderes tun kann.
    *   **Akzeptanzkriterien:**
        *   Timer startbar aus dem Kochmodus; nach Ablauf ein deutliches Signal.
    *   **Abwägung:** Meist stellt man den Timer direkt an Herd oder Ofen – ein eigener Timer lohnt nur in manchen Fällen.
