# Szenario 6 – Das neue Lieblingsrezept (Erfassung & Pflege)

> Teil von [docs/stories/user-stories.md](../docs/stories/user-stories.md).

## Inhalt

- Szenario-Narrativ (Import, manuelle Erfassung, Sub-Rezepte, Pflege)
- US-601 (Rezept-Import) [V2]
- US-602 (Manuelle Erfassung & Anhänge) [SKELETON]
- US-603 (Sub-Rezepte) [V2]
- US-604 (Zutaten-Mapping) [V2]
- US-605 (Schritte anlegen) [MVP]
- US-606 (Erweiterter Schritt-Editor) [PARKING]
- US-607 (Zutaten-Zuordnung) [MVP]
- US-608 (Auto-Tagging) [PARKING]
- US-609 (Manuelles Tagging) [MVP]
- US-610 (Gesamtzeit) [MVP]
- US-611 (Detaillierte Zeit-Erfassung) [V2]
- US-612 (Rezept-Notizen & Varianten) [V1]
- US-613 (Validierung) [V2]
- US-614 (Rezept-Korrektur) [MVP]
- US-615 (Änderungshistorie) [V2]
- US-616 (Rezept-Löschen) [V1]
- US-617 (Schritt-Typisierung) [V2]
- US-618 (Schritt-Abschnitte) [V1]
- US-619 (Alternative Zutaten) [V1]
- US-620 (Optionale Zutaten) [PARKING]
- US-621 (Rezept zum Ausprobieren) [V1]
- US-622 (Agenten-Schnittstelle) [V1]

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
    *   **Akzeptanzkriterien (SKELETON):**
        *   Formular für neues Rezept als eigene Seite: Titel; Zutaten als Freitext in einem mehrzeiligen Feld, eine Zutat je Zeile in der Form „Menge Einheit Zutat" („250 g Mehl") oder nur „Zutat" („Salz") – die Zutat muss im Bestand existieren, die Einheit ist ihre Basiseinheit; Schritte als geordnete Liste, ein Feld je Schritt mit sichtbarer Nummer.
        *   Zerlegt wird beim Speichern auf dem Server; jede Meldung zu einer Zutatenzeile nennt die Zeile. Brüche, Plural, Mengen ohne Einheit, Modifizierer und die formatierte Anzeige je Zeile im Formular folgen in US-607 (MVP).
        *   Pflicht: Titel, mindestens eine Zutat, mindestens ein Schritt. Titel eindeutig (Leerraum zusammengefasst und getrimmt, ohne Unterschied der Groß-/Kleinschreibung); jede Zutat höchstens einmal je Rezept.
        *   Detailansicht zeigt die Schritte nummeriert und voneinander abgesetzt – sie dient bis zum Kochmodus (US-508, V1) auch zum Kochen, am Tablet oder Handy.
        *   Rezept-Liste und Detailansicht; Rezepte sind per Link direkt aufrufbar.
    *   **Akzeptanzkriterien (MVP – Bild-Upload, Basis-Portion, Löschsperre, Titel-Hinweis):**
        *   Upload/Kamera-Funktion für Bilder.
        *   Hochgeladenes Bild wird als Rezept-Quelle gesetzt.
        *   Das Rezept trägt eine *Basis-Portion* als Menge plus Einheit (z.B. „2 Personen", „12 Stück", „1 Blech"); keine Spannen wie „2-3 Personen". Sie ist der Ausgangswert der *Planungs-Portion* (US-803, US-101) und der Skalierung (US-511).
        *   Eine Zutat, die in einem Rezept verwendet wird, lässt sich nicht löschen.
        *   Existiert der Titel bereits, weist das Formular schon beim Verlassen des Titelfelds darauf hin – nicht erst beim Speichern.

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

*   **US-606 (Erweiterter Schritt-Editor) [PARKING]:** Als *Rezept-Sammler* möchte ich Schritte komfortabel verwalten (Sortieren, Splitten, Zusammenführen), um Texte schnell zu strukturieren (z. B. beim Import).
    *   **Akzeptanzkriterien:**
        *   Textfeld kann an Cursor-Position gesplittet werden.
        *   Schritte können zusammengeführt werden.
        *   Reihenfolge der Schritte änderbar.

*   **US-607 (Zutaten-Zuordnung) [MVP]:** Als *Rezept-Sammler* möchte ich pro Schritt Zutaten (Menge + Einheit + Zutat) direkt eingeben, damit die Rezept-Zutatenliste automatisch als Aggregat aller Schritt-Zutaten entsteht.
    *   **Akzeptanzkriterien (MVP – manuelle Erfassung):**
        *   Pro Schritt können Zutaten (Menge, Einheit, Zutat) direkt hinzugefügt, bearbeitet und entfernt werden.
        *   Die Zutatenliste in der Rezept-Detailansicht ist ein Aggregat aller Schritt-Zutaten.
        *   Jede Zutat muss mindestens einem Schritt zugeordnet sein (Speichern ohne Schritt-Zutaten ist nicht möglich).
        *   Dieselbe Zutat darf in mehreren Schritten vorkommen (z.B. Butter für Teig und Streusel); die Rezept-Zutatenliste summiert sie.
        *   Fehlt eine Zutat im Bestand, lässt sie sich direkt aus dem Rezept anlegen (über den bestehenden Zutaten-Dialog), ohne das Rezept zu verlassen.
    *   **Akzeptanzkriterien (MVP – Zutatenzeile):** Die Freitext-Zeile aus US-602 (SKELETON: nur „Menge Einheit Zutat" mit Dezimalzahl) wird komfortabel:
        *   Jede Zeile wird beim Bestätigen zerlegt und als formatierter Eintrag angezeigt (Menge und Einheit hervorgehoben, Zutat daneben, Modifizierer darunter); „x" entfernt den Eintrag, der Stift holt ihn zurück ins Textfeld.
        *   Brüche wie „1/2", „½", „1 1/2" werden verstanden und als „½", „1½" angezeigt. Drittel sind dabei zu beachten: gespeichert wird mit drei Nachkommastellen (⅓ → 0,333), skaliert darf trotzdem kein „0,999" erscheinen.
        *   Plural und einheitenlose Stückzahl („5 Äpfel", „1 Apfel").
        *   *Zutaten-Modifizierer* hinter Komma oder in Klammern („Butter, weich", „Tomaten (stückig)") – Produkt-Modifizierer und Zubereitungshinweis nach US-904 (MVP).
        *   Unscharfe und mehrdeutige Zuordnung: offene Frage in `docs/open-questions.md` (Zutatenzeile zerlegen).
    *   **Akzeptanzkriterien (V2 – Import-Workflow):**
        *   Nach URL-Import (US-601) wird die extrahierte Zutatenliste neben den Schritten angezeigt.
        *   Drag & Drop oder alternative mobilfreundliche Interaktion verknüpft importierte Zutat mit einem Schritt.

*   **US-608 (Auto-Tagging) [PARKING]:** Als *Rezept-Sammler* möchte ich, dass Tags wie "Vegetarisch" automatisch anhand der Zutaten-Tags erkannt werden, um Pflegeaufwand zu sparen.
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
        *   Bearbeitet wird direkt in der Detailansicht, bereichsweise (z.B. ein Schritt, eine Menge) – ohne Wechsel auf eine eigene Bearbeiten-Seite. Anlass: Korrekturen fallen oft beim oder nach dem Kochen auf und sollen dann reibungslos gehen.
        *   Jeder bearbeitbare Bereich zeigt sichtbar, dass er bearbeitbar ist (z.B. Bearbeiten-Symbol); langer Druck ist höchstens eine zusätzliche Abkürzung, nie der einzige Weg.

*   **US-615 (Änderungshistorie) [V2]:** Als *Rezept-Sammler* möchte ich sehen, wer wann was am Rezept geändert hat, um im Zweifel alte Stände wiederherstellen zu können.
    *   **Akzeptanzkriterien:**
        *   Liste der Änderungen (Datum, Nutzer, Feld) einsehbar.
        *   (Optional) Wiederherstellen alter Versionen.

*   **US-616 (Rezept-Löschen) [V1]:** Als *Rezept-Sammler* möchte ich Rezepte archivieren können, wenn sie doppelt sind oder nicht geschmeckt haben, um meine Sammlung sauber zu halten.
    *   **Akzeptanzkriterien:**
        *   Archivieren-Funktion mit Sicherheitsabfrage.
        *   Archivierte Rezepte sind in der normalen Ansicht ausgeblendet.
        *   Filter "Archivierte anzeigen" in der Rezept-Liste macht archivierte Rezepte sichtbar und ermöglicht Wiederherstellung.
        *   Nur aktive Rezepte verhindern das Löschen ihrer Zutaten; archivierte nicht. Im Workshop zu klären: wie die Wiederherstellung mit einer inzwischen gelöschten Zutat umgeht.
        *   Dedizierter Admin-Bereich listet alle archivierten Rezepte.
        *   Wiederherstellung und endgültiges Löschen aus dem Admin-Bereich möglich.

*   **US-617 (Schritt-Typisierung) [V2]:** Als *Rezept-Sammler* möchte ich Schritten eine Aktivitätsart (Vorbereitung, Kochen, Backen, Ruhen) zuweisen, um die Zeiten genauer zu kalkulieren und das Tracking (siehe US-517) zu ermöglichen.
    *   **Akzeptanzkriterien:**
        *   Auswahlfeld "Aktivitäts-Typ" pro Schritt im Editor.
        *   Standard-Typ ist "Vorbereitung" oder "Kochen".

*   **US-618 (Schritt-Abschnitte) [V1]:** Als *Rezept-Sammler* möchte ich Schritte zu benannten Abschnitten gruppieren (z.B. „Teig", „Füllung", „Dressing"), damit mehrteilige Rezepte übersichtlich bleiben.
    *   **Akzeptanzkriterien:**
        *   Schritte lassen sich einem benannten Abschnitt zuordnen; Abschnitte sind optional.
        *   Die Zutatenliste der Detailansicht ist nach denselben Abschnitten gruppiert – sie entsteht aus den Zutaten der Schritte (US-607), die Gruppierung folgt daraus.
        *   Dieselbe Zutat darf in mehreren Abschnitten vorkommen (z.B. Butter in Teig und Streusel).
    *   **Anlass:** 21 von 114 Rezepten der bisherigen Sammlung gliedern ihre Zutaten in Abschnitte, überwiegend Backrezepte.

*   **US-619 (Alternative Zutaten) [V1]:** Als *Rezept-Sammler* möchte ich für eine Rezept-Zutat mehrere gleichwertige Zutaten angeben (z.B. „200 g Butter oder Margarine"), damit das Rezept zeigt, dass beide gehen.
    *   **Akzeptanzkriterien:**
        *   Eine Rezept-Zutat kann mehrere Zutaten als Alternativen tragen; Menge und Einheit gelten für alle gemeinsam.
        *   Die Anzeige nennt alle Alternativen („200 g Butter oder Margarine").
        *   Bewusst nicht vorgesehen: eine eigene Menge je Alternative (z.B. frische Hefe oder Trockenhefe) – eine der Varianten genügt; Umrechnungswissen zwischen Produkten gehört nicht in die Anwendung.
        *   Im Workshop zu klären: was die Einkaufsliste mit einer Alternative macht.

*   **US-620 (Optionale Zutaten) [PARKING]:** Als *Rezept-Sammler* möchte ich eine Rezept-Zutat als optional markieren (z.B. Garnitur, Topping), damit sie nicht ungefragt auf die Einkaufsliste kommt.
    *   **Akzeptanzkriterien:**
        *   Markierung „optional" je Rezept-Zutat; die Anzeige macht sie kenntlich.
        *   Bis dahin genügen die Rezept-Notizen (US-612).

*   **US-621 (Rezept zum Ausprobieren) [V1]:** Als *Feierabend-Planer* möchte ich ein neues Rezept erst ausprobieren, bevor es in die Sammlung kommt, und es dabei trotzdem einplanen und einkaufen können.
    *   **Anlässe:** Zutaten von der SoLaWi, für die es kein Rezept gibt; eine große Menge einer Zutat bei nur wenigen passenden Rezepten; mehr Rezepte für eine beliebte Zutat („zu wenig Gnocchi-Rezepte"); einfach mal etwas Neues.
    *   **Akzeptanzkriterien:**
        *   Ein Rezept kann als „zum Ausprobieren" angelegt werden; es lässt sich in den Pool legen, und seine Zutaten kommen auf die Einkaufsliste wie bei jedem anderen Rezept.
        *   In der Rezept-Liste ist es als solches erkennbar oder getrennt von der Sammlung.
        *   Nach dem Kochen: Entscheidung „in die Sammlung aufnehmen" oder „verwerfen".
    *   **Im Workshop zu klären:** Der Komfort steht und fällt mit dem Erfassen. Erwogen vom User: (1) nur ein Link im Plan, Einkaufsliste von Hand, im Kochmodus öffnet sich die Seite – trivial, aber die Zutaten müssen abgetippt werden; (2) das Rezept importieren (US-601, US-622) – am bequemsten, wenn der Import für die meisten Rezepte einfach funktioniert.

*   **US-622 (Agenten-Schnittstelle) [V1]:** Als *Rezept-Sammler* möchte ich Rezepte von einem (beliebigen, externen) Agenten importieren und bearbeiten lassen, damit auch unstrukturierte oder uneinheitliche Vorlagen ohne Abtippen in die Sammlung kommen.
    *   **Anlässe:** Vorlagen sind sehr unterschiedlich – ausführlich, knapp oder ungenau, mit eigenen Begriffen; ein Agent bringt sie in eine einheitliche Form und deckt Probleme beim Import auf. Viele Rezepte stecken mitten in langen Texten (Blogs), an denen ein Parser scheitert. Bestehende Rezepte soll ein Agent lesen („wie wurde das bisher erfasst?") und ändern können („Pass Rezept X an: 200 ml Milch statt 300 ml").
    *   **Akzeptanzkriterien:**
        *   Eine dokumentierte Schnittstelle bietet alles, was man auch selbst in der Anwendung tun kann – Rezepte und Zutaten lesen, anlegen, ändern, eine neue Zutat anlegen, eine Zutatenzeile zerlegen lassen.
        *   Der Zugriff von außen ist geschützt.
    *   **Im Workshop zu klären:** Form der Schnittstelle (dokumentierte HTTP-API, MCP-Server oder beides); Verhältnis zu US-601 (URL-Import über einen Parser, V2) – ein Agenten-Import könnte ihn ersetzen; ob Änderungen des Agenten vor dem Speichern bestätigt werden.
