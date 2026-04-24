---
name: implementing-scenario
description: >
  Implementiert ein einzelnes freigegebenes Gherkin-Szenario end-to-end: Architektur-Check,
  Double-Loop TDD mit Subagenten pro Schicht, Orchestrator-Check, Review-Loop und Commit.
  Voraussetzung: das Szenario muss bereits via /gherkin-workshop freigegeben sein – fehlt es
  in features/, stoppt der Skill sofort. Verwende diesen Skill immer wenn ein @US-NNN-Szenario
  implementiert werden soll. Typische Trigger: „implementiere Szenario X", „fang mit dem ersten
  Szenario an", „nächstes Szenario", „happy-path implementieren", direkter Aufruf via /implementing-scenario.
user-invocable: true
---

# Szenario implementieren

Implementiere Szenario $ARGUMENTS.
Fehlen `$ARGUMENTS` → User nach Tag (`@US-NNN-tag`) und Szenario-Titel fragen, bevor weitergegangen wird.

Aufruf: `/implementing-scenario @US-NNN-tag "Szenario-Titel"`
Beispiel: `/implementing-scenario @US-904-happy-path "Neue Zutat anlegen"`

Der Ablauf ist bewusst outside-in strukturiert: Der E2E-Test definiert zuerst das gewünschte
Verhalten von außen – erst danach entsteht Produktionscode, der dieses Verhalten erfüllt. So
bleibt der Test die Spec, nicht der Code. Architekturentscheidungen kommen vor dem ersten Test,
weil sie im Nachhinein teuer zu ändern sind. Die Implementierungsarbeit delegiert der Haupt-Thread
an Subagenten, damit er selbst keine Coding-Guidelines laden muss und den Überblick behält.

Zwei Ausführungsregeln gelten für den gesamten Ablauf:
- Dateien > 100 Zeilen in der Regel nicht komplett lesen: TOC zuerst (Read mit `limit: 30`), dann gezielt per Grep oder `Read offset/limit`. Ausnahme: muss ein spezifischer, abgrenzbarer Abschnitt vollständig erfasst werden (z.B. ein einzelnes Gherkin-Szenario), darf dieser komplett gelesen werden.
- Implementierungsarbeit (Schritte 1–3) und Reviews (Schritt 5) an Subagenten delegieren – der Haupt-Thread orchestriert.

GRUNDSATZ: Die Regeln sind starke Guidelines, keine absoluten Gesetze. Gibt es sehr gute Gründe
abzuweichen: sofort kommunizieren und auf Bestätigung warten. Ein guter Grund liegt vor, wenn
das strikte Befolgen einer Regel nachweislich zu schlechterem Ergebnis führt – z.B. wenn ein
Test ohne vorangehende Domain-Typen nicht schreibbar ist (zirkuläre Abhängigkeit). Kein guter
Grund: Zeitdruck, Bequemlichkeit, "das klappt schon so".

Lege folgende Task-Liste an (Regeln: `docs/TASK_SYSTEM.md`):
```
TaskCreate: "Schritt 0: Architektur-Check"
TaskCreate: "Schritt 1–3: TDD-Zyklus (Double-Loop)"
TaskCreate: "Schritt 4: Orchestrator-Check"
TaskCreate: "Schritt 5: Review-Loop"
TaskCreate: "Schritt 6: Commit & Session-Abschluss"
```

── SCHRITT 0: ARCHITEKTUR-CHECK ─────────────────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": in_progress

Beantworte diese Fragen schriftlich, bevor der erste Test geschrieben wird.
Der Schritt ist wichtig, weil nachträgliche Architekturentscheidungen teuer sind –
einmal Code da, ist die Versuchung groß, die Entscheidung an den Code anzupassen statt umgekehrt.

**Gezielt lesen, nicht full-read:**
- Akzeptanzkriterien: `docs/stories/szenario_N_*.md` (N = US-Präfix, z.B. US-904 → szenario_9_datenpflege.md; Mapping-Tabelle: `docs/USER_STORIES.md`)
- Architektur-Patterns: `docs/ARCHITECTURE.md` – TOC lesen, dann nur relevante Sektionen
- Phasen-Spec: Phase aus `docs/AGENT_MEMORY.md` → `docs/SKELETON_SPEC.md` oder `docs/MVP_SPEC.md` (nur API+DB-Sektion der Story)
- Feature-Datei: `features/<story>.feature` – nur das Szenario mit Tag `$ARGUMENTS` vollständig lesen

