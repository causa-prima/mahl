# Szenario 2 – Der Vorrats-Check (Freitagmorgen)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Pantry-Check, Mengen-Anpassung, Fix-Einträge)
- US-201 (Pantry-Check) [SKELETON]
- US-202 (Mengen-Anpassung) [MVP]
- US-203 (Fix-Eintrag) [V1]

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
