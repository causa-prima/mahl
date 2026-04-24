# Szenario 4 – Der Familien-Einkauf

> Teil von [USER_STORIES.md](../USER_STORIES.md).

## Inhalt

- Szenario-Narrativ (Undo, Live-Sync)
- US-401 (Undo-Funktion) [V1]
- US-402 (Live-Sync) [V2]

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
