# Glossar & Fachliches Domänenmodell

Dieses Dokument definiert die **Ubiquitäre Sprache** (Ubiquitous Language) für das Projekt "Mahl". Diese Begriffe sind in allen Anforderungen, User Stories und im Code bindend zu verwenden.

## 1. Kern-Domäne: Zutaten & Einheiten

### Zutat (Ingredient)
Die abstrakte Stammdaten-Repräsentation eines Lebensmittels.
*   **Eigenschaften:** Eindeutiger *Hauptname*, definierte *Basiseinheit*, Liste von *Tags*, Liste erlaubter *Modifizierer*.
*   **Flag "Immer vorrätig":** Markierung für Artikel, die standardmäßig nicht auf die *Einkaufsliste* kommen (z.B. Salz, Öl), es sei denn, sie werden explizit gefordert.
*   **Beispiel:** "Weizenmehl Type 405".

### Zutaten-Modifizierer (Ingredient Modifier)
Eine Eigenschaft, die den Zustand oder die Verarbeitungsform einer *Zutat* konkretisiert.
*   **Zweck:** Ermöglicht die Unterscheidung von Varianten ohne separate Stammdaten-Einträge.
*   **Beispiel:** Zutat "Tomaten (Dose)" -> Modifizierer: "stückig", "passiert", "ganz".

### Zutaten-Alias (Ingredient Alias)
Ein alternativer Suchbegriff, der auf genau eine *Zutat* verweist.
*   **Zweck:** Mapping beim Import und Fehlertoleranz bei der Suche.
*   **Beispiel:** "Karotte", "Möhre" -> mappen beide auf Zutat "Karotte".

### Basiseinheit (Base Unit)
Die kanonische Einheit, in der eine *Zutat* systemintern gespeichert und auf der *Einkaufsliste* aggregiert wird.
*   **Regel:** Alle *Rezept-Zutaten* müssen in diese Einheit umrechenbar sein.

### Umrechnungsfaktor (Conversion Factor)
Definiert das Verhältnis einer beliebigen *Einheit* zur *Basiseinheit*.
*   **Typen:**
    *   *Global:* Gilt für alle Zutaten (z.B. 1 kg = 1000 g).
    *   *Zutatenspezifisch:* Gilt nur für eine Zutat (z.B. "1 EL Mehl" = 12g).

### Non-Food-Item
Ein Artikel, der keine *Zutat* ist (z.B. "Toilettenpapier"), aber auf der *Einkaufsliste* stehen kann.
*   **Verwaltung:** Werden in einer separaten Liste für Autocomplete-Vorschläge gespeichert.

---

## 2. Domäne: Rezepte

### Rezept (Recipe)
Eine persistierte Anleitung zur Zubereitung eines Gerichts.
*   **Bestandteile:** Metadaten (Titel, Bild, Quelle), Liste von *Rezept-Zutaten*, Liste von *Schritten*, *Basis-Portion*, *Tags*, *Notizen* (für Varianten), *Zubereitungszeiten*.

### Rezept-Variante (Recipe Variant)
Eine explizite Abwandlung eines *Rezepts* (z.B. "Vegetarisch" vs. "Mit Fleisch").
*   **Implementierung:** Freitext-Notiz oder strukturierte Abweichung von Zutaten/Schritten.

### Zubereitungszeit (Preparation Time)
Die zeitliche Aufwandsabschätzung für ein *Rezept*.
*   **Komponenten:** Vorbereitungszeit, Kochzeit, Backzeit, Ruhezeit.
*   **Gesamtzeit:** Summe aller Komponenten.

### Rezept-Zutat (Recipe Ingredient)
Die Verwendung einer *Zutat* in einem spezifischen *Rezept*.
*   **Datenstruktur:** Referenz auf *Zutat* (oder *Sub-Rezept*), Menge (Zahl), Einheit, gewählter *Modifizierer* (optional).
*   **Beispiel:** "500g" (Menge) "Tomaten" (Zutat) "stückig" (Modifizierer).

### Sub-Rezept (Sub-Recipe)
Ein *Rezept*, das in einem anderen Rezept als *Rezept-Zutat* referenziert wird.
*   **Auflösung:** Wird auf der *Einkaufsliste* rekursiv in seine elementaren *Zutaten* zerlegt, skaliert auf die benötigte Menge.

### Schritt (Step)
Ein atomarer Teil der Zubereitungsanleitung.
*   **Verknüpfung:** Kann mit einer Teilmenge der *Rezept-Zutaten* verknüpft sein (für "Kochmodus").

### Basis-Portion (Base Portion)
Die Referenzmenge, für die das *Rezept* ursprünglich erstellt wurde.
*   **Format:** Menge + Einheit (z.B. "4 Personen", "12 Stück", "1 Blech").

### Planungs-Portion (Planning Portion)
Die absolute Zielmenge, für die ein Rezept an einem bestimmten Tag gekocht wird.
*   **Verwendung:** Basis für die Skalierung der Zutaten auf der *Einkaufsliste*.
*   **Beispiel:** Rezept ist für "4 Personen" (Basis), gekocht wird aber für "6 Personen" (Planung).

### Import-Pool (Import Pool)
Ein temporärer Arbeitsbereich für neu importierte Rezepte, deren *Zutaten* noch nicht vollständig auf *Stammdaten-Zutaten* gemappt sind.

