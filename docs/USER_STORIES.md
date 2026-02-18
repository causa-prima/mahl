# User Stories & Szenarien

Dieses Dokument beschreibt die Anforderungen aus der Perspektive der Nutzer, basierend auf realen Alltagsszenarien. Es dient als "Single Source of Truth" für die Entwicklung.

## Vision & Mission

**Vision (Das Zielbild)**
> "Mahl befreit den Familienalltag von der mentalen Last der Essensplanung und macht gesunde, abwechslungsreiche Ernährung zum stressfreien Selbstläufer."

**Mission (Der Auftrag)**
> "Wir entwickeln einen intelligenten Assistenten, der die Lücke zwischen Planung, Einkauf und Kochen schließt. Wir eliminieren Entscheidungsmüdigkeit durch smarte Vorschläge, optimieren den Einkauf durch Kontext-Wissen und führen entspannt durch die Zubereitung - immer mit dem Ziel, Zeit zu sparen und Verschwendung zu vermeiden."

## Priorisierung (Tags)

*   **[SKELETON]:** "Walking Skeleton". Die absolute Mindestanforderung, um einen technischen Durchstich (End-to-End) zu ermöglichen. Ohne dies ist die App nicht nutzbar.
*   **[MVP]:** "Minimum Viable Product". Der Funktionsumfang, der nötig ist, um dem Nutzer echten Mehrwert zu bieten und die Mission zu erfüllen.
*   **[V1]:** "Version 1.0" (MMP). Der erste vollständige Release, der sich "rund" anfühlt. Enthält Komfortfunktionen, Fehlerbehandlung und Features, die für eine dauerhafte Nutzung wichtig sind.
*   **[V2]:** "Version 2.0". Echte Erweiterungen, neue Module und Optimierungen für die Zukunft.

---

## 1. Personas

Basierend auf den Szenarien haben wir folgende Rollen identifiziert:

*   **Der Feierabend-Planer (Planung):** Plant abends, wenn die Energie niedrig ist. Braucht Automatisierung und intelligente Vorschläge, um Entscheidungen zu minimieren.
*   **Der eilige Einkäufer (Einkauf Single):** Kauft unter Zeitdruck (Mittagspause). Braucht Kontextinformationen ("Wofür ist das?") für schnelle Entscheidungen im Laden.
*   **Der Familien-Einkäufer (Einkauf Gruppe):** Kauft mit Kindern ein. Braucht Robustheit gegen Fehlbedienung (Undo) und Übersicht.
*   **Der pragmatische Koch (Zubereitung):** Kocht unter Zeitdruck und mit Ablenkungen. Braucht klare Führung und schnelle Entscheidungshilfen.
*   **Der Rezept-Sammler (Verwaltung):** Pflegt die Datenbank. Braucht Import-Tools und einfache Pflege für hohe Datenqualität.

---

## 2. Szenarien & Abgeleitete Stories

### Szenario 0: Der App-Start (Kontext)
> "Ich nehme mein Handy in die Hand, um einzukaufen. Die App öffnet direkt die Einkaufsliste. Später am Abend nehme ich das Tablet in der Küche. Die App öffnet direkt den Kochmodus für das heutige Rezept."

**Abgeleitete User Stories:**

*   **US-001 (Geräte-Kontext) [V1]:** Als *Nutzer* möchte ich eine Standardansicht definieren, damit ich sofort im richtigen Kontext bin (Handy -> Einkauf, Tablet -> Kochen).
    *   **Akzeptanzkriterien:**
        *   Einstellung "Standard-Startseite" in den Nutzereinstellungen pro Gerät speicherbar.
        *   Beim App-Start wird die konfigurierte Ansicht geladen.

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

---

### Szenario 2: Der Vorrats-Check (Freitagmorgen)
> "Der Plan steht. Bevor ich einkaufen gehe, öffne ich die Einkaufsliste. Die App zeigt mir alle benötigten Zutaten. Ich gehe zum Vorratsschrank. 'Mehl haben wir noch', klick, abgehakt. 'Milch... oh, nur noch ein Schluck da', ich lasse es auf der Liste, reduziere aber die Menge von 2 auf 1 Liter. 'Salz' wird gar nicht erst angezeigt, weil es als 'Immer da' markiert ist. Perfekt, jetzt habe ich nur das auf der Liste, was ich wirklich kaufen muss."

**Abgeleitete User Stories:**

*   **US-201 (Pantry-Check) [SKELETON]:** Als *Feierabend-Planer* möchte ich vor dem Einkauf eine Liste aller benötigten Zutaten sehen und vorhandene Dinge abhaken, damit ich nichts Doppeltes kaufe.
    *   **Akzeptanzkriterien:**
        *   Liste zeigt alle Zutaten aus dem Plan (außer solche mit Flag "Immer vorrätig").
        *   Abhaken markiert das Item als "gekauft" (setzt BoughtAt-Timestamp). Item wird nicht gelöscht, sondern in Bereich "Zuletzt gekauft" verschoben (siehe US-303).