Fragen:

1. **ATDD-Gate:** Szenario `$ARGUMENTS` in `features/` vorhanden?
  - Nicht vorhanden? → STOP. Erst `gherkin-workshop` für die User Story ausführen,
     dann zurückkommen. Ohne freigegebenes Gherkin-Szenario fehlt die objektive
     Fertigstellungsbedingung – der Code kann nicht als "Done" gelten. Vorhanden: Given/When/Then vollständig notieren – das ist die exakte Spec.
2. **YAGNI/KISS-Scope:** Was ist das Minimal-Notwendige für genau dieses Szenario?
   Was wäre Gold-Plating (= kein Test dafür existiert, kein Akzeptanzkriterium fordert es)?
   Notiere explizit: *"Folgendes implementiere ich NICHT: ..."*

3. **Domain-Typen & Architektur:** Brauche ich neue Domain-Typen?
   - Struktur: `readonly record struct` für Value Objects, `abstract record` für Sum-Types?
   - Error-States: Wie typisiert? (`OneOf<T, Error<string>>`, kein `T?` in Domain-Properties)
   - Alle neuen Typ-Deklarationen in `Server/` sind `internal` (kein `public` ohne Begründung)
   - Neuer Infrastruktur-Code (DbContext, DbTypes) gehört in `Infrastructure/`, nicht in `Server/`

4. **Entscheide:** Berührt das Szenario eine bestehende Entscheidung in `docs/history/decisions.md`?
   Falls ja, gilt sie noch? Falls neue Architekturentscheidung nötig: User fragen, bevor Code
   geschrieben wird. Selbst entschiedenes in `docs/history/decisions.md` dokumentieren.

Schriftliche Antwort auf alle vier Punkte.
Dieser Schritt ist reine Analyse – noch kein Produktionscode schreiben. Domain-Typen und
Implementierungsdetails entstehen im TDD-Zyklus, wenn Tests sie erzwingen.

── SCHRITT 1–3: TDD-ZYKLUS (DOUBLE-LOOP) ───────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": completed | TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": in_progress

Ziel: genau das Szenario aus $ARGUMENTS vollständig grün bekommen – nicht mehr, nicht weniger.

**Äußerer Loop – E2E-Test (Haupt-Thread):**

Schreibe selbst den Playwright-Test für das Szenario (Given/When/Then 1:1) – bevor der erste Subagent gespawnt wird. Führe ihn aus und zeige die Fehlermeldung. Das beweist, dass der Test echtes Verhalten misst und noch nicht durch bestehende Implementierung zufällig grün werden kann. Referenz: `docs/E2E_TESTING.md` (TOC zuerst).

Dieser Test bleibt rot, bis alle inneren Loops abgeschlossen sind – das ist gewollt. Der Haupt-Thread ändert den E2E-Test während der inneren Loops nicht.

**Innerer Loop – Subagent pro Schicht (Delegation ist Pflicht):**

Für jede Schicht einen Subagenten spawnen. Haupt-Thread lädt KEINE Coding-Guidelines – der
Subagent tut das selbst.

**Schicht-Reihenfolge (outside-in):**
- Backend-Szenario: API-Endpoint → Domain-Typen/Validierung → Service/Repository
- Frontend-Szenario: React-Komponente (mit Service-Mock, TDD) → Service-Client (TypeScript-API-Funktion, mit MSW-Mock, TDD)
- Full-Stack-Szenario: E2E → Frontend (oben) → Backend (oben)

**Subagent-Prompt-Template** (`Agent` mit `subagent_type: "general-purpose"`, EINE Schicht pro Aufruf):

Befülle das Template mit den konkreten Werten aus Schritt 0, bevor du den Subagent-Aufruf absetzt.