### Koch-Historie (Cooking History)
Ein unveränderliches Protokoll aller gekochten Gerichte.
*   **Eintrag:** Datum, *Rezept*, *Planungs-Portion*.
*   **Zweck:** Auswertungen ("Wann zuletzt gekocht?"), Statistik.

### Kochmodus (Cooking Mode)
Eine dedizierte Ansicht zur schrittweisen Führung durch die Zubereitung.
*   **Funktion:** Zeigt *Schritte* einzeln an, filtert *Rezept-Zutaten* pro Schritt, verhindert Standby des Geräts.

---

## 3. Domäne: Planung

### Planungs-Pool (Planning Pool)
Ein isolierter, temporärer Arbeitsbereich während des Planungs-Wizards.
*   **Zweck:** Ermöglicht Simulation und Anpassung eines Plans, ohne den aktiven *Wochen-Pool* zu beeinflussen.
*   **Transition:** Wird bei Abschluss ("Commit") in den *Wochen-Pool* überführt.

### Wochen-Pool (Weekly Pool)
Die Menge aller *Rezepte*, die für den aktuellen Planungszeitraum verbindlich ausgewählt wurden.
*   **Zustand:** Rezepte warten hier auf Zuweisung zu einem Tag oder auf "Sofort Kochen".

### Wochenplan (Weekly Plan)
Die konkrete kalendarische Zuordnung von *Rezepten* aus dem *Wochen-Pool* zu Wochentagen.

### Plan-Eintrag (Plan Entry)
Die konkrete Zuweisung eines *Rezepts* zu einem *Slot* im *Wochenplan*.
*   **Eigenschaften:** Datum, Slot-Typ, *Planungs-Portion*.

### Harte Regel (Hard Constraint)
Ein Ausschlusskriterium für die Plan-Generierung.
*   **Effekt:** Rezepte, die diese Regel verletzen, werden strikt ignoriert.
*   **Beispiel:** "Max. 2x Fleisch pro Woche", "Kein Schwein".

### Sortier-Regel (Soft Constraint / Preference)
Ein Kriterium zur Priorisierung von gültigen Kandidaten.
*   **Effekt:** Beeinflusst die Reihenfolge der Vorschläge (Score), schließt aber nichts aus.
*   **Beispiel:** "Bevorzuge hohe Bewertung", "Lange nicht gekocht".

### Fallback-Strategie (Fallback Strategy)
Eine definierte *Sortier-Regel*, die angewendet wird, wenn eine *Harte Regel* zu einer leeren Ergebnismenge führt (oder als Alternative definiert ist).

### Esser-Profil (Eater Profile)
Ein virtueller Benutzer zur Erfassung von Geschmacksvorlieben.
*   **Daten:** Name, Bewertungen (Sterne) pro Rezept, Ausschlusskriterien (Tags).

### Slot (Time Slot)
Ein definierter Zeitpunkt für eine Mahlzeit (z.B. "Montag Abend").

### Globale Regel (Global Rule)
Eine Regel, die standardmäßig für jede Planung gilt (z.B. "Vegetarisch"). Sie ist in den Nutzereinstellungen hinterlegt.

### Tagesregel (Day Rule)
Eine Regel, die an einen spezifischen Wochentag oder ein Datum gebunden ist (z.B. "Dienstags max. 30 min", "jeden ersten Sonntag im Monat Pfannkuchen").

### Session-Regel (Session Rule)
Eine temporäre Regel, die nur für den aktuellen Lauf des Planungs-Wizards gilt (z.B. "Heute mal Ausnahme bei Fleisch").

---

## 4. Domäne: Einkauf

### Einkaufsliste (Shopping List)
Eine aggregierte Liste von *Einkaufslisten-Einträgen* für einen definierten Zeitraum.

### Einkaufslisten-Eintrag (Shopping List Item)
Eine Position auf der Einkaufsliste.
*   **Typen:**
    *   *Zutat:* Referenziert eine *Zutat*. Menge ist die Summe aller Bedarfe aus dem *Wochenplan*.
    *   *Freitext:* Ein manueller Eintrag (siehe *Non-Food-Item*).
*   **Zustand:** Offen / Gekauft.

### Delta-Menge (Delta Quantity)
Eine manuelle Korrektur der Menge eines *Einkaufslisten-Eintrags*, die nicht aus dem Rezept resultiert (z.B. "Habe noch die Hälfte da").
*   **Berechnung:** Angezeigte Menge = (Rezept-Bedarf + Delta-Menge).

### Fix-Eintrag (Pinned Item)
Ein *Einkaufslisten-Eintrag*, der als "permanent" markiert ist.
*   **Verhalten:** Erscheint nach dem "Kaufen" beim nächsten Einkaufs-Zyklus (Reset) automatisch wieder als "Offen".

### Shop-Kategorie (Shop Category)
Eine logische Gruppierung zur Sortierung der *Einkaufsliste* (entspricht dem Laufweg im Laden).
*   **Mapping:** *Tags* werden auf *Shop-Kategorien* abgebildet (z.B. Tag "Apfel" -> Kategorie "Obst & Gemüse").

---

## 5. Domäne: Klassifizierung

### Tag
Ein hierarchisches Schlagwort.
*   **Struktur:** Gerichteter azyklischer Graph (DAG). Ein Tag kann mehrere Eltern haben.
*   **Beispiel:** "Kartoffel" ist Kind von "Gemüse" UND "Sättigungsbeilage".