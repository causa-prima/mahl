# Guideline für Frontend UX / Interaction Design

<!--
wann-lesen: Bei jeder neuen oder geänderten React-Komponente — beim Schreiben und im Self-Review.
Scope: Interaction Design (Sichtbarkeit, Feedback, Terminologie, Fehlerzustände).
Visuelle Konsistenz (Spacing, Hierarchie, Farbe) wird in einer eigenen Guideline beschrieben,
sobald mehr als ~3 Komponenten dieselben visuellen Entscheidungen treffen müssen.
-->

## Inhalt

| Prinzip | Wann relevant |
|---|---|
| 1. Principle of Least Surprise | Bei jedem Button, Link, Formular, Navigation |
| 2. Don't Make Me Think | Bei Labels, Aktionsbeschriftungen, Strukturentscheidungen |
| 3. Sichtbares Feedback | Bei jeder Aktion, die etwas verändert |
| 4. Fehlermeldungen als Hilfe | Bei jeder Validierung oder Fehlerbehandlung |
| 5. Destructive Actions schützen | Bei Löschen, Archivieren, Überschreiben |
| 6. Konsistente Terminologie | Bei allen sichtbaren Texten (Labels, Buttons, Meldungen) |
| 7. Leerer Zustand erklärt sich | Bei jeder Liste, Tabelle oder Ansicht, die leer sein kann |

> **Voraussetzung:** Diese Guideline gilt für alle React-Komponenten.
> `docs/CODING_GUIDELINE_TYPESCRIPT.md` beschreibt die technische Umsetzung.

---

## 1. Principle of Least Surprise

**Warum:** Nutzer bauen mentale Modelle auf. Jede Überraschung erzeugt Unsicherheit und Vertrauensverlust.

**Entscheidungsregel:** Tut eine Aktion genau das, was Label, Position und Kontext erwarten lassen?
- Ja → kein Handlungsbedarf.
- Nein → Label oder Verhalten anpassen, bis beides übereinstimmt.

✅ "Speichern" speichert. "Abbrechen" verwirft. "Löschen" löscht.
❌ "Speichern" speichert und navigiert überraschend auf eine andere Seite ohne Ankündigung.

**Reihenfolge:** Aktionen in der Reihenfolge anordnen, die der mentalen Abfolge des Nutzers entspricht (primäre Aktion zuerst, destruktive Aktion am Ende).

---

## 2. Don't Make Me Think

**Warum:** Jede Erklärung, die die UI selbst liefern müsste, kostet den Nutzer kognitive Energie.

**Entscheidungsregel:** Braucht ein Nutzer einen Tooltip, eine Legende oder eine Erklärung, um ein UI-Element zu verstehen?
- Nein → gut.
- Ja → Label oder Struktur überarbeiten, bis der Tooltip überflüssig ist.

✅ Button "Zutat hinzufügen" braucht keine Erklärung.
❌ Button "+" braucht einen Tooltip "Neue Zutat anlegen" → Label direkt ändern.

**Ausnahme:** Tooltips für sekundäre Informationen, die das Layout sprengen würden (z.B. Erklärung eines Fachbegriffs), sind erlaubt — nie als Ersatz für ein klares primäres Label.

---

## 3. Sichtbares Feedback

**Warum:** Ohne Feedback wissen Nutzer nicht, ob ihre Aktion ankam.

**Entscheidungsregel:**
1. Hat die Aktion einen direkten, sichtbaren UI-Zustandswechsel (Checkbox hakt, Item verschwindet, Wert ändert sich)?
   → Kein zusätzliches Feedback nötig. Der Zustandswechsel ist das Feedback.
2. Gibt es keinen direkten UI-Zustandswechsel?
   → Toast oder Inline-Feedback ist Pflicht.

✅ Checkbox "Immer vorrätig" → hakt sofort → kein Toast nötig.
✅ Formular bleibt nach "Speichern" offen → Toast "Gespeichert" Pflicht.
❌ "Speichern" → nichts ändert sich sichtbar → kein Feedback → Nutzer klickt mehrfach.