```
Implementiere Schicht <LAYER> für Gherkin-Szenario <TAG> "<TITEL>".

Lies diese Docs vor deinem ersten Test – in dieser Reihenfolge, TOC zuerst, dann gezielt.
Du startest ohne Projektkontext und würdest sonst auf allgemeines Wissen zurückfallen, das
hier an entscheidenden Stellen abweicht: das TDD-Format, Railway-Oriented Programming in C#,
Branded Types und neverthrow in TypeScript. Die Reihenfolge folgt Abhängigkeiten: erst das
Prozess-Framework (wie du vorgehst), dann allgemeine Prinzipien, dann das Layer-spezifische Handwerk.
- docs/TDD_PROCESS.md  (Sektion "Outside-In ATDD / Double-Loop TDD" + Red-Green-Refactor)
- docs/CODING_GUIDELINE_GENERAL.md  (komplett, ist klein)
- Layer-spezifisch:
  * C#-Endpoint/Validierung: docs/CODING_GUIDELINE_CSHARP.md + docs/CSharp-ROP.md
  * C#-Sum-Types: + docs/CSharp-SumTypes.md
  * TypeScript/React:        docs/CODING_GUIDELINE_TYPESCRIPT.md
  * React-Komponente (pages/components): + docs/CODING_GUIDELINE_UX.md

Akzeptanzkriterien (inline):
<Given/When/Then aus Schritt 0 einfügen>

Scope-Grenzen (NICHT implementieren):
<YAGNI-Liste aus Schritt 0 einfügen>

Failing E2E-Test: <Pfad zur spec.ts>

Vorgehen (strikt einhalten):
1. RED: Genau einen Test schreiben (Unit/Integration passend zur Schicht). Ausführen, Fehlermeldung zeigen.
2. GREEN: Minimale Implementierung. "Fake it till you make it" ist Pflicht. Alle Tests ausführen.
3. REFACTOR: Checkliste aus docs/TDD_PROCESS.md Phase 3 vollständig abarbeiten – inklusive Stryker + Branch Coverage (Pflicht). Ziel: 100 % Mutation Score + 100 % Branch Coverage.
TDD-Abweichung (z.B. Test NACH Code) ist ein Prozess-Fehler – dann STOP und berichten.

Ausgabe:
- Diff der Änderungen (Dateinamen + Hunks)
- Output je Test-Run (RED, GREEN, REFACTOR-Grün)
- Stryker-Score + Branch-Coverage-Score
- Suppression-Report: neue Suppressionen mit Datei:Zeile + Begründung (oder "keine")
- Kurzer Report: was implementiert, was bewusst weggelassen
```

Spawn-Regeln:
- EINE Schicht pro Subagent – keine Mehrfach-Schichten im selben Aufruf (sonst verschwimmt TDD-Disziplin).
- Haupt-Thread reviewt den Diff und den Test-Run-Output nach jedem Subagent-Return.
- Weicht der Subagent von TDD ab → Finding direkt fixen (ggf. neuer Subagent-Call).

**E2E-Loop schließen (Haupt-Thread):**

Nach allen inneren Loops: Playwright-Test erneut ausführen. Noch rot? Fehlende Verbindung
(Routing? API-Integration?) identifizieren → neuer Schicht-Subagent.

── SCHRITT 4: ORCHESTRATOR-CHECK ────────────────────────────────────────────
→ TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": completed | TaskUpdate "Schritt 4: Orchestrator-Check": in_progress

Der Haupt-Thread prüft, bevor externe Reviewer spawnen. Drei Punkte:

1. **Test-Qualität (Gold-Plating-Check):** `git diff` ausschließlich der Test-Dateien lesen.
   Jede Assertion muss sich einem konkreten Given/When/Then des aktuellen Szenarios zuordnen
   lassen. Assertions ohne passendes Akzeptanzkriterium → Schicht-Subagent spawnen mit Auftrag,
   die überflüssige Assertion zu entfernen (und ggf. den damit verbundenen nicht-geforderten
   Produktionscode).

2. **Suppression-Check:** `git diff` nach `// Stryker disable` und `/* v8 ignore` durchsuchen.
   Für jede neue Suppression: Begründung kritisch hinterfragen (nicht nur auf Vollständigkeit –
   sondern gemäß `docs/kaizen/principles.md` auf inhaltliche Validität: beweist die Begründung
   echte Äquivalenz / Nichttestbarkeit, oder klingt sie nur plausibel?). Schwache Begründung
   → Schicht-Subagent spawnen mit Auftrag, entweder den Test zu ergänzen oder den
   nicht-geforderten Produktionscode zu entfernen.

