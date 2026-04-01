---
name: review-docs
description: Vollständige Qualitätsprüfung der Projektdokumentation: Guidelines, Skills, Agenten, CLAUDE.md und globale ~/.claude-Dateien. Analysiert Konsistenz, Progressive Disclosure, Verständlichkeit, Vollständigkeit und Minimalität mithilfe paralleler Sub-Agenten. Liefert priorisierte Verbesserungsvorschläge und arbeitet Findings interaktiv ab. Nur manuell aufrufen via /review-docs oder expliziter Erwähnung – nicht auto-triggern.
---

# Dokumentations-Review

Ziel: Strukturierte, priorisierte Verbesserungsvorschläge für alle Dokumentations- und Konfigurationsdateien des Projekts. **Phase 1: Nur analysieren, keine Änderungen vornehmen.**

## Bekannte Grenzwerte (fest, kein Re-Recherchieren nötig)

| Datei/Typ | Grenzwert | Art |
|-----------|-----------|-----|
| CLAUDE.md | < 200 Zeilen empfohlen | Soft (Befolgungsrate sinkt darüber) |
| MEMORY.md | 200 Zeilen / 25 KB | Hard Truncation beim Session-Start |
| Diskrete Instruktionen | ~150–200 gesamt; ~50 davon verbraucht Claude Code selbst | Forschungsbasiert |
| CLAUDE.md Dateigröße | < 40 KB | Soft (claudelint warnt ab hier) |

## Scope

**Projekt-Level** (Arbeitsverzeichnis):
- `CLAUDE.md` (Projekt-Root)
- `docs/AGENT_MEMORY.md`
- `docs/` – alle Markdown-Dateien, **außer** `docs/history/sessions/` (Session-Logs, keine Richtlinien)
- `docs/history/decisions.md` und `docs/history/lessons_learned.md` (explizit einschließen)
- `.claude/skills/` – alle Skill-Definitionen
- `.claude/agents/` – alle Agenten-Definitionen (falls vorhanden)
- `.claude/settings.json`

**Global** (`~/.claude/` – gesonderte Behandlung, siehe unten):
- `~/.claude/CLAUDE.md` (falls vorhanden)
- `~/.claude/skills/`
- `~/.claude/settings.json`

## Schritt 1: Dateigrößen prüfen

Messe die Zeilenzahl und Dateigröße der kritischen Dateien mit `wc -l` und `wc -c`. Vergleiche mit den Grenzwerten aus der Tabelle oben. Halte die Ergebnisse fest – sie fließen in Section 0 des Outputs ein.

## Schritt 2: Vier parallele Sub-Agenten starten

**Wichtig: Sub-Agenten nach Analyse-Dimension aufteilen, nicht nach Dateibereich.** Jeder Agent liest alle relevanten Dateien, fokussiert aber auf eine andere Fragestellung. Nur so können Widersprüche *zwischen* Dokumenten erkannt werden.

---

### Validierungsstandard (gilt für alle vier Agenten, nicht verhandelbar)

**Vor jedem Finding: Verifikationspflicht.**
Lies die relevante Stelle in der Zieldatei und zitiere sie – entweder als Beweis dass etwas fehlt ("Datei X hat keine Erwähnung von Y") oder als Widerlegung deines eigenen Verdachts ("Datei X Z.42 sagt bereits Y → kein Finding"). Verweise in der Zieldatei auf andere Dateien MÜSSEN verfolgt werden, bevor ein "fehlt"-Finding formuliert wird. Ein Finding ohne geprüfte Zielstelle ist ungültig.

