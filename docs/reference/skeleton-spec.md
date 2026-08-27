# SKELETON-Spezifikation

<!--
wann-lesen: Überblick über SKELETON-Scope (welche User Stories) und das Walking-Skeleton-Akzeptanzkriterium
kritische-regeln:
  - Kein produktiver Code – nur Referenz
  - Entscheidungen → docs/history/adr.md
  - Architektur-Constraints → [SKELETON-Phase: Scope-Constraints](architecture.md#ARC-skeleton-constraints)
  - Verhaltenserwartungen → Gherkin-Szenarien in features/
-->

---

<a id="SKE-ziel"></a>
## Ziel

Minimaler technischer Durchstich (End-to-End), der alle Schichten verbindet:
**Zutat anlegen → Rezept anlegen → Rezept in Pool → Einkaufsliste generiert & abhakbar**

---

<a id="SKE-user-stories"></a>
## User Stories im SKELETON

| Story | Beschreibung |
|-------|-------------|
| US-904 | Zutaten-Verwaltung (CRUD) |
| US-602 | Manuelle Rezepterfassung (Titel + Zutaten + Schritte + Foto-Upload) |
| US-803 | Rezept dem Wochen-Pool hinzufügen (flache Liste, keine Datumslogik) |
| US-201 | Einkaufsliste anzeigen (generiert aus Pool) |
| US-303 | Artikel abhaken (BoughtAt-Timestamp, verschiebt in "Zuletzt gekauft") |

> Verschoben auf MVP: `PUT /api/ingredients/{id}` (Edit-UI)

---

<a id="SKE-api-routen"></a>
## API-Routen (Übersicht)

| Gruppe | Methoden |
|--------|---------|
| `/api/ingredients` | GET, POST, GET/{id}, DELETE/{id}, POST/{id}/restore |
| `/api/recipes` | GET, POST, GET/{id}, DELETE/{id} |
| `/api/weekly-pool` | GET, POST /recipes/{recipeId}, DELETE /recipes/{recipeId} |
| `/api/shopping-list` | GET, POST /generate, PUT /items/{id}/check, PUT /items/{id}/uncheck |

Alle nicht-offensichtlichen Verhaltensdetails (Status-Codes, 409-Varianten, Sortierung etc.) → `docs/history/adr.md` (Abschnitt „Ingredients-Endpoints" / „Recipes-Endpoints").

---

<a id="SKE-akzeptanzkriterium"></a>
## Akzeptanzkriterium (Walking Skeleton)

1. Zutat anlegen (z.B. "Tomaten, Stück")
2. Rezept anlegen (Titel + mind. 1 Zutat + 1 Schritt)
3. Rezept dem Pool hinzufügen
4. Einkaufsliste generieren → zeigt "Tomaten Xg"
5. Artikel abhaken → verschiebt in "Zuletzt gekauft"
