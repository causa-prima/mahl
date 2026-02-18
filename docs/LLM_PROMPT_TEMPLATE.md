# LLM Prompt Template

Verwende diesen Prompt, um ein LLM mit der Implementierung des Mahl-Projekts zu beauftragen.

---

## Einfacher Startprompt

```
Ich möchte, dass du die "Mahl"-App gemäß den Spezifikationen im Repository implementierst.

Bitte lies zunächst folgende Dokumente vollständig:
1. docs/AGENT_MEMORY.md - Prüfe ob bereits Arbeit geleistet wurde (Session-Kontinuität)
2. docs/IMPLEMENTATION_GUIDE.md - Vollständige technische Spezifikation
3. docs/GLOSSARY.md - Domain-Modell und ubiquitäre Sprache (bindend!)
4. docs/USER_STORIES.md - Alle Features mit Prioritäten
5. CLAUDE.md - Entwicklungsrichtlinien und bestehende Code-Patterns

Wichtige Hinweise:
- **TDD ist Pflicht:** Tests VOR Implementierung schreiben (Red-Green-Refactor)
- **Mutation Testing:** Periodisch mit Stryker.NET/Stryker-JS validieren (Ziel: 90%+ Coverage, Ausnahmen begründen)
  - Hybrid-Ansatz: Vollständiger Lauf am Ende jeder Phase, schnelle Iteration mit `--files` während Feature-Entwicklung
- Es existiert bereits Code im Repository, der als Referenz für Patterns dient (siehe Shared/Types/, Server/)
- Die Domain-Modeling-Patterns (Custom Value Types, Factory Methods, OneOf) sind NICHT optional
- **Konsultiere Sub-Agenten:** Hole regelmäßig Feedback von Refactoring-, UI/UX-, Security-Experten ein
- **Agent Memory aktualisieren:** Am Ende jeder Session AGENT_MEMORY.md updaten
- Beginne mit der SKELETON-Phase (siehe IMPLEMENTATION_GUIDE.md Abschnitt 5)
- Gehe iterativ vor: Feature für Feature, mit Tests

Frage mich, wenn du Entscheidungen treffen musst, die nicht in den Specs dokumentiert sind.

Los geht's!
```

---

## Detaillierter Prompt mit Phasen-Fokus

### Phase 1: SKELETON

```
Implementiere die SKELETON-Phase der Mahl-App gemäß docs/IMPLEMENTATION_GUIDE.md.

Kontext:
- Session-Status: docs/AGENT_MEMORY.md (falls bereits Sessions gelaufen sind)
- Vollständige Specs: docs/IMPLEMENTATION_GUIDE.md
- Domain-Modell: docs/GLOSSARY.md
- User Stories (nur [SKELETON]-getaggte): docs/USER_STORIES.md
- Bestehende Code-Patterns: Shared/Types/, Server/Data/

Workflow:
1. **Prüfe AGENT_MEMORY.md:** Was wurde bereits gemacht?
2. **Analysiere bestehenden Code** und verstehe die Patterns
3. **Triff Entscheidungen** (mit Begründung dokumentieren):
   - Frontend-Framework (Blazor vs. React vs. Vue) - siehe Implementation Guide Abschnitt 2.1
   - Datenbank (PostgreSQL vs. MariaDB) - siehe Abschnitt 2.1
   - **Optional:** Konsultiere UI/UX-Sub-Agent für Frontend-Entscheidung
4. **Setze technische Infrastruktur auf:**
   - Docker & Docker Compose
   - Datenbank-Migrations
   - Basis-Authentifizierung
   - PWA-Grundkonfiguration
5. **Implementiere alle SKELETON-User-Stories mit TDD:**
   - US-201: Pantry-Check
   - US-303: Artikel abhaken
   - US-501: Pool-Liste
   - US-505: Zutaten-Übersicht
   - US-506: Koch-Start aus Pool
   - US-602: Manuelle Rezepterfassung
   - US-605: Schritte anlegen
   - US-614: Rezept bearbeiten
   - US-801: Rezept-Liste
   - US-803: Manuelle Plan-Anpassung
   - US-904: Zutaten-Verwaltung
6. **Mutation Testing durchführen:** Stryker.NET/Stryker-JS am Ende der Phase
   - Ziel: 90%+ Coverage (Ausnahmen in AGENT_MEMORY.md dokumentieren)
   - Vollständiger Stryker-Lauf: Am Ende der Phase (SKELETON komplett abgeschlossen)
   - Zwischendurch: Nach jeder größeren Feature-Gruppe (z.B. nach 3-5 User Stories)
   - Schnelles Feedback während Entwicklung: `dotnet stryker --files <file>`
7. **Agent Memory aktualisieren:** Status, Entscheidungen, Lessons Learned

Akzeptanzkriterium:
Ein Nutzer kann sich einloggen, ein Rezept manuell anlegen, es dem Wochen-Pool hinzufügen,
die generierte Einkaufsliste sehen, Artikel abhaken, und das Rezept im Kochmodus kochen.

**Wichtig:** TDD! Tests ZUERST schreiben, dann implementieren.
```