**Ein Finding ist nur valide wenn ALLE drei Punkte zutreffen:**
1. Die Information existiert NICHT in der Zieldatei und NICHT in den Dateien auf die sie verweist
2. Das Fehlen führt zu einem konkreten, beschreibbaren Fehlverhalten: "Agent X würde in Situation Y Code/Entscheidung Z produzieren, die falsch ist"
3. Es handelt sich nicht um allgemeines Sprachfeature-Wissen (C#-Keywords, Zugriffsmodifikatoren) oder allgemeines Claude-Code-Systemwissen (Skill vs. Agent, user-invocable etc.)

**Kein "könnte" ohne Szenario.** "Könnte missverstanden werden" ohne konkretes Fehlverhaltensszenario ist kein Finding. Entweder: konkretes Szenario beschreiben → Finding. Oder: als Beobachtung ohne Impact vermerken (erscheint NICHT in der Finding-Liste).

**Abstraktionsebenen unterscheiden.** Vor dem Flaggen von Duplikation/Inkonsistenz prüfen: Beschreiben beide Stellen tatsächlich denselben Sachverhalt auf derselben Abstraktionsebene? Projekt-Visibility ≠ Typ-Sichtbarkeit. Konzept-Erklärung ≠ Implementierungsregel. Kurzer Verweis in CLAUDE.md ≠ vollständige Regeldefinition in einem Doc.

---

**Sub-Agenten-Prompts:** Füge den Validierungsstandard oben als ersten Abschnitt in den Prompt jedes Sub-Agenten ein, bevor du die agenten-spezifischen Anweisungen übergibst. Nur so ist gewährleistet, dass der Standard tatsächlich im Kontext der Sub-Agenten landet.

**Ausgabeformat für Agenten 1–3:** Jeder Agent gibt seine Findings im folgenden Format zurück. Dieses Format ebenfalls in den Prompt einfügen:

```
## FINDING: [prägnanter Titel]
**Dimension:** [Progressive Disclosure | Konsistenz | Verständlichkeit]
**Datei:** `pfad/zur/datei.md` Z.XX
**Zitat:** > exakter zitierter Text (oder: "Datei enthält keine Erwähnung von X")
**Problem:** Was genau ist falsch – und welches konkrete Fehlverhalten resultiert daraus?
**Vorschlag:** Direkte Empfehlung.
**Impact:** HOCH | MITTEL | NIEDRIG
```

Ein Finding pro Block. Mehrere Findings durch `---` trennen. Keine Prosa außerhalb dieser Blöcke.

Falls ein Agent keine Findings zurückgibt (leere Antwort): In der Aggregation explizit als "(Agent X: keine Findings)" vermerken.

Starte alle vier Agenten gleichzeitig:

---

### Agent 1 – Progressive Disclosure & Minimalität

**Frage:** Werden Agenten mit mehr Kontext belastet als für ihre jeweilige Aufgabe nötig?

Lies alle Projekt- und globalen Docs. Suche nach:
- Inhalten, die bei jeder Session geladen werden, aber nur für seltene Szenarien relevant sind
- Dokumenten oder Abschnitten, die für die meisten Aufgaben irrelevant sind, aber trotzdem im Kontext landen
- Redundanten Inhalten, die an mehreren Stellen stehen und den Kontext unnötig aufblähen
- Möglichkeiten, Inhalte in **Skills** auszulagern (primäres Mittel – laden nur bei Trigger, echte Progressive Disclosure)
- Ob das **Navigation-Table-Pattern** in CLAUDE.md genutzt wird: Verweis "lies X wenn du Y tust" statt Inhalt direkt einzubetten (lädt nichts automatisch, aber setzt diszipliniertes Abrufen voraus)
- Ob **Subdirectory-CLAUDE.md**-Dateien sinnvoll wären – aber als letztes Mittel einordnen: Sie erzwingen das Laden für *alle* Arbeit in diesem Pfad, sind also nicht wirklich lazy; sinnvoll nur wenn ein gesamtes Unterverzeichnis dauerhaft eigene Instruktionen braucht
- Dokumente, die zusammengeführt werden könnten ohne Informationsverlust

Bewerte auch: Werden Skills/Agenten klar genug beschrieben, sodass der Hauptagent nur die wirklich relevanten lädt?

---

### Agent 2 – Konsistenz & Vollständigkeit

**Frage:** Widersprechen sich Dokumente? Fehlen Informationen, die Agenten für ihre Aufgabe brauchen?

Lies alle Projekt- und globalen Docs. Suche nach:
- Widersprüchen: gleicher Sachverhalt, unterschiedliche Anweisungen in verschiedenen Docs (z.B. TDD_PROCESS.md vs. CODING_GUIDELINE vs. Skill-Beschreibungen)
- Duplikaten: gleiche Regel an mehreren Stellen – Wartungsrisiko bei Änderungen
- Terminologie-Inkonsistenzen: gleicher Begriff, verschiedene Bedeutungen; oder verschiedene Begriffe für dasselbe Konzept
- Fehlenden Verlinkungen: Doc A setzt Wissen aus Doc B voraus, verweist aber nicht auf B
- Szenarien, für die kein Dokument klare Anweisungen gibt (Lücken)
- CLAUDE.md-Navigation: Deckt die Tabelle alle realen Aufgaben ab?

---

### Agent 3 – Verständlichkeit

**Frage:** Sind die Anweisungen klar genug, dass ein Agent (oder Mensch) sie ohne Rückfragen befolgen kann?

Lies alle Projekt- und globalen Docs. Suche nach:
- Mehrdeutigen oder schwer parsbaren Formulierungen
- Fehlenden Beispielen wo das Konzept abstrakt ist
- Übermäßig langen oder verschachtelten Abschnitten, die vereinfacht werden könnten
- Anweisungen die zu vage sind um verifizierbar zu sein (z.B. "formatiere ordentlich" statt konkrete Regel)
- Inkonsistenter Sprache (Deutsch/Englisch gemischt ohne Systematik)
- Abschnitten, die für Agenten relevant sind, aber für Menschen schwer verständlich wären (oder umgekehrt)

---

### Agent 4 – Globale Konflikte (~/.claude vs. Projekt)

**Frage:** Widersprechen globale User-Settings dem Projekt, und was ist die richtige Lösung?

Lies alle Dateien in `~/.claude/` (Skills, Settings, CLAUDE.md falls vorhanden) UND alle Projekt-Level-Docs.

Für jeden gefundenen Konflikt/Widerspruch:
- **Was:** Welche Regel/Einstellung widerspricht sich?
- **Global-Zitat:** `pfad/datei` Z.XX: > exakter zitierter Text
- **Projekt-Zitat:** `pfad/datei` Z.XX: > exakter zitierter Text
- **Empfehlung:** "Im Projekt überschreiben" ODER "In ~/.claude anpassen"
- **Begründung:** Warum diese Empfehlung?

Prüfe auch: Sind globale Skills mit Projekt-Skills kompatibel? Gibt es Doppelabdeckung (gleiche Aufgabe, zwei verschiedene Skills)?

---

## Schritt 3: Ergebnisse aggregieren und ausgeben

Warte bis alle vier Agenten abgeschlossen haben.

### Pre-Filter (vor der Aggregation)

Gehe jedes gemeldete Finding durch und prüfe es gegen den Validierungsstandard aus Schritt 2:

1. **Zitat vorhanden?** Hat der Agent die betreffende Stelle wirklich gelesen und zitiert? Falls nicht: Finding verwerfen. (Für Agent-4-Einträge: beide Felder `Global-Zitat` und `Projekt-Zitat` müssen vorhanden sein.)
2. **Alle Verweise verfolgt?** Falls das Finding lautet "X fehlt in Datei A": Wurden auch alle Dateien geprüft, auf die Datei A verweist? Falls nicht: jetzt prüfen. Findet sich X dort → Finding verwerfen.
3. **Konkretes Fehlverhalten?** Falls das Finding nur "könnte missverstanden werden" ohne Szenario beschreibt → Finding verwerfen.
4. **Richtige Abstraktionsebene?** Falls das Finding Duplikation meldet: sind es wirklich identische Regeln auf derselben Ebene? Falls nein → Finding verwerfen.

Verworfene Findings werden nicht ausgegeben. Es ist kein Fehler, wenn nach dem Pre-Filter weniger Findings übrig bleiben – das ist das Ziel.

Dedupliziere die verbleibenden Findings, die von mehreren Agenten identisch erkannt wurden. Wenn zwei Agenten dasselbe Problem aus verschiedenen Winkeln sehen, fasse es zu einem Finding zusammen.

Falls nach Pre-Filter und Deduplizierung keine Findings verbleiben: dem User mitteilen ("Keine validen Findings gefunden – Dokumentation ist konsistent und vollständig.") und Phase 2 überspringen.

### Findings speichern

Schreibe die vollständigen Findings in `.claude/tmp/doc-review-YYYY-MM-DD.md` (aktuelles Datum einsetzen). Diese Datei wird in Phase 2 zum Nachschlagen verwendet.

Format der gespeicherten Datei:
```
# Doc Review – YYYY-MM-DD

## Dateigrößen-Check
| Datei | Zeilen | Größe | Status |

## Globale Konflikte
| Was | Global sagt | Projekt sagt | Empfehlung | Begründung |

## Findings

### [#1 – HOCH] Titel der das Problem vollständig beschreibt

**`pfad/zur/datei.md` Z.42** *(Dimension)*
> exakter zitierter Text

**Kontext:** Was genau ist das Problem und warum ist es problematisch?
**Vorschlag:** Direkte Empfehlung.
[Optional bei komplexen Entscheidungen:]
**Optionen:**
- Option A: ...
- Option B: ...
```

### Dem User ausgeben

Zeige dem User **nur**:

```
## CEO-Übersicht
| # | Impact | Was ist das Problem? | Wo? |
|---|--------|----------------------|-----|
| 1 | HOCH   | [kurze, schnell scanbare Beschreibung – lieber 2 kurze Sätze als 1 langer] | Dateiname |
...

## Dateigrößen-Check
| Datei | Zeilen | Größe | Status |
...

## Globale Konflikte (~/.claude vs. Projekt)
| Was | Global sagt | Projekt sagt | Empfehlung |
... [oder: "Keine Konflikte gefunden."]

---
Vollständige Analyse: `.claude/tmp/doc-review-YYYY-MM-DD.md`
```

**Hinweise zur CEO-Übersicht:**
- Jedes Finding ist eine Zeile. "Was ist das Problem?" muss schnell verständlich sein – kurze Sätze, maximal 3, kein Schachtelsatz.
- Sortierung: Hoch → Mittel → Niedrig.

**Priorisierung nach Impact:**
- **Hoch:** Führt wahrscheinlich zu falschem Agentenverhalten, ignoriertem Kontext oder widersprüchlichen Anweisungen
- **Mittel:** Verschlechtert Qualität oder Effizienz merklich, aber kein direkter Fehler
- **Niedrig:** Kosmetisch, nice-to-have, minimaler praktischer Effekt

---

## Phase 2: Findings abarbeiten

Nach der Ausgabe der CEO-Übersicht:

1. **Gruppierung prüfen:** Bevor der User gefragt wird – prüfe, ob mehrere Findings denselben Ort, dieselbe Datei oder dasselbe Konzept betreffen und sinnvoll zusammen gelöst werden können. Fasse solche Findings zu benannten Gruppen zusammen. Das Ergebnis ist eine geordnete Arbeitsliste aus Einzelfindings und Gruppen.

2. **Pausieren** und den User fragen: mit welchem Eintrag soll begonnen werden, oder ob er eine andere Reihenfolge bevorzugt?

Den folgenden Loop durchlaufen bis alle Einträge abgearbeitet sind oder der User abbricht:

**Pro Eintrag (Einzelfinding oder Gruppe):**

1. **Lies** die betreffenden Findings aus `.claude/tmp/doc-review-YYYY-MM-DD.md`.

2. **Zeige** dem User:
   - Fortschrittsindikator: `Eintrag X von Y – [Titel / Gruppenname]` (bei Gruppen: alle enthaltenen Finding-Titel in Kurzform auflisten)
   - Titel + Kontext-Snippet (zitierter Text)
   - Bei offensichtlichem Fix: direkte Empfehlung
   - Bei komplexeren Entscheidungen: 2–3 Optionen mit kurzer Abwägung

3. **Warte** für nicht-offensichliche Fixes auf die Reaktion des Users:
   - User bestätigt / wählt Option → umsetzen, weiter mit nächstem Eintrag
   - User schlägt eigene Lösung vor → prüfen ob sie mit den Guideline-Zielen vereinbar ist; falls Konflikt: klar benennen bevor umgesetzt wird
   - User bricht ab (z.B. "stop", "reicht", "genug") → Loop beenden

   **Vor dem Umsetzen den `grill-me`-Skill (via Skill-Tool) aufrufen wenn:** (a) unklar ist ob die gewählte Lösung mit den Guidelines vereinbar ist, oder (b) das Zielbild des Users nicht vollständig verstanden wurde. Besonders bei (b) nicht voreilig umsetzen – lieber einmal zu viel nachfragen als in die falsche Richtung ändern.

4. **Umsetzen** der gewählten Lösung (Dateien bearbeiten).

5. **Kurze Bestätigung** was geändert wurde, dann automatisch weiter mit dem nächsten Eintrag.

Wenn alle Einträge abgearbeitet sind: `"Alle Findings abgearbeitet – Review abgeschlossen."` ausgeben und beenden.
