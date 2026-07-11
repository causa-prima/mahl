---
name: implementing-scenario
description: >
  Implementiert einen freigegebenen Szenario-Lauf (ein oder mehrere Gherkin-Szenarien desselben
  Clusters) end-to-end: Architektur-Check, Double-Loop TDD mit Subagenten pro Schicht,
  Orchestrator-Check, Review-Loop und Commit. Voraussetzung: der Lauf muss bereits via
  /gherkin-workshop (Schritt 6: Szenario-Clustering) freigegeben sein – fehlt er in features/,
  stoppt der Skill sofort. Verwende diesen Skill immer wenn ein @US-NNN-Lauf implementiert werden
  soll. Typische Trigger: „implementiere Lauf X", „fang mit dem ersten Lauf an", „nächster Lauf",
  „happy-path implementieren", direkter Aufruf via /implementing-scenario.
user-invocable: true
---

# Lauf implementieren

Implementiere Lauf $ARGUMENTS.
Fehlen `$ARGUMENTS` → User nach Story-Tag (`@US-NNN`) und Lauf-Nummer (`run-N`) fragen, bevor weitergegangen wird.

Aufruf: `/implementing-scenario @US-NNN run-N`
Beispiel: `/implementing-scenario @US-904 run-3`

Ein Lauf bündelt einen oder mehrere Szenarien desselben Clusters (Algorithmus + Tag-Format:
`.claude/skills/gherkin-workshop/references/scenario-clustering.md`). Ein Singleton-Lauf enthält
genau ein Szenario – der restliche Ablauf ist identisch, nur ohne Mehrfach-Parametrisierung.

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
Test ohne vorangehende Domain-Typen nicht schreibbar ist (zirkuläre Abhängigkeit).

Lege folgende Task-Liste an (Regeln: `docs/process/task-system.md`):
```
TaskCreate: "Schritt 0: Architektur-Check"
TaskCreate: "Schritt 1–3: TDD-Zyklus (Double-Loop)"
TaskCreate: "Schritt 4: Orchestrator-Check"
TaskCreate: "Schritt 5: Review-Loop"
TaskCreate: "Schritt 6: Abschluss (Session-Abschluss & Commit)"
```

── SCHRITT 0: ARCHITEKTUR-CHECK ─────────────────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": in_progress

Beantworte diese Fragen schriftlich, bevor der erste Test geschrieben wird.
Der Schritt ist wichtig, weil nachträgliche Architekturentscheidungen teuer sind –
einmal Code da, ist die Versuchung groß, die Entscheidung an den Code anzupassen statt umgekehrt.

**Gezielt lesen, nicht full-read:**
- Akzeptanzkriterien: `docs/stories/szenario_N_*.md` (N = US-Präfix, z.B. US-904 → szenario_9_datenpflege.md; Mapping-Tabelle: `docs/stories/user-stories.md`)
- Architektur-Patterns: `docs/reference/architecture.md` – TOC lesen, dann nur relevante Sektionen
- Phasen-Spec: Phase aus `docs/AGENT_MEMORY.md` → `docs/reference/skeleton-spec.md` oder `docs/reference/mvp-spec.md` (nur API+DB-Sektion der Story)
- Feature-Datei: `features/<story>.feature` – nur die Szenarien des Laufs `$ARGUMENTS` vollständig lesen

Fragen:

1. **ATDD-Gate:** Lauf `$ARGUMENTS` in `features/` vorhanden?
   ```
   python3 .claude/scripts/check-atdd-gate.py <STORY-TAG> <run-N>
   ```
   Beispiel: `python3 .claude/scripts/check-atdd-gate.py @US-904 run-3`
   - Exit 1? → STOP. Erst `gherkin-workshop` (inkl. Schritt 6: Szenario-Clustering) für
     die User Story ausführen, dann zurückkommen. Ohne freigegebenen und geclusterten
     Szenario-Satz fehlt die objektive Fertigstellungsbedingung – der Code kann nicht als
     "Done" gelten.
   - Exit 0: Der Script-Output enthält Background + Given/When/Then **aller** Szenarien
     des Laufs (Lauf-Label, Schicht, Singleton-Flag im Kopf) – das ist die exakte Spec für
     den gesamten Lauf. Bei einem Frontend-only-Lauf (Schicht-Label im Output) entfällt
     der Backend-Subagent in Schritt 1–3 vollständig.
   - **Sibling-Läufe überfliegen (Titel, keine Details):** `python3 .claude/scripts/next_run.py --open --story <US-NNN>` zeigt nur für diese Story alle noch **offenen** Lauf-Labels **mit Szenario-Titeln** – mechanisch, günstig, ohne Given/When/Then anderer Läufe lesen zu müssen (das widerspräche der Lese-Sparsamkeits-Regel oben) und ohne Rauschen aus anderen Storys/NFR-Features. Bewusst nur `--open`: ein bereits `--done`-Lauf hat seine Capability schon gebaut, dort gibt es nichts vorwegzunehmen. Dient ausschließlich Punkt 2.
