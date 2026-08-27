# Glossar & Fachliches Domänenmodell

<!--
wann-lesen: Bei jedem Benennen von Typen, Variablen, Methoden oder Endpoints – Begriffe aus diesem Glossar sind im Code bindend
kritische-regeln:
  - Nur die hier definierten deutschen/englischen Begriffe verwenden (Ubiquitous Language)
  - Synonyme (z.B. "Möhre" statt "Karotte") sind kein gültiger Code-Name
-->

<a id="GLO-inhalt"></a>
## Inhalt

| Abschnitt | Domäne | Enthaltene Begriffe |
|-----------|--------|---------------------|
| [Zutaten & Einheiten](#GLO-zutaten-einheiten) | Stammdaten | Zutat, Zutaten-Modifizierer, Zutaten-Alias, Basiseinheit, Umrechnungsfaktor, Non-Food-Item |
| [Rezepte](#GLO-domaene-rezepte) | Rezeptverwaltung | Rezept, Rezept-Variante, Zubereitungszeit, Rezept-Zutat, Sub-Rezept, Schritt, Basis-Portion, Planungs-Portion, Import-Pool, Koch-Historie, Kochmodus |
| [Planung](#GLO-domaene-planung) | Wochenplanung | Planungs-Pool, Wochen-Pool, Wochenplan, Plan-Eintrag, Harte Regel, Sortier-Regel, Fallback-Strategie, Esser-Profil, Slot, Globale/Tages-/Session-Regel |
| [Einkauf](#GLO-domaene-einkauf) | Einkaufsliste | Einkaufsliste, Einkaufslisten-Eintrag, Delta-Menge, Fix-Eintrag, Shop-Kategorie |
| [Klassifizierung](#GLO-domaene-klassifizierung) | Taxonomie | Tag (DAG-Struktur) |

Dieses Dokument definiert die **Ubiquitäre Sprache** (Ubiquitous Language) für das Projekt "Mahl". Diese Begriffe sind in allen Anforderungen, User Stories und im Code bindend zu verwenden.

**Sprach-Konvention:** In Dokumentation und User Stories: Deutsch. In Code-Identifiern (Klassen, DTOs, Endpoints, Variablen): Englisch. Format der Einträge: `Deutscher Begriff (EnglishIdentifier)` – der englische Term ist der Code-Name.

<a id="GLO-zutaten-einheiten"></a>
## Kern-Domäne: Zutaten & Einheiten

<a id="GLO-zutat"></a>
### Zutat (Ingredient)
Die abstrakte Stammdaten-Repräsentation eines Lebensmittels.
*   **Eigenschaften:** Eindeutiger *Hauptname*, definierte *Basiseinheit*, Liste von *Tags*, Liste erlaubter *Modifizierer*.
*   **Flag "Immer vorrätig":** Markierung für Artikel, die standardmäßig nicht auf die *Einkaufsliste* kommen (z.B. Salz, Öl), es sei denn, sie werden explizit gefordert.
*   **Beispiel:** "Weizenmehl Type 405".

<a id="GLO-zutaten-modifizierer"></a>
### Zutaten-Modifizierer (Ingredient Modifier)
Eine Eigenschaft, die den Zustand oder die Verarbeitungsform einer *Zutat* konkretisiert.
*   **Zweck:** Ermöglicht die Unterscheidung von Varianten ohne separate Stammdaten-Einträge.
*   **Beispiel:** Zutat "Tomaten (Dose)" -> Modifizierer: "stückig", "passiert", "ganz".

<a id="GLO-zutaten-alias"></a>
### Zutaten-Alias (Ingredient Alias)
Ein alternativer Suchbegriff, der auf genau eine *Zutat* verweist.
*   **Zweck:** Mapping beim Import und Fehlertoleranz bei der Suche.
*   **Beispiel:** "Karotte", "Möhre" -> mappen beide auf Zutat "Karotte".

<a id="GLO-basiseinheit"></a>
### Basiseinheit (Base Unit)
Die kanonische Einheit, in der eine *Zutat* systemintern gespeichert und auf der *Einkaufsliste* aggregiert wird.
*   **Regel:** Alle *Rezept-Zutaten* müssen in diese Einheit umrechenbar sein.
*   **UI-Label:** Im Nutzer-Interface heißt das Feld „Einheit“ (nicht „Basiseinheit“). Solange es im UI keine Einheiten-Umrechnung gibt (SKELETON/MVP), hat „Basis-“ keinen Kontrast und verwirrt eher; „Einheit“ ist für Rezept-Sammler der erwartbare Alltagsbegriff. Bei Einführung der Umrechnung (V1, *Umrechnungsfaktor*) erneut prüfen, ob „Basiseinheit“ zur Abgrenzung nötig wird.

<a id="GLO-umrechnungsfaktor"></a>
### Umrechnungsfaktor (Conversion Factor)
Definiert das Verhältnis einer beliebigen *Einheit* zur *Basiseinheit*.
*   **Typen:**
    *   *Global:* Gilt für alle Zutaten (z.B. 1 kg = 1000 g).
    *   *Zutatenspezifisch:* Gilt nur für eine Zutat (z.B. "1 EL Mehl" = 12g).

<a id="GLO-non-food-item"></a>
### Non-Food-Item
Ein Artikel, der keine *Zutat* ist (z.B. "Toilettenpapier"), aber auf der *Einkaufsliste* stehen kann.
*   **Verwaltung:** Werden in einer separaten Liste für Autocomplete-Vorschläge gespeichert.

---

<a id="GLO-domaene-rezepte"></a>
## Domäne: Rezepte

<a id="GLO-rezept"></a>
### Rezept (Recipe)
Eine persistierte Anleitung zur Zubereitung eines Gerichts.
*   **Bestandteile:** Metadaten (Titel, Bild, Quelle), Liste von *Rezept-Zutaten*, Liste von *Schritten*, *Basis-Portion*, *Tags*, *Notizen* (für Varianten), *Zubereitungszeiten*.

<a id="GLO-rezept-variante"></a>
### Rezept-Variante (Recipe Variant)
Eine explizite Abwandlung eines *Rezepts* (z.B. "Vegetarisch" vs. "Mit Fleisch").
*   **Implementierung:** Freitext-Notiz oder strukturierte Abweichung von Zutaten/Schritten.

<a id="GLO-zubereitungszeit"></a>
### Zubereitungszeit (Preparation Time)
Die zeitliche Aufwandsabschätzung für ein *Rezept*.
*   **Komponenten:** Vorbereitungszeit, Kochzeit, Backzeit, Ruhezeit.
*   **Gesamtzeit:** Summe aller Komponenten.

<a id="GLO-quantity"></a>
### Quantity (Menge)
Eine Mengenangabe, bestehend aus einer positiven Zahl und einer Einheit – oder keine Angabe.
*   **Varianten:** `Specified(value: decimal > 0, unit: NonEmptyTrimmedString)` | `Unspecified`
*   **Verwendung:** Rezept-Zutaten, Einkaufslisten-Einträge, Basis-Portion.
*   **Code-Typ:** `Quantity` (Sum-Type im Domain-Layer)

<a id="GLO-rezept-zutat"></a>
### Rezept-Zutat (Recipe Ingredient)
Die Verwendung einer *Zutat* in einem spezifischen *Rezept*.
*   **Datenstruktur:** Referenz auf *Zutat* (oder *Sub-Rezept*), *Quantity*, gewählter *Modifizierer* (optional).
*   **Beispiel:** "500g" (*Quantity*) "Tomaten" (Zutat) "stückig" (Modifizierer).

<a id="GLO-sub-rezept"></a>
### Sub-Rezept (Sub-Recipe)
Ein *Rezept*, das in einem anderen Rezept als *Rezept-Zutat* referenziert wird.
*   **Auflösung:** Wird auf der *Einkaufsliste* rekursiv in seine elementaren *Zutaten* zerlegt, skaliert auf die benötigte Menge.

<a id="GLO-schritt"></a>
### Schritt (Step)
Ein atomarer Teil der Zubereitungsanleitung.
*   **Verknüpfung:** Kann mit einer Teilmenge der *Rezept-Zutaten* verknüpft sein (für "Kochmodus").

<a id="GLO-basis-portion"></a>
### Basis-Portion (Base Portion)
Die Referenzmenge, für die das *Rezept* ursprünglich erstellt wurde.
*   **Format:** Menge + Einheit (z.B. "4 Personen", "12 Stück", "1 Blech").

<a id="GLO-planungs-portion"></a>
### Planungs-Portion (Planning Portion)
Die absolute Zielmenge, für die ein Rezept an einem bestimmten Tag gekocht wird.
*   **Verwendung:** Basis für die Skalierung der Zutaten auf der *Einkaufsliste*.
*   **Beispiel:** Rezept ist für "4 Personen" (Basis), gekocht wird aber für "6 Personen" (Planung).

<a id="GLO-import-pool"></a>
### Import-Pool (Import Pool)
Ein temporärer Arbeitsbereich für neu importierte Rezepte, deren *Zutaten* noch nicht vollständig auf *Stammdaten-Zutaten* gemappt sind.

<a id="GLO-koch-historie"></a>
### Koch-Historie (Cooking History)
Ein unveränderliches Protokoll aller gekochten Gerichte.
*   **Eintrag:** Datum, *Rezept*, *Planungs-Portion*.
*   **Zweck:** Auswertungen ("Wann zuletzt gekocht?"), Statistik.

<a id="GLO-kochmodus"></a>
### Kochmodus (Cooking Mode)
Eine dedizierte Ansicht zur schrittweisen Führung durch die Zubereitung.
*   **Funktion:** Zeigt *Schritte* einzeln an, filtert *Rezept-Zutaten* pro Schritt, verhindert Standby des Geräts.

---

<a id="GLO-domaene-planung"></a>
## Domäne: Planung

<a id="GLO-planungs-pool"></a>
### Planungs-Pool (Planning Pool)
Ein isolierter, temporärer Arbeitsbereich während des Planungs-Wizards.
*   **Zweck:** Ermöglicht Simulation und Anpassung eines Plans, ohne den aktiven *Wochen-Pool* zu beeinflussen.
*   **Transition:** Wird bei Abschluss ("Commit") in den *Wochen-Pool* überführt.

<a id="GLO-wochen-pool"></a>
### Wochen-Pool (Weekly Pool)
Die Menge aller *Rezepte*, die für den aktuellen Planungszeitraum verbindlich ausgewählt wurden.
*   **Zustand:** Rezepte warten hier auf Zuweisung zu einem Tag oder auf "Sofort Kochen".

<a id="GLO-wochenplan"></a>
### Wochenplan (Weekly Plan)
Die konkrete kalendarische Zuordnung von *Rezepten* aus dem *Wochen-Pool* zu Wochentagen.

<a id="GLO-plan-eintrag"></a>
### Plan-Eintrag (Plan Entry)
Die konkrete Zuweisung eines *Rezepts* zu einem *Slot* im *Wochenplan*.
*   **Eigenschaften:** Datum, Slot-Typ, *Planungs-Portion*.

<a id="GLO-harte-regel"></a>
### Harte Regel (Hard Constraint)
Ein Ausschlusskriterium für die Plan-Generierung.
*   **Effekt:** Rezepte, die diese Regel verletzen, werden strikt ignoriert.
*   **Beispiel:** "Max. 2x Fleisch pro Woche", "Kein Schwein".

<a id="GLO-sortier-regel"></a>
### Sortier-Regel (Soft Constraint / Preference)
Ein Kriterium zur Priorisierung von gültigen Kandidaten.
*   **Effekt:** Beeinflusst die Reihenfolge der Vorschläge (Score), schließt aber nichts aus.
*   **Beispiel:** "Bevorzuge hohe Bewertung", "Lange nicht gekocht".

<a id="GLO-fallback-strategie"></a>
### Fallback-Strategie (Fallback Strategy)
Eine definierte *Sortier-Regel*, die angewendet wird, wenn eine *Harte Regel* zu einer leeren Ergebnismenge führt (oder als Alternative definiert ist).

<a id="GLO-esser-profil"></a>
### Esser-Profil (Eater Profile)
Ein virtueller Benutzer zur Erfassung von Geschmacksvorlieben.
*   **Daten:** Name, Bewertungen (Sterne) pro Rezept, Ausschlusskriterien (Tags).

<a id="GLO-slot"></a>
### Slot (Time Slot)
Ein definierter Zeitpunkt für eine Mahlzeit (z.B. "Montag Abend").

<a id="GLO-globale-regel"></a>
### Globale Regel (Global Rule)
Eine Regel, die standardmäßig für jede Planung gilt (z.B. "Vegetarisch"). Sie ist in den Nutzereinstellungen hinterlegt.

<a id="GLO-tagesregel"></a>
### Tagesregel (Day Rule)
Eine Regel, die an einen spezifischen Wochentag oder ein Datum gebunden ist (z.B. "Dienstags max. 30 min", "jeden ersten Sonntag im Monat Pfannkuchen").

<a id="GLO-session-regel"></a>
### Session-Regel (Session Rule)
Eine temporäre Regel, die nur für den aktuellen Lauf des Planungs-Wizards gilt (z.B. "Heute mal Ausnahme bei Fleisch").

---

<a id="GLO-domaene-einkauf"></a>
## Domäne: Einkauf

<a id="GLO-einkaufsliste"></a>
### Einkaufsliste (Shopping List)
Eine aggregierte Liste von *Einkaufslisten-Einträgen* für einen definierten Zeitraum.

<a id="GLO-einkaufslisten-eintrag"></a>
### Einkaufslisten-Eintrag (Shopping List Item)
Eine Position auf der Einkaufsliste.
*   **Typen:**
    *   *Zutat:* Referenziert eine *Zutat*. Menge ist die Summe aller Bedarfe aus dem *Wochenplan*.
    *   *Freitext:* Ein manueller Eintrag (siehe *Non-Food-Item*).
*   **Zustand:** Offen / Gekauft.

<a id="GLO-delta-menge"></a>
### Delta-Menge (Delta Quantity)
Eine manuelle Korrektur der Menge eines *Einkaufslisten-Eintrags*, die nicht aus dem Rezept resultiert (z.B. "Habe noch die Hälfte da").
*   **Berechnung:** Angezeigte Menge = (Rezept-Bedarf + Delta-Menge).

<a id="GLO-fix-eintrag"></a>
### Fix-Eintrag (Pinned Item)
Ein *Einkaufslisten-Eintrag*, der als "permanent" markiert ist.
*   **Verhalten:** Erscheint nach dem "Kaufen" beim nächsten Einkaufs-Zyklus (Reset) automatisch wieder als "Offen".

<a id="GLO-shop-kategorie"></a>
### Shop-Kategorie (Shop Category)
Eine logische Gruppierung zur Sortierung der *Einkaufsliste* (entspricht dem Laufweg im Laden).
*   **Mapping:** *Tags* werden auf *Shop-Kategorien* abgebildet (z.B. Tag "Apfel" -> Kategorie "Obst & Gemüse").

---

<a id="GLO-domaene-klassifizierung"></a>
## Domäne: Klassifizierung

<a id="GLO-tag"></a>
### Tag
Ein hierarchisches Schlagwort.
*   **Struktur:** Gerichteter azyklischer Graph (DAG). Ein Tag kann mehrere Eltern haben.
*   **Beispiel:** "Kartoffel" ist Kind von "Gemüse" UND "Sättigungsbeilage".