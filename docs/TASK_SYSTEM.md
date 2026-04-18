# Task-System – Regeln

<!--
wann-lesen: Wenn eine Aufgabe mit ≥ 3 Schritten geplant wird und Tasks angelegt werden sollen.
-->

Sobald eine Aufgabe **≥ 3 größere Schritte** erfordert, wird eine Task-Liste angelegt. Beispiele:
- Einzelner Unit-Test (RED→GREEN→REFACTOR als Einheit): **keine** Task-Liste
- Endpoint mit ≥ 3 Verhaltensweisen (happy path + error + edge case): **Task-Liste**
- Feature mit Arch-Check + TDD-Zyklen + Review + Docs: **Task-Liste**

## Regeln

**Anlegen:** Nach kurzer Analyse Top-Level-Tasks anlegen (Namenskonvention `1.`, `2.`, `3.`...).

**Status:**
- `in_progress` setzen unmittelbar bevor die erste Aktion eines Steps ausgeführt wird
- `completed` setzen bevor der nächste Step beginnt – **nur wenn der Task nicht gelöscht wird**

**Abgeschlossene Tasks:** Kurze Listen → `completed` stehen lassen. Lange Listen → beim
Betreten des nächsten Steps löschen (statt `completed` zu setzen).

**Neuer Task-Block (z.B. neuer Skill-Aufruf):** Vor dem Anlegen neuer Tasks alle noch offenen
Tasks aus dem vorherigen Block explizit schließen (`completed`) oder löschen (`TaskStop`).
Ausnahme: Die neuen Tasks sind Erweiterungen des laufenden Blocks – dann einfach anhängen.

**Plan-Änderungen (Einfügung zwischen bestehende Tasks):**
- ≤ 2 nachfolgende Tasks: löschen + neu anlegen (korrekte Reihenfolge)
- Sonst: Einschub-Notation `"2b. Titel"` (Threshold empirisch anpassen)

## Skills mit vordefinierten Task-Strukturen

`implementing-feature`, `review-code`, `closing-session` definieren ihre Task-Strukturen selbst.
Für alle anderen gilt: Agent legt bei Bedarf selbst eine passende Struktur an.
