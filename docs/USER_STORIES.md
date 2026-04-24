# User Stories & Szenarien

Dieses Dokument ist der **Index**: Vision, Personas, Priorisierung – plus Navigation zu den per-Szenario-Dateien in `docs/stories/`.
Einzelne User-Story-Beschreibungen und Akzeptanzkriterien stehen in der jeweiligen Szenario-Datei.

## Vision & Mission

**Vision (Das Zielbild)**
> "Mahl befreit den Familienalltag von der mentalen Last der Essensplanung und macht gesunde, abwechslungsreiche Ernährung zum stressfreien Selbstläufer."

**Mission (Der Auftrag)**
> "Wir entwickeln einen intelligenten Assistenten, der die Lücke zwischen Planung, Einkauf und Kochen schließt. Wir eliminieren Entscheidungsmüdigkeit durch smarte Vorschläge, optimieren den Einkauf durch Kontext-Wissen und führen entspannt durch die Zubereitung - immer mit dem Ziel, Zeit zu sparen und Verschwendung zu vermeiden."

## Priorisierung (Tags)

*   **[SKELETON]:** "Walking Skeleton". Die absolute Mindestanforderung, um einen technischen Durchstich (End-to-End) zu ermöglichen. Ohne dies ist die App nicht nutzbar.
*   **[MVP]:** "Minimum Viable Product". Der Funktionsumfang, der nötig ist, um dem Nutzer echten Mehrwert zu bieten und die Mission zu erfüllen.
*   **[V1]:** "Version 1.0" (MMP). Der erste vollständige Release, der sich "rund" anfühlt. Enthält Komfortfunktionen, Fehlerbehandlung und Features, die für eine dauerhafte Nutzung wichtig sind.
*   **[V2]:** "Version 2.0". Echte Erweiterungen, neue Module und Optimierungen für die Zukunft.

---

## Personas

Basierend auf den Szenarien haben wir folgende Rollen identifiziert:

*   **Der Feierabend-Planer (Planung):** Plant abends, wenn die Energie niedrig ist. Braucht Automatisierung und intelligente Vorschläge, um Entscheidungen zu minimieren.
*   **Der eilige Einkäufer (Einkauf Single):** Kauft unter Zeitdruck (Mittagspause). Braucht Kontextinformationen ("Wofür ist das?") für schnelle Entscheidungen im Laden.
*   **Der Familien-Einkäufer (Einkauf Gruppe):** Kauft mit Kindern ein. Braucht Robustheit gegen Fehlbedienung (Undo) und Übersicht.
*   **Der pragmatische Koch (Zubereitung):** Kocht unter Zeitdruck und mit Ablenkungen. Braucht klare Führung und schnelle Entscheidungshilfen.
*   **Der Rezept-Sammler (Verwaltung):** Pflegt die Datenbank. Braucht Import-Tools und einfache Pflege für hohe Datenqualität.

---

## Szenarien

Jedes Szenario hat eine eigene Datei unter `docs/stories/`. US-ID-Präfix korreliert mit der Szenario-Nummer (US-1xx → Szenario 1, …, US-9xx → Szenario 9; Ausnahme: US-001 in Szenario 0).

| Datei | Thema | User Stories |
|-------|-------|--------------|
| [Szenario 0 – App-Start](stories/szenario_0_app-start.md) | Kontext, Geräte-spezifische Startseite | US-001 |
| [Szenario 1 – Planung](stories/szenario_1_planung.md) | Feierabend-Planung mit Wizard | US-101 … US-110 |
| [Szenario 2 – Vorrats-Check](stories/szenario_2_vorratscheck.md) | Pantry-Check, Mengen-Delta, Fix-Einträge | US-201, US-202, US-203 |
| [Szenario 3 – Einkauf](stories/szenario_3_einkauf.md) | Eiliger Einkauf, Non-Food, Offline | US-301 … US-307 |
| [Szenario 4 – Familien-Einkauf](stories/szenario_4_familien-einkauf.md) | Undo, Live-Sync | US-401, US-402 |
| [Szenario 5 – Kochen](stories/szenario_5_kochen.md) | Kochmodus, Skalierung, Bewertung | US-501 … US-517 |
| [Szenario 6 – Rezept-Erfassung](stories/szenario_6_rezept-erfassung.md) | Import, Pflege, Sub-Rezepte | US-601 … US-617 |
| [Szenario 7 – Regeln & Setup](stories/szenario_7_regeln-setup.md) | Harte/Weiche Regeln, Fallback | US-701, US-702, US-703 |
| [Szenario 8 – Resteverwertung](stories/szenario_8_resteverwertung.md) | Rezept-Liste, Suche, Plan-Anpassung | US-801 … US-804 |
| [Szenario 9 – Datenpflege](stories/szenario_9_datenpflege.md) | Stammdaten, Einheiten, Backup, Tag-Hierarchie | US-901 … US-910 |

**Story → Szenario-Datei finden:** US-Präfix nehmen und die passende Zeile in der Tabelle wählen. Alternativ: `Grep "US-904" docs/stories/` liefert die Datei direkt.