2. **YAGNI/KISS-Scope:** Was ist das Minimal-Notwendige für genau diese Szenarien des Laufs?
   Was wäre Gold-Plating (= kein Test dafür existiert, kein Akzeptanzkriterium fordert es)?
   Notiere explizit: *"Folgendes implementiere ich NICHT: ..."*
   Deutet ein **späterer** Sibling-Lauf (Titel aus der Übersicht oben) erkennbar auf dieselbe
   UI-Fläche/denselben Endpoint hin, den der aktuelle Lauf bereits berührt (z.B. der aktuelle
   Lauf zeigt schon Daten in einer Liste, ein späterer Szenario-Titel spricht von Sortierung/
   Leerzustand/Filterung derselben Liste) → dessen Capability **explizit** in die NICHT-Liste
   aufnehmen, mit Verweis auf den Sibling-Lauf (z.B. *„NICHT: Sortierung, Leerzustand-Hinweis,
   Soft-Delete-Filterung (→ run-7 „Mehrere Zutaten erscheinen alphabetisch sortiert" u.a.);
   Anzeige des gerade angelegten Items aber JA"*). Macht die YAGNI-Grenze auditierbar statt vom
   Zufall abhängig, ob der Implementer sie selbst errät.

3. **Domain-Typen & Architektur:** Brauche ich neue Domain-Typen? Falls ja: grob skizzieren (welche Konzepte, welche Schicht). Konkrete Typ-Entscheidungen (Struktur, Fehler-Modellierung, Sichtbarkeit) fallen im TDD-Zyklus – der Layer-Implementer liest dafür die Coding-Guidelines.

4. **ADR-Check:** Berühren die Szenarien des Laufs eine bestehende Entscheidung?

   `decisions.py`-Kurzreferenz:
   - `list --tag X` → Header-Zeile + Tags aller passenden ADRs (kompakt, zum Scannen)
   - `list --tag X --full` → vollständiger Text jeder ADR inkl. Beschreibung + verworfene Alternativen
   - `get ID1 ID2 ...` → vollständiger Text für konkrete IDs
   - `tags` → Übersicht aller Tag-Kategorien
   - `refs` → listet alle `// ADR-SXXX-N`-Kommentare im Code und prüft ob die referenzierten ADRs existieren

   Mechanische Suche (Ergebnisse vollständig in die Subagenten-Message):
   ```
   python3 .claude/scripts/decisions.py list --tag scope:cross-cutting --full
   python3 .claude/scripts/decisions.py list --tag story:us-NNN --full    # NNN aus $ARGUMENTS, z.B. story:us-904
   ```

   Eigene Bewertung – intern festhalten, Subagent macht diese unabhängig:
   ```
   python3 .claude/scripts/decisions.py tags                              # Überblick Tag-Kategorien
   python3 .claude/scripts/decisions.py list --tag resource:<X>           # relevante Kategorien listen
   python3 .claude/scripts/decisions.py get ADR-SXXX-N ADR-SYYY-M ...    # potentiell relevante vollständig lesen
   # Entscheiden welche davon relevant sind
   ```

   Falls neue Architekturentscheidung nötig: User fragen. Selbst Entschiedenes in `docs/history/adr.md` dokumentieren.
   Mechanische-Suche-Ergebnisse (`--full`) inklusive der verwendeten Befehle in die Subagenten-Message aufnehmen.

5. **TD-Sichtung & -Entscheidung:** Sieh in `docs/tech-debt.md` nach technischer Schuld, die die von diesem Lauf berührten Code-Bereiche/Dateien betrifft (aus Punkt 2–4: welcher Endpoint/welche UI-Fläche/welche Domain-Typen). Für **jeden** so getroffenen TD-Eintrag *vor* der Umsetzung entscheiden **und schriftlich begründen**:
   - **Mit-erledigen** – nur wenn der Lauf den Code ohnehin anfasst *und* die Behebung kohäsiv + günstig ist (Boy-Scout-Regel, **kein** Gold-Plating; steht im Spannungsfeld zu Punkt 2 – im Zweifel aufschieben). Dann Scope + betroffene TD-ID notieren und im TDD-Zyklus mit umsetzen.
   - **Aufschieben** – mit **Grund** (außerhalb des berührten Codes / zu groß / eigener fokussierter Schritt nötig).

   Macht die TD-Mitnahme **bewusst und auditierbar** statt zufällig – verhindert beide Fehler: stilles Übergehen *und* ungebremstes Mitnehmen. TD **ohne** Bezug zu den berührten Bereichen bleibt bewusst außen vor (wird erst angefasst, wenn ein Lauf real dorthin kommt).

6. **Modell-Eignung je geplanter Schicht:** Die Komplexitätseinschätzung liegt nach Punkt 2–5 ohnehin vor (YAGNI-Scope, Domain-Typen, ADR-Berührung, TD-Mitnahme). Halte pro erwarteter Schicht fest, welches Modell genügt: **`sonnet` ist der Default** und trägt die normale schichtweise TDD-Arbeit. Im Zweifel beim `sonnet`-Default bleiben. Nur eine Schicht, die klar überdurchschnittlich anspruchsvoll ist (offener Entwurfsraum, mehrschichtig verschränkte Logik), gezielt auf Opus eskalieren (`model`-Parameter beim Spawn). Beim Spawn (Schritt 1–3) wird diese Vorab-Einschätzung nur noch bestätigt.

Schriftliche Antwort auf alle sechs Punkte.
Dieser Schritt ist reine Analyse – noch kein Produktionscode schreiben. Domain-Typen und
Implementierungsdetails entstehen im TDD-Zyklus, wenn Tests sie erzwingen.

── SCHRITT 1–3: TDD-ZYKLUS (DOUBLE-LOOP) ───────────────────────────────────
→ TaskUpdate "Schritt 0: Architektur-Check": completed | TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": in_progress

Ziel: genau die Szenarien des Laufs aus $ARGUMENTS vollständig grün bekommen – nicht mehr, nicht weniger.

**Vorabanalyse: Spec-Ambiguitäten klären (Haupt-Thread):**

Bevor die E2E-Tests geschrieben werden, alle Szenarien des Laufs auf offene Entscheidungen scannen – schichtübergreifend:
- **Verhaltensentscheidungen:** Was passiert nach einer Aktion? Dialog-Verhalten nach Erfolg/Fehler, Feldinitialisierung, Reihenfolge von Elementen, exakter Fehlermeldungstext.
- **Backend-Entscheidungen:** HTTP-Statuscodes, Header-Format (z.B. `Location`), DB-Schema-Details (Constraints, Datentypen, Default-Werte).

Gefundene Ambiguitäten mit dem User klären, bevor der E2E-Test entsteht.
Reine Design-Entscheidungen (CSS, Fonts, Abstände) sind kein Klärungsbedarf – diese liegen in den UX-Guidelines und brauchen keine Spec-Anpassung.

**Äußerer Loop – E2E-Test(s) (Haupt-Thread):**

Schreibe selbst die Playwright-Test(s) für **alle** Szenarien des Laufs (je Szenario Given/When/Then 1:1) – bevor der erste Subagent gespawnt wird. Ein homogener Cluster (gleiches Setup, gleiche Assertion-Form, nur der Input variiert – das ist per Definition des Clustering-Algorithmus der Regelfall) kollabiert dabei zu **einem** parametrisierten Test (`[TestCase]`/`test.each` o.ä.), jede Zeile = ein Szenario. Führe die Test(s) aus und zeige die Fehlermeldung(en). Das beweist, dass sie echtes Verhalten messen und noch nicht durch bestehende Implementierung zufällig grün werden können. Referenz: `docs/process/e2e-testing.md` (TOC zuerst).

Diese Tests bleiben rot, bis alle inneren Loops abgeschlossen sind – das ist gewollt. Der Haupt-Thread ändert sie während der inneren Loops nicht.

**Innerer Loop – Subagent pro Schicht (Delegation ist Pflicht):**

> **Voraussetzung:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` muss in den globalen Settings aktiv sein. Ohne dieses Feature schlägt `SendMessage` still fehl – der Prozess hängt ohne Fehlermeldung.

Für jede Schicht einen Subagenten spawnen. Haupt-Thread lädt KEINE Coding-Guidelines – der
Subagent tut das selbst.

**Schicht-Reihenfolge (outside-in):** Die Schicht des Laufs steht bereits im `# @run-N`-Tag
(Ausgabe von `check-atdd-gate.py` in Schritt 0) – kein erneutes Beurteilen pro Szenario nötig,
alle Szenarien eines Laufs teilen dieselbe Schicht (Konsequenz des Clustering-Algorithmus,
Achse „Schicht" in Schritt 4).
- **Full-Stack:** ein Frontend-Subagent implementiert beide Frontend-Schichten sequenziell (Komponente mit Service-Mock zuerst, dann Service-Client mit MSW) → danach ein Backend-Subagent *(Frontend zuerst: implementiert gegen MSW-Mocks; Backend ersetzt diese Mocks danach)*.
- **Frontend-only:** nur der Frontend-Subagent (Komponente mit Service-Mock, ohne Service-Client-Schicht) – **kein Backend-Subagent**. Backend-only-Läufe sind aktuell nicht vorgesehen.

**Schicht-Subagenten (EINE Schicht pro Aufruf, alle Szenarien des Laufs in einem Batch):**

- Backend-Schicht: `subagent_type: "backend-layer-implementer"`
- Frontend-Schicht: `subagent_type: "frontend-layer-implementer"`

Befülle die Message mit den konkreten Werten aus Schritt 0 – **für alle Szenarien des Laufs gemeinsam**:

```
Lauf: <run-N> „<Cluster-Label>" (<Schicht>[, Singleton])

Szenarien (Tag + Titel + Akzeptanzkriterien bleiben je Szenario zusammen – Grundlage
für die `// Szenario: <Titel>`-Traceability-Kommentare je Test):

<TAG> "<TITEL 1>"
<Given/When/Then von Szenario 1 aus Schritt 0>

<TAG> "<TITEL 2>"
<Given/When/Then von Szenario 2 aus Schritt 0>
...

Scope-Grenzen (nicht implementieren):
<YAGNI-Liste aus Schritt 0>

Failing E2E-Test(s): <Pfad(e) zur spec.ts>

Relevante ADRs:
Bereits ausgeführt (nicht nochmal ausführen):
  python3 .claude/scripts/decisions.py list --tag scope:cross-cutting --full
  python3 .claude/scripts/decisions.py list --tag story:us-NNN --full
<Vollständige Ausgabe beider Befehle – oder: "keine Treffer in [Befehl]">
```

Spawn-Regeln:
- EINE Schicht pro Subagent – keine Mehrfach-Schichten im selben Aufruf (sonst verschwimmt TDD-Disziplin). Ausnahme: der Frontend-Subagent implementiert Komponente und Service-Client sequenziell in einem Aufruf (siehe Schicht-Reihenfolge oben).
- **Modellwahl vor Spawn:** Die in Schritt 0 Punkt 5 festgehaltene Modell-Eignung bestätigen. Default ist `sonnet` (Frontmatter); nur eine klar überdurchschnittlich anspruchsvolle Schicht per `model`-Parameter auf Opus eskalieren. Im Zweifel beim `sonnet`-Default bleiben.
- **Subagent benennen:** `name: "backend-<schicht>"` bzw. `"frontend-<schicht>"` – nötig damit der Haupt-Thread via `SendMessage` für das Test-Review antworten kann.
- **KEIN `run_in_background: true`** – andernfalls werden Berechtigungsanfragen des Subagenten automatisch abgelehnt; er kann keine Dateien schreiben oder Befehle ausführen.
- **Subagent-Lebenszyklus:** Subagenten terminieren nach ihrer Ausgabe nicht – sie schlafen und bleiben via `SendMessage` erreichbar. Das ist das Kernverhalten von `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`. `permissionMode: acceptEdits` in den Subagenten-Definitionen stellt sicher, dass Datei-Edits nicht geblockt werden.
- **Arbeitende Subagenten nicht pollen:** Ein Subagent läuft im Hintergrund; der Harness meldet seinen *inhaltlichen* Abschluss automatisch (Test-Review-Signal, Verifikations-Hash-Block, Return). Idle-/„available"-Zwischensignale während der Arbeit (typisch während eines laufenden ~2-min-Stryker-Laufs) bedeuten **nicht** „fertig". Reagiere darauf **nicht** mit einer Status-Nachfrage per `SendMessage` („bist du fertig?", „wie ist der Stand?") – das pollt einen arbeitenden Subagenten, verschwendet Tokens und stört ihn. Warte auf den inhaltlichen Return; `SendMessage` dient der Beantwortung von PLANUNG-Rückfragen und der Findings-Übergabe, nicht dem Status-Abfragen.
- **PLANUNG-Phase beachten:** Der Subagent beginnt mit einem PLANUNG-Schritt, stellt Rückfragen und berichtet seine eigenständig gefundenen ADRs. Auf diese Ausgabe antworten:
  - **Rückfragen:** Alle Rückfragen in einer Antwort beantworten. Für jede Frage prüfen, ob sie bereits in Schritt 0 geklärt wurde – bekannte Antworten direkt einschließen (kurz vermerken: „aus Schritt 0 bekannt: [Antwort]"), offene Fragen gebündelt an den User weitergeben. Max. 2 Runden; danach dem Nutzer die Situation erklären (offene Fragen auflisten) und fragen wie weiter verfahren werden soll.
  - **ADR-Abgleich:** Findet der Subagent ADRs, die du nicht als relevant eingestuft hast (oder umgekehrt), kritisch prüfen ob sie tatsächlich anwendbar sind. Im Zweifelsfall mit dem Subagenten klären – dessen Begründungen aber ebenfalls kritisch hinterfragen, nicht blind übernehmen. Kein Konflikt: kein weiterer Austausch nötig.
  Erst nach dieser Antwort beginnt der Batch-RED-Zyklus.
- Haupt-Thread reviewt Diff und Test-Run-Output nach jedem Subagent-Return.
- **Suppressions-Politik korrekt formulieren:** Dem Subagenten nie „Ziel: NULL neue Suppressions" vorgeben – die Regel ist „keine *unbegründeten* Suppressions". Begründete (äquivalenter Mutant, strukturell unerreichbar, Fehlerpfad bewusst aufs treibende Szenario verschoben) sind erlaubt und werden in Schritt 4 validiert. Eine „null"-Vorgabe drängt den Subagenten, korrekten/guideline-vorgeschriebenen Code zu entfernen statt ihn begründet zu suppressen.
- Weicht der Subagent von TDD ab → an denselben Subagenten korrigieren (er wartet noch auf Test-Review). Max. 2 Iterationen; nach jeder Korrektur fordert der Subagent erneut Review an, bevor er zu GREEN übergeht. Nach 2 Iterationen ohne Verbesserung: Abbruch + Meldung an User.

**Batch-Test-Review nach RED im Inneren Loop (Haupt-Thread):**

Der Subagent schreibt den **gesamten Test-Batch der Schicht** (alle Tests, die die Szenarien des Laufs auf dieser Schicht fordern – bei einem homogenen Cluster typischerweise ein einziger parametrisierter Test), bestätigt den **kollektiven** Fehlschlag und sendet **einmal** das Signal `TEST-REVIEW: <Testname1, Testname2, ...>` mit allen Tests des Batches. Der Haupt-Thread liest den Test-Code via `git diff` (die Tests sind **nicht** gestaged; neue Dateien via `git diff --no-index /dev/null <datei>` oder direktes Lesen) und prüft den **ganzen Batch** anhand der folgenden Kriterien.

**Freigabe-Anker setzen (erst NACH inhaltlicher Freigabe):** Ist der Batch in Ordnung, friert der Haupt-Thread jede freigegebene Test-Datei als git-Blob ein und **merkt sich die `pfad=sha`-Paare** für Schritt 4:
```
git hash-object -w <test-datei-1> <test-datei-2> …    # gibt je Datei einen Blob-SHA aus
```
Gegen diesen Anker prüft Schritt 4, dass nach der Freigabe **nur Setup** (Mock-Handler, Testdaten), **keine Assertions** geändert wurden – auch wenn der Subagent die Tests selbst staged (der Blob hängt am Inhalt, nicht am Index). Wird der Batch **nicht** freigegeben: konkrete Korrektur-Anforderung, **kein** Blob. Setup-Änderungen nach Freigabe beschreibt der Subagent im Return; Schritt 4 zeigt sie als Diff.

- **Per-Assertion-Pflicht (inkl. Given/When):** Für jede neue oder geänderte Assertion und signifikante Given/When-Schritte: Welches Gherkin-Kriterium erzwingt sie? Falls keines vorhanden – drei Diagnosen, der Haupt-Thread entscheidet:
  - a) **Gold-Plating** → Subagent löscht Assertion und ggf. zugehörigen Produktionscode.
  - b) **User-facing Verhalten ohne Szenario** → User-Freigabe für neues Szenario einholen, erst dann implementieren.
  - c) **Technische API/Architektur-Entscheidung** → Test braucht `// ADR-SXXX-N`-Kommentar der auf den Eintrag in `docs/history/adr.md` verweist; Haupt-Thread verifiziert via `python3 .claude/scripts/decisions.py refs`.

- **Anpassungen an bestehenden Tests:** Was würde ohne diese Anpassung kaputtgehen, das nicht ohnehin durch andere Assertions auffiele? Keine Antwort → redundant (Diagnose a).

- **Full-State-Assertions:** Bei `BeEquivalentTo` / `toEqual` (C#) bzw. `toEqual` / `toMatchObject` (TypeScript): Sind alle Properties durch ein Gherkin-Kriterium gedeckt? Gibt es `Excluding(...)` oder Partial-Matches? → müssen mit Kommentar begründet sein; unchecked oder excluded Properties sind Gold-Plating-Signal für den Produktionscode.

- **Given/When-Struktur:** Neue Tests sollen durch `// Given`, `// When`, `// Then`-Kommentare gegliedert sein. Fehlen diese → Finding melden (nicht blockierend).

── SCHRITT 4: ORCHESTRATOR-CHECK ────────────────────────────────────────────
→ TaskUpdate "Schritt 1–3: TDD-Zyklus (Double-Loop)": completed | TaskUpdate "Schritt 4: Orchestrator-Check": in_progress

**E2E-Loop schließen:**

Playwright-Test erneut ausführen. Noch rot? Ursache identifizieren (Routing? API-Integration? Fehlende Verbindung zwischen Schichten):
- Ursache in bereits implementierter Schicht → an bestehenden Schicht-Subagenten übergeben.
- Ursache in noch nicht implementierter Schicht → neuer Schicht-Subagent.

**Mechanische Verifikation (Script):**

Der Subagent hat in seinem Return einen `=== VERIFIKATIONS-HASH ===`-Block aus einem **frischen** `qa-check.py`-Lauf geliefert. Verifiziere ihn mechanisch – das Script führt **keinen** neuen Stryker-Lauf aus und meldet pass/fail. Übergib dabei die im Test-Review gemerkten Freigabe-Anker (`pfad=sha`-Paare aus Schritt 1–3) via `--approved-tests` – das ist bei geänderten Test-Dateien **Pflicht** (sonst bricht qa-check ab):
```
python3 .claude/scripts/qa-check.py --layer backend  --verify <hash-aus-return> --approved-tests <pfad1=sha1> <pfad2=sha2> …
python3 .claude/scripts/qa-check.py --layer frontend --verify <hash-aus-return> --approved-tests <pfad1=sha1> <pfad2=sha2> …
```

- `✅` (Exit 0) → Hash stimmt überein UND Score == 100 % → frischer, gültiger Übergabe-Lauf, mechanische Findings vertrauenswürdig.
- `❌` (Exit 1) → entweder Hash-Mismatch (kein frischer Lauf / Zustand geändert) oder Score < 100 %. In beiden Fällen Subagent auffordern, das Problem zu beheben und `qa-check.py` erneut auszuführen. Bleibt es nach einem Retry rot → STOP, User fragen.

> **Wichtig:** Der Subagent muss `qa-check.py` zur Übergabe **ohne** `--skip-stryker` laufen lassen – nur ein frischer Lauf erzeugt einen gültigen Übergabe-Hash (mit `--skip-stryker` wird kein Hash ausgegeben). `--skip-stryker` ist reiner Diagnose-Modus für den Orchestrator, nie die Übergabe. Den Subagenten NICHT anweisen, `--skip-stryker` zu nutzen.

`--verify`/`--skip-stryker` geben zusätzlich den vollständigen Check-Block aus (auch bei zu niedrigem Score – qa-check bricht nicht mehr früh ab, sondern zeigt alle Checks und gated am Ende per Exit-Code).

Der Script-Output enthält: geänderte Test-Dateien (Check 1), neue Suppressionen (Check 2),
Unit-Test-Muster (Check 3), ESLint-Status (Check 4, Frontend),
Test-Struktur/Given-When-Then (Check 5), Stryker-Score sowie den **TEST-FREIGABE-AUDIT**.

**Inhaltliche Bewertung (Haupt-Thread):**

1. **Test-Freigabe-Audit:** Der `=== TEST-FREIGABE-AUDIT ===`-Block vergleicht jede geänderte
   Test-Datei gegen ihren Freigabe-Anker. `✅ unverändert` → ok. Meldet er eine Datei als
   `GEÄNDERT` (mit Diff freigegeben→aktuell) oder `KEINE Freigabe-SHA`, den gezeigten Diff prüfen:
   nur Setup (Mock-Handler, Testdaten) → erlaubt; Assertion-Änderung oder nie freigegebene
   Test-Datei → ❌ zurück an den Schicht-Subagenten. (Kein Exit-Gate – nur der Haupt-Thread kann
   Setup ≠ Assertion entscheiden.)

2. **Suppression-Validität:** Für jede Suppression aus Check 2: Beweist die Begründung
   echte Äquivalenz / Nichttestbarkeit, oder klingt sie nur plausibel? (Maßstab:
   `docs/kaizen/principles.md`).

3. **Stryker-Score & Survivor-Fix:** Score aus Script-Output lesen. Score < 100 % → je Survivor:
   - Äquivalenter Mutant → als Suppression anlegen (Begründung Pflicht).
   - Gold-Plating (kein Gherkin-Kriterium erzwingt die Logik) → Produktionscode löschen.
   - Fehlender Test (Survivor beobachtbar – Backend: via HTTP, Frontend: via Komponenten-API) → an bestehenden Schicht-Subagenten.
   - Survivor **nicht** beobachtbar (Backend: nicht via HTTP, Frontend: nicht via Komponenten-API) – typisch für technisch erzwungene Zweige die nie ausgelöst werden können (z.B. exhaustiver `default`-Case über ein geschlossenes Sum-Type) → an bestehenden Schicht-Subagenten: Suppression anlegen lassen (Begründung Pflicht). Der Subagent hätte das bereits vor der Übergabe beheben müssen; 100 %-Score ist Voraussetzung für den Return.
   Score nach Fix immer noch < 100 % → als `lessons_learned` dokumentieren.

4. **Unit-Test-Autorisierung:** Für jeden Treffer aus Check 3: Wurde dieser Test explizit
   vom Orchestrator beauftragt (Stryker-Survivor-Check, Survivor nicht via Schicht-Grenze beobachtbar)?
   Nein → ❌ Gold-Plating.

**Findings übergeben:** Alle Findings werden **gesammelt** an den jeweiligen Schicht-Subagenten
übergeben – mit der Bitte um Korrektur oder, falls der Subagent gute Gegenargumente hat, um
Begründung. Der Subagent hat den vollständigen Implementierungskontext und kann echte
Gegenpositionen einbringen. Der Haupt-Thread entscheidet nach der Antwort ob die Begründung
trägt – Subagenten-Argumente dabei kritisch hinterfragen, nicht blind übernehmen. Nach
umgesetzten Korrekturen führt der Subagent `qa-check.py` erneut aus und liefert einen
aktualisierten `=== VERIFIKATIONS-HASH ===`-Block.

── SCHRITT 5: REVIEW-LOOP ───────────────────────────────────────────────────
→ TaskUpdate "Schritt 4: Orchestrator-Check": completed | TaskUpdate "Schritt 5: Review-Loop": in_progress

Review-Runden mit frischen Agenten pro Runde. Max. 3 Runden.

**Pro Runde:**

1. `.claude/skills/review-code/SKILL.md` laden und den darin beschriebenen Prozess ausführen.
   Eingaben übergeben: Szenario-Tags + Given/When/Then aller Szenarien des Laufs (aus Schritt 0), YAGNI-Liste (aus Schritt 0), geänderte Dateien (git diff), Check-2-Output (Suppressionen) aus dem Schritt-4-qa-check, gemeinsam ermittelte ADRs (Schritt 0 + Subagenten-PLANUNG).
   Keine neue Task-Liste anlegen – review-code läuft eingebettet in den implementing-scenario-Ablauf.
   Die von review-code gespawnten spezialisierten Agenten erhalten **kein Iterations-Wissen** –
   weder Findings aus früheren Runden noch Hinweise auf bereits abgelehnte false positives.

2. Findings im **Haupt-Thread** auswerten:
   - ❌ Must Fix → neuen Schicht-Subagenten spawnen (mit Coding-Guidelines + TDD-Pflicht).
     Diesem können auch ⚠️-Improvements aus dieser Runde mitgegeben werden, damit er sie
     optional mit adressiert. Nach Fixes → nächste Runde.
   - ⚠️ Improvement → notieren; nach einer 0-❌-Runde Entscheidung dem User vorlegen.
   - Suppression-Findings → direkt entscheiden: Begründung ausreichend oder Schicht-Subagent.

3. **Terminierung:**
   - a) 0 ❌ in einer Runde → Schritt 5 abgeschlossen.
   - b) Nach 3 Runden ohne 0-❌-Runde → STOP, User fragen.

Haupt-Thread entscheidet über verbleibende ⚠️-Findings vor Schritt 6.

── SCHRITT 6: ABSCHLUSS (SESSION-ABSCHLUSS & COMMIT) ───────────────────────
→ TaskUpdate "Schritt 5: Review-Loop": completed | TaskUpdate "Schritt 6: Abschluss (Session-Abschluss & Commit)": in_progress

1. **Offene Punkte mit dem User triagieren (bevor committed wird):** Sammle aus dem gesamten Ablauf alles, was nicht in den Szenario-Code eingeflossen ist – nichts darf nur in der Konversation hängen bleiben oder ungefragt irgendwo eingetragen werden:
   - **Improvement-Vorschläge aus den Subagenten-Returns** (Schicht-Implementer melden am Ende einen „Prozessverbesserung"-/Vorschlags-Abschnitt) – jeden Return durchsehen und **pro Subagent explizit ausweisen**, ob er Feedback gab (Inhalt) oder nicht („keine"). Wird daraus ein OBS/LL erfasst, die **Quelle präzise** eintragen (`Subagent` vs. `Orchestrator`), damit später beobachtbar bleibt, woher das Feedback stammt.
   - **Zurückgestellte ⚠️-Findings** aus dem Review-Loop (Schritt 5).
   - **Während des Ablaufs entdeckte technische Schuld / Tooling-Reibung.**
   - **TD-Abgleich:** Prüfe, ob ein bestehender `docs/tech-debt.md`-Eintrag durch diesen Lauf behoben wurde – bewusst mit-erledigt (Schritt 0, Punkt 5) **oder** unbewusst nebenbei → den Eintrag schließen. Verhindert, dass `tech-debt.md` längst erledigte Posten weiterschleppt.

   Lege dem User **jeden** Punkt vor – mit genug **Kontext** zum Entscheiden und einer **begründeten Empfehlung**. Der User entscheidet pro Punkt:
   1. **Direkt umsetzen** → jetzt erledigen (ggf. eigener TDD-Zyklus / Schicht-Subagent).
   2. **Vermerken** → in das passende Dokument bzw. die passenden Dokumente eintragen. Welches Dokument wofür zuständig ist, steht in der `CLAUDE.md`-Navigationstabelle (single source of truth – hier bewusst NICHT dupliziert, damit nichts driftet).
   3. **Ignorieren** → bewusst verwerfen.

   Erst eintragen/umsetzen, NACHDEM der User entschieden hat. Kein stilles Eintragen, kein stilles Vergessen.

   **Doppel-Erfassung vermeiden:** Folgt direkt ein Session-Abschluss (Schritt 6.3 → `closing-session`), besitzt dieser die *Aufnahme* der Beobachtungen/Learnings (dortiger Schritt 2/5). Dann hier nur **surfacen + triagieren** und „direkt umsetzen"-Punkte **vor dem Commit** erledigen; die als „vermerken" entschiedenen LL/OBS **im `closing-session`-Lauf gebündelt schreiben** – nicht jetzt schreiben und dort erneut abfragen. Läuft die Session **ohne** Abschluss weiter (Szenario fertig, kein `closing-session`), hier vermerken.

2. **Vorgehen mit dem User klären** – frage per `AskUserQuestion`, was als nächstes passieren soll, damit der Commit i.d.R. die Session-Abschluss-Dateien mit enthält. Optionen:
   - **Session-Abschluss, dann Commit** (Empfehlung) → erst `closing-session` ausführen, dann committen, sodass die Session-Abschluss-Dateien (Session-Log, AGENT_MEMORY-Phasenzeile, `lessons_learned`, Index) im **selben** Commit liegen.
   - **Nur Session-Abschluss** → `closing-session` ausführen, **kein** Commit.
   - **Nur Commit** → jetzt committen, ohne Session-Abschluss; davor `docs/AGENT_MEMORY.md` selbst aktualisieren (Phase/Story/**Nächster Lauf**: erledigten Lauf markieren, nächsten benennen); technische Schuld → `docs/tech-debt.md`, offene Fragen → `docs/open-questions.md`.
   - **Etwas anderes** (Freitext) → der Anweisung des Users folgen.

3. **Session-Abschluss** (falls gewählt): `closing-session`-Skill laden und ausführen. Die dort entstandenen/geänderten Dateien fließen in den nachfolgenden Commit ein.

4. **Commit erstellen** (falls gewählt; kein Amend): Der Agent committet selbst. `git commit` steht auf Auto-Deny (PreToolUse-Hook) → mit angehängtem `# --allow-once` ausführen (einmalige User-Freigabe).
   `git status` prüfen – alle noch unstaged Änderungen stagen (`git add <dateien>`), **inklusive** der Dateien aus dem Session-Abschluss.
   ```
   git commit -m "$(cat <<'EOF'
   US-XXX: Lauf N – [Cluster-Label]

   Co-Authored-By: <MODELLNAME> <noreply@anthropic.com>
   EOF
   )"  # --allow-once
   ```
   Mapping: Story-Tag ohne `@`, Lauf-Nummer und Cluster-Label aus dem `check-atdd-gate.py`-Output
   von Schritt 0 übernehmen.
   Beispiel: `$ARGUMENTS = @US-904 run-3` (Label „Anlegen·Name-Validierung") → `"US-904: Lauf 3 – Anlegen·Name-Validierung"`
   Co-Authored-By: Modellname aus dem System-Kontext einsetzen.

→ TaskUpdate "Schritt 6: Abschluss (Session-Abschluss & Commit)": completed