**Ladezeiten:** Jede Aktion, die auf eine Server-Antwort wartet, zeigt einen Ladezustand (Spinner, deaktivierter Button o.ä.) — nie eine eingefrorene UI ohne Reaktion.

---

## 4. Fehlermeldungen als Hilfe

**Warum:** Eine Fehlermeldung, die nicht erklärt was falsch ist und wie man es beheben kann, ist keine Hilfe.

**Entscheidungsregel:** Kann der Nutzer aus der Fehlermeldung direkt ableiten, was er ändern muss?
- Ja → gut.
- Nein → Meldung konkretisieren.

Format: "[Was ist falsch]." oder "[Was ist falsch] ([Constraint])."

✅ "Name darf nicht leer sein."
✅ "Name ist zu lang (maximal 200 Zeichen)."
❌ "Ungültige Eingabe."
❌ "Fehler beim Speichern." (ohne Ursache oder Handlungsaufforderung)

**Platzierung:** Fehlermeldungen erscheinen so nah wie möglich am betroffenen Element — nicht ausschließlich als Toast, wenn ein Formularfeld betroffen ist.

---

## 5. Destructive Actions schützen

**Warum:** Irreversible Aktionen erzeugen Angst. Rückgängig-machen schafft Vertrauen.

**Entscheidungsregel (gestuft):**

| Stufe | Situation | Verhalten |
|---|---|---|
| 1 | Soft-Delete machbar | Soft-Delete + Wiederherstellungsmöglichkeit im UI. Undo-Toast zusätzlich, wenn kein offensichtlicher Restore-Weg im normalen UI existiert. |
| 2 | Soft-Delete zu komplex | Bestätigungsdialog ("Wirklich löschen?"). Kein Undo. |
| 3 | Irreversibel + schwerwiegend | Explizite Bestätigung (z.B. Name eintippen). Nur für außergewöhnliche Fälle — aktuell in Mahl nicht vorgesehen. |

Stufe 1 hat immer Vorrang vor Stufe 2.

✅ Zutat löschen → wird als gelöscht markiert → im UI wiederherstellbar → kein Datenverlust.
❌ Zutat löschen → sofort unwiederbringlich weg → Nutzer muss neu anlegen.

---

## 6. Konsistente Terminologie

**Warum:** Synonyme erzeugen Unsicherheit. Nutzer fragen sich: "Ist das dasselbe?"

**Entscheidungsregel:** Verwende für jedes Konzept ausschließlich den Terminus aus `docs/GLOSSARY.md`. Keine Synonyme — auch nicht in Labels, Buttons, Fehlermeldungen oder leeren Zuständen.

✅ "Zutat" durchgehend in Labels, Buttons, Fehlermeldungen, leeren Zuständen.
❌ "Zutat" im Button, "Ingredient" im Fehler, "Produkt" im leeren Zustand.

**Neues UI-Konzept ohne Glossar-Eintrag:** Erst Glossar-Eintrag ergänzen, dann im UI verwenden.

---

## 7. Leerer Zustand erklärt sich

**Warum:** Eine leere Liste ohne Kontext lässt Nutzer im Unklaren — ist das ein Fehler oder gewollt?

**Entscheidungsregel:** Jede Liste oder Ansicht, die leer sein kann, zeigt:
1. Warum sie leer ist ("Noch keine Zutaten angelegt.")
2. Was der Nutzer als nächstes tun kann (primäre Aktion oder Hinweis).

✅ "Noch keine Zutaten angelegt." + Button "Zutat hinzufügen"
❌ Leere Liste ohne Text.
❌ "Keine Daten vorhanden." (erklärt nicht warum und was zu tun ist)

**Gefilterter vs. echter leerer Zustand:** Ist die Liste durch einen aktiven Filter leer, erklärt der leere Zustand den Filter und wie man ihn aufhebt — nicht "Noch nichts angelegt".