3. **Scores verifizieren:** Stryker-Score + Branch-Coverage-Score aus den Subagent-Ausgaben
   lesen. Kein Score gemeldet oder Wert unklar → Stryker + Coverage selbst ausführen.
   Score < 100 % bestätigt → als `lessons_learned` dokumentieren (Subagent hat
   REFACTOR-Pflicht verletzt), Ursache per `docs/TDD_PROCESS.md` REFACTOR-Logik analysieren
   (Gold-Plating / fehlender Test / äquivalenter Mutant), dann Schicht-Subagent für die
   Korrektur spawnen.

Triviale Findings (Tippfehler, eindeutig falsche Suppression-Begründung) darf der Haupt-Thread
selbst fixen. Alles andere → Schicht-Subagent.

── SCHRITT 5: REVIEW-LOOP ───────────────────────────────────────────────────
→ TaskUpdate "Schritt 4: Orchestrator-Check": completed | TaskUpdate "Schritt 5: Review-Loop": in_progress

Review-Runden mit frischen Agenten pro Runde. Max. 3 Runden.

**Pro Runde:**

1. `.claude/skills/review-code/SKILL.md` laden und den darin beschriebenen Prozess ausführen.
   Eingaben übergeben: Scope, geänderte Dateien, Stryker-Suppression-Report aus Schritt 1–3.
   Keine neue Task-Liste anlegen – review-code läuft eingebettet in den implementing-scenario-Ablauf.
   Die von review-code gespawnten spezialisierten Agenten erhalten **kein Iterations-Wissen** –
   weder Findings aus früheren Runden noch Hinweise auf bereits abgelehnte false positives.

2. Findings im **Haupt-Thread** auswerten:
   - ❌ Must Fix → neuer Schicht-Subagent spawnen (mit Coding-Guidelines + TDD-Pflicht).
     Den Schicht-Subagenten können dabei auch ⚠️-Improvements aus dieser Runde mitgegeben
     werden, damit er sie optional mit adressiert. Nach Fixes → nächste Runde.
   - ⚠️ Improvement → notieren; nach einer 0-❌-Runde Entscheidung dem User vorlegen.
   - Suppression-Findings → direkt entscheiden: Begründung ausreichend oder Schicht-Subagent.

3. **Terminierung:**
   - a) 0 ❌ in einer Runde → Schritt 5 abgeschlossen.
   - b) Nach 3 Runden ohne 0-❌-Runde → STOP, User fragen.

Haupt-Thread entscheidet über verbleibende ⚠️-Findings vor Schritt 6.

── SCHRITT 6: COMMIT & SESSION-ABSCHLUSS ───────────────────────────────────
→ TaskUpdate "Schritt 5: Review-Loop": completed | TaskUpdate "Schritt 6: Commit & Session-Abschluss": in_progress

1. **Commit erstellen** (kein Amend):
   ```
   git commit -m "$(cat <<'EOF'
   US-XXX: [Szenario-Titel]

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```
   Mapping aus `$ARGUMENTS`: Tag `@US-904-happy-path` → Präfix `US-904` (@ und Suffix ab zweitem Bindestrich entfernen); Titel in Anführungszeichen direkt übernehmen.
   Beispiel: `$ARGUMENTS = @US-904-happy-path "Neue Zutat anlegen"` → `"US-904: Neue Zutat anlegen"`
   Co-Authored-By: Modellname aus dem System-Kontext der aktuellen Session einsetzen.

2. **Session-Abschluss anbieten** – frage den User:
   > „Szenario abgeschlossen. Soll ich die Session jetzt schließen (`closing-session`)?"

   Antwort abwarten:
   - **Ja** → `closing-session`-Skill laden und ausführen.
   - **Nein / später** → nur `docs/AGENT_MEMORY.md` aktualisieren (Phase-Zeile:
     Szenario als abgeschlossen markieren, nächstes benennen; Technische Schuld + Offene
     Fragen aktualisieren).

→ TaskUpdate "Schritt 6: Commit & Session-Abschluss": completed
