# Szenario 7 – Die Familienkonferenz (Regeln & Setup)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Harte/Weiche Regeln, Fallback)
- US-701 (Harte Regeln / Ausschluss) [MVP]
- US-702 (Sortier-Regeln / Präferenzen) [MVP]
- US-703 (Fallback-Strategien) [V2]

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