### Phase 2: MVP

```
Implementiere die MVP-Phase der Mahl-App.

Voraussetzung: SKELETON-Phase ist abgeschlossen und getestet.

Neue Features (siehe docs/USER_STORIES.md für Details):
- Planungs-Wizard mit automatischen Vorschlägen
- Intelligente Artikelerfassung
- Offline-Verfügbarkeit der Einkaufsliste
- Vollständiger Kochmodus
- Rezept-Import (Schema.org)
- Regel-basierte Planung (Harte & Weiche Regeln)
- Einheiten-Management

Siehe docs/IMPLEMENTATION_GUIDE.md Abschnitt 5.2 für die vollständige Liste.

Fokussiere dich auf echten Nutzer-Mehrwert: Am Ende dieser Phase sollte die App
im Alltag nutzbar sein.
```

---

## Spezifischer Prompt für einzelne Features

```
Implementiere User Story US-301: Intelligente Artikelerfassung

Kontext:
- Domain-Modell: docs/GLOSSARY.md (Begriffe: Zutat, Non-Food-Item, Einkaufslisten-Eintrag)
- User Story Details: docs/USER_STORIES.md (Zeile 141-147)
- Bestehende Patterns: Siehe ShoppingListItem in Shared/

Akzeptanzkriterien:
- Live-Suche während des Tippens
- Suche in Stammdaten und aktueller Liste
- Status-Anzeige für bereits vorhandene Artikel
- Tippen fügt hinzu oder erhöht Menge
- Letzter Vorschlag ist "Neu erstellen" mit Parsing von Menge/Einheit

Bitte implementiere Backend-Endpoint, Frontend-UI und Tests.
```

---

## Troubleshooting-Prompt

Wenn das LLM Probleme hat oder vom Pfad abweicht:

```
STOP. Bitte überprüfe folgende Punkte:

1. Hast du docs/IMPLEMENTATION_GUIDE.md vollständig gelesen?
2. Verwendest du die Domain-Begriffe aus docs/GLOSSARY.md korrekt?
3. Folgst du den bestehenden Code-Patterns? (Custom Value Types, Factory Methods, OneOf)
4. Implementierst du gemäß der richtigen Phase (SKELETON/MVP/V1/V2)?
5. Hast du die Akzeptanzkriterien der User Story verstanden?

Wenn du unsicher bist, lies bitte nochmal die relevanten Abschnitte und frage spezifisch nach.
```

---

## Tipps für optimale Ergebnisse

1. **Gib dem LLM Kontext:** Verweise immer auf die relevanten Dokumente
2. **Sei spezifisch:** Benenne die Phase, User Story, oder das Feature
3. **Iteriere:** Lass Features einzeln implementieren und reviewe sie
4. **Teste früh:** Bestehe auf Tests für jedes Feature
5. **Halte den Fokus:** Ein Feature nach dem anderen, nicht alles auf einmal

---

**Hinweis:** Diese Prompts sind Vorschläge. Passe sie an deinen spezifischen Use Case und
das verwendete LLM an.
