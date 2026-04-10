# MVP-Spezifikation

> **Status:** Nicht gestartet
>
> **Voraussetzung:** SKELETON vollständig abgeschlossen
>
> **Wann lesen:** Beim Start der MVP-Phase.
>
> **Wichtig:** Alle DB-Schema-Details, API-Routen und Verhaltenserwartungen in dieser Datei sind **vorläufige Planungsgrundlagen**, keine fixierten Specs. Für jede User Story entstehen die verbindlichen Verhaltenserwartungen erst im `gherkin-workshop`. Impl.-Details emergieren aus Tests.

---

## Ziel

Alle Features, die nötig sind, um dem Nutzer echten Mehrwert zu bieten. Nach MVP ist die App im Alltag nutzbar.

---

## User Stories (MVP)

Details zu jeder Story: `docs/USER_STORIES.md`

| Story | Beschreibung | Bereich |
|-------|-------------|---------|
| US-103 | Muss-Rezepte (für bestimmte Tage pinnen) | Planung |
| US-105 | Automatische Vorschläge & Regeln | Planung |
| US-106 | Besuchs-Planung (Portionsanpassung pro Tag) | Planung |
| US-202 | Mengen-Anpassung auf Einkaufsliste (Delta-Logik) | Einkauf |
| US-301 | Intelligente Artikelerfassung (Live-Suche) | Einkauf |
| US-306 | Offline-Verfügbarkeit der Einkaufsliste | Einkauf |
| US-307 | Non-Food-Items (Freitext-Einträge) | Einkauf |
| US-501 | Pool-Liste als Dashboard | Kochen |
| US-505 | Zutaten-Übersicht vor dem Kochen | Kochen |
| US-506 | Koch-Start aus Pool ("Jetzt kochen"-Button) | Kochen |
| US-508 | Kochmodus (Schritt-für-Schritt) | Kochen |
| US-509 | Schritt-Zutaten (welche Zutaten jetzt?) | Kochen |
| US-510 | Quellen-Zugriff im Kochmodus | Kochen |
| US-605 | Schritte anlegen/bearbeiten | Rezepte |
| US-607 | Zutaten-Zuordnung zu Schritten | Rezepte |
| US-609 | Manuelles Tagging | Rezepte |
| US-610 | Gesamtzeit erfassen | Rezepte |
| US-614 | Rezept bearbeiten | Rezepte |
| US-616 | Rezept-Archivierung (Soft-Delete mit UI) | Rezepte |
| US-701 | Harte Regeln / Ausschluss-Kriterien | Regeln |
| US-702 | Sortier-Regeln / Präferenzen | Regeln |
| US-801 | Rezept-Liste (vollständig) | Rezepte |
| US-902 | Einheiten-Management (Umrechnungsfaktoren) | Datenpflege |
| US-906 | Vorrats-Management ("Immer vorrätig"-UI) | Datenpflege |

---

## Erweiterungen bestehender API-Responses (MVP)

### RecipeSummaryDto (GET /api/recipes)
Im SKELETON nur `{ id, title }`. Ab MVP um Metadaten erweitern, mind. Tags (US-609) und Gesamtzeit (US-610):
`{ id, title, tags: string[], durationMinutes: int? }`

---

## Neue DB-Entities (MVP)

- **Tag** – hierarchisches Schlagwort (DAG-Struktur vorbereiten, flat in MVP)
- **RecipeTag** – Rezept ↔ Tag (n:m)
- **IngredientModifier** – Varianten einer Zutat (z.B. "stückig", "passiert")
- **Rule** – Harte & Weiche Planungsregeln
- **Unit + ConversionFactor** – Einheiten-Management
- **NonFoodItem** – Freitext-Einträge für Einkaufsliste

### ShoppingListItem erweitert
- `ManualAdjustment` (decimal, DEFAULT 0) – User-Korrektur zur berechneten Menge

### ShoppingListItemSource (NEU)
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `Id` | int | PK |
| `ShoppingListItemId` | int | FK → ShoppingListItem, CASCADE |
| `RecipeId` | int | FK → Recipe, CASCADE |
| `Quantity` | decimal | Anteil aus diesem Rezept |

**Index:** UNIQUE (ShoppingListItemId, RecipeId)

Ermöglicht: Welche Zutat kommt aus welchem Rezept → Transparenz-Anzeige in V1.

### WeeklyPoolEntry erweitert
- `PlannedDate` (date?) – Kalender-Zuordnung
- `PlannedPortions` (decimal?) – Planungs-Portion (Default: Basis-Portion des Rezepts)

---

## Intelligente Einkaufslisten-Generierung (MVP)

Statt einfachem Delete+Recreate (SKELETON):

1. Für jedes Pool-Rezept: Zutaten-Bedarf berechnen
2. Aggregieren nach Zutat + Einheit
3. Wenn Item bereits existiert und `BoughtAt != null` → ignorieren (schon gekauft)
4. Wenn Item existiert und `BoughtAt == null` → Sources aktualisieren, Menge neu berechnen
5. `ManualAdjustment` bleibt erhalten
6. Bei Pool-Rezept-Entfernung: CASCADE löscht Sources → Menge neu berechnen → wenn ≤ 0: Item löschen

---

## Offline-Sync-Strategie (US-306)

**Service Worker (Workbox):**
- Cache-First für Lesezugriffe
- Network-First mit Fallback für Schreiboperationen
- Background-Sync: Änderungen bei Reconnect synchronisieren

**IndexedDB:** Lokale Datenhaltung für Einkaufsliste

**Konfliktlösung: "Last-Write-Wins mit Nutzer-Transparenz"**
1. Jede Änderung bekommt einen Client-Timestamp
2. Bei Konflikt: Jüngerer Timestamp gewinnt + Toast "Deine Änderung wurde überschrieben. [Undo]"
3. Abhaken: Kein Konflikt (deterministisch)
4. Additive Änderungen gewinnen über Delete/Reduce

**Polling:** Einkaufsliste prüft alle 3-5 Sekunden auf Server-Updates (nur wenn App im Vordergrund).

**HTTPS-Anforderung:** Service Worker funktioniert nur mit HTTPS (oder localhost in Dev). Lokale Entwicklung auf `http://localhost` ist OK.

---

## Neue API-Endpoints (MVP, Auszug)

```
# Planungs-Wizard
POST   /api/planning/generate          Vorschläge generieren
POST   /api/planning/commit            Plan übernehmen

# Tags
GET    /api/tags
POST   /api/tags
DELETE /api/tags/{id}

# Einheiten
GET    /api/units
POST   /api/units/{id}/conversions

# Kochmodus
GET    /api/recipes/{id}/cooking-mode  Schritte mit zugeordneten Zutaten
POST   /api/cooking-history            Rezept als "gekocht" markieren
```

*Details werden beim Implementieren aus USER_STORIES.md abgeleitet.*