*   **US-202 (Mengen-Anpassung) [MVP]:** Als *Feierabend-Planer* möchte ich die Menge von Artikeln auf der Liste reduzieren (z.B. "brauche nur noch die Hälfte"), um Reste zu berücksichtigen.
    *   **Akzeptanzkriterien:**
        *   Menge jedes Eintrags ist editierbar.
        *   **Delta-Logik:** Änderungen werden als *Delta-Menge* gespeichert, ohne die Rezept-Zuordnung zu ändern.
        *   Positive Änderung = Zusätzliche Menge; Negative Änderung = Reduzierte Menge.
        *   Wenn Gesamtmenge (Rezept-Summe + Delta) <= 0, wird der Eintrag von der Liste entfernt.
        *   Änderung gilt nur für diesen Einkaufs-Zyklus.

*   **US-203 (Fix-Eintrag) [V1]:** Als *Feierabend-Planer* möchte ich bestimmte Artikel (z.B. Milch, Joghurt) auf der Einkaufsliste "pinnen", damit sie standardmäßig auf jeder neuen Einkaufsliste erscheinen, auch wenn ich sie beim letzten Mal abgehakt habe.
    *   **Akzeptanzkriterien:**
        *   Artikel können als *Fix-Eintrag* markiert werden.
        *   Beim Abhaken verschwinden sie (oder werden als erledigt markiert) für den aktuellen Einkauf.
        *   Beim nächsten Einkaufs-Zyklus (oder nach Reset) erscheinen sie automatisch wieder als "offen".

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

---

### Szenario 4: Der Familien-Einkauf
> "Na gut, wir gehen alle gemeinsam einkaufen. Also ab zum Einkaufsladen! Ja okay, wir nehmen ein paar Bananen mit. Na gut, auch noch ein paar Weintrauben. Packst du bitte die Gnocchi ein? Hey, vorsicht! Mist, wurde jetzt aus versehen etwas auf der Einkaufsliste abgehakt? Ah, ja, die Butter haben wir noch nicht, also wieder auf die Liste damit. Nein, wir haben davon schon genug zuhause, das sollt ihr erstmal aufessen! Oh, schau mal, Papa hat die Sahne schon geholt und abgehakt, danke! Okay, alles drin - ab zur Kasse und dann nach Hause."

**Abgeleitete User Stories:**

*   **US-401 (Undo-Funktion) [V1]:** Als *Familien-Einkäufer* möchte ich versehentlich abgehakte Artikel einfach wiederherstellen können, damit Fehlbedienungen im Chaos kein Problem sind.
    *   **Akzeptanzkriterien:**
        *   Klick auf ein Item im Bereich "Zuletzt gekauft" stellt Item wieder auf "Offen".

*   **US-402 (Live-Sync) [V2]:** Als *Familien-Einkäufer* möchte ich sehen, wenn mein Partner Artikel auf seinem Gerät abhakt ("Sahne schon geholt"), damit wir nichts doppelt kaufen oder suchen.
    *   **Akzeptanzkriterien:**
        *   Änderungen werden bei Internetverbindung sofort synchronisiert.
        *   UI aktualisiert sich ohne manuellen Refresh.

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

---

### Szenario 7: Die Familienkonferenz (Regeln & Setup)
> "Wir sitzen zusammen und besprechen, wie wir uns ernähren wollen. Wir definieren harte Grenzen: Maximal 2x Fleisch pro Woche. Das sind Ausschlusskriterien für den Plan. Dann definieren wir unsere Wünsche: Wir wollen Rezepte bevorzugen, die wir lange nicht gegessen haben und die allen gut schmecken. Das sind Sortier-Regeln. Falls eine harte Regel wie 'Max 30 min Zeit' dazu führt, dass gar kein Rezept gefunden wird, soll das System nicht aufgeben, sondern stattdessen einfach 'kurze Rezepte bevorzugen' (Sortierung) nutzen, damit wir wenigstens einen Vorschlag bekommen."

**Abgeleitete User Stories:**

*   **US-701 (Harte Regeln / Ausschluss) [MVP]:** Als *Feierabend-Planer* möchte ich "Harte Regeln" definieren (z.B. "Max 2x Fleisch", "Kein Schwein"), die Rezepte strikt aus dem Planungs-Pool ausschließen, wenn das Limit erreicht ist.
    *   **Akzeptanzkriterien:**
        *   Definition von Limits (Count, Frequency) für Tags.
        *   Rezepte, die das Limit verletzen, werden nicht vorgeschlagen.

*   **US-702 (Sortier-Regeln / Präferenzen) [MVP]:** Als *Feierabend-Planer* möchte ich "Weiche Regeln" definieren (z.B. "Bevorzuge hohe Bewertung", "Lange nicht gekocht"), die die Reihenfolge der Vorschläge beeinflussen, ohne Kandidaten komplett zu entfernen.
    *   **Akzeptanzkriterien:**
        *   Gewichtung von Faktoren (Historie, Bewertung, Dauer).
        *   Ergebnisliste wird basierend auf Score sortiert.

*   **US-703 (Fallback-Strategien) [V2]:** Als *Feierabend-Planer* möchte ich für harte Regeln einen Fallback definieren (z.B. "Wenn < 30min nichts findet, dann sortiere nach Dauer aufsteigend"), damit der Generator auch bei strengen Filtern Ergebnisse liefert.
    *   **Akzeptanzkriterien:**
        *   Verknüpfung einer *Harten Regel* mit einer *Sortier-Regel* als *Fallback-Strategie*.
        *   Hinweis an den Nutzer, wenn Fallback angewendet wurde.

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