# Szenario 0 – Der App-Start (Kontext)

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (App-Start auf Handy/Tablet)
- US-001 (Geräte-Kontext) [PARKING]

---

### Szenario 0: Der App-Start (Kontext)
> "Ich nehme mein Handy in die Hand, um einzukaufen. Die App öffnet direkt die Einkaufsliste. Später am Abend nehme ich das Tablet in der Küche. Die App öffnet direkt den Kochmodus für das heutige Rezept."

**Abgeleitete User Stories:**

*   **US-001 (Geräte-Kontext) [PARKING]:** Als *Nutzer* möchte ich eine Standardansicht definieren, damit ich sofort im richtigen Kontext bin (Handy -> Einkauf, Tablet -> Kochen).
    *   **Akzeptanzkriterien:**
        *   Einstellung "Standard-Startseite" in den Nutzereinstellungen pro Gerät speicherbar.
        *   Beim App-Start wird die konfigurierte Ansicht geladen.
    *   **Parking-Hinweis:** Als einfacherer erster Schritt kann der Default-Wert hardcodiert werden (Smartphone → Einkaufsliste, Tablet → Pool), bevor die konfigurierbare Variante implementiert wird.
