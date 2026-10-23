---
name: implementing-scenario
description: >
  Implementiert einen freigegebenen Szenario-Lauf (ein oder mehrere Gherkin-Szenarien desselben
  Clusters) end-to-end: Architektur-Check, Double-Loop TDD mit Subagenten pro Schicht,
  Orchestrator-Check, Review-Loop und Abschluss-Triage. Voraussetzung: der Lauf muss bereits via
  /gherkin-workshop (Szenario-Clustering) freigegeben sein – fehlt er in features/,
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

**Ablauf** – in dieser Reihenfolge:

1. [Architektur-Check](#IMP-architektur-check)
2. [TDD-Zyklus](#IMP-tdd-zyklus) (Double-Loop, je Schicht ein Subagent)
3. [Orchestrator-Check](#IMP-orchestrator-check)
4. [Review-Loop](#IMP-review-loop)
5. [Abschluss](#IMP-abschluss) (Triage, dann Session-Abschluss oder nächster Lauf)

Zwei Ausführungsregeln gelten für den gesamten Ablauf:
- Dateien > 100 Zeilen in der Regel nicht komplett lesen: TOC zuerst (Read mit `limit: 30`), dann gezielt per `grep` oder `Read offset/limit`. Ausnahme: muss ein spezifischer, abgrenzbarer Abschnitt vollständig erfasst werden (z.B. ein einzelnes Gherkin-Szenario), darf dieser komplett gelesen werden.
- Implementierungsarbeit ([TDD-Zyklus](#IMP-tdd-zyklus)) und Reviews ([Review-Loop](#IMP-review-loop)) an Subagenten delegieren – der Haupt-Thread orchestriert.

GRUNDSATZ: Die Regeln sind starke Guidelines, keine absoluten Gesetze. Gibt es sehr gute Gründe
abzuweichen: sofort kommunizieren und auf Bestätigung warten. Ein guter Grund liegt vor, wenn
das strikte Befolgen einer Regel nachweislich zu schlechterem Ergebnis führt – z.B. wenn ein
Test ohne vorangehende Domain-Typen nicht schreibbar ist (zirkuläre Abhängigkeit).

<a id="IMP-architektur-check"></a>
## Architektur-Check

Beantworte alle Fragen dieses Abschnitts schriftlich, bevor der erste Test geschrieben wird.
Der Schritt ist wichtig, weil nachträgliche Architekturentscheidungen teuer sind –
einmal Code da, ist die Versuchung groß, die Entscheidung an den Code anzupassen statt umgekehrt.
Er ist reine Analyse – noch kein Produktionscode schreiben. Domain-Typen und
Implementierungsdetails entstehen im TDD-Zyklus, wenn Tests sie erzwingen.

**Gezielt lesen, nicht full-read** (Abrufwege: Navigationstabelle in `AGENTS.md`):
- Akzeptanzkriterien: `docs/stories/szenario_N_*.md` (N = US-Präfix, z.B. US-904 → szenario_9_datenpflege.md; Mapping-Tabelle: `docs/stories/user-stories.md`)
- Architektur-Patterns: `docs/reference/architecture.md` – Abschnittsliste holen, dann nur die relevanten Abschnitte
- Phasen-Spec: Phase aus `docs/AGENT_MEMORY.md` → `docs/reference/skeleton-spec.md` oder `docs/reference/mvp-spec.md` (nur API+DB-Sektion der Story)
- Feature-Datei: die Datei mit dem Feature-Tag der Story (`grep -l '@US-NNN' features/`) – nur die Szenarien des Laufs `$ARGUMENTS` vollständig lesen

Fragen:

1. **ATDD-Gate:** Lauf `$ARGUMENTS` in `features/` vorhanden?
   ```
   python3 -m prozesscode.check-atdd-gate <STORY-TAG> <run-N>
   ```
   Beispiel: `python3 -m prozesscode.check-atdd-gate @US-904 run-3`
   - Exit 1? → STOP. Erst `gherkin-workshop` (inkl. [Szenario-Clustering](../gherkin-workshop/SKILL.md#GHW-szenario-clustering)) für
     die User Story ausführen, dann zurückkommen. Ohne freigegebenen und geclusterten
     Szenario-Satz fehlt die objektive Fertigstellungsbedingung – der Code kann nicht als
     "Done" gelten.
   - Exit 0: Der Script-Output enthält Background + Given/When/Then **aller** Szenarien
     des Laufs (Lauf-Label, Schicht, Singleton-Flag im Kopf) – das ist die exakte Spec für
     den gesamten Lauf. Bei einem Frontend-only-Lauf (Schicht-Label im Output) entfällt
     der Backend-Subagent in [TDD-Zyklus](#IMP-tdd-zyklus) vollständig.
   - **Sibling-Läufe überfliegen (Titel, keine Details):** `python3 -m prozesscode.next_run --open --story <US-NNN>` zeigt nur für diese Story alle noch **offenen** Lauf-Labels **mit Szenario-Titeln** – mechanisch, günstig, ohne Given/When/Then anderer Läufe lesen zu müssen (das widerspräche der Lese-Sparsamkeits-Regel oben) und ohne Rauschen aus anderen Storys/NFR-Features. Bewusst nur `--open`: ein bereits `--done`-Lauf hat seine Capability schon gebaut, dort gibt es nichts vorwegzunehmen. Dient ausschließlich [YAGNI/KISS-Scope](#IMP-yagni-scope).
2. <a id="IMP-yagni-scope"></a>**YAGNI/KISS-Scope:** Was ist das Minimal-Notwendige für genau diese Szenarien des Laufs?
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

4. <a id="IMP-adr-check"></a>**ADR-Check:** Berühren die Szenarien des Laufs eine bestehende Entscheidung?

   `decisions.py`-Kurzreferenz:
   - `list --tag X` → Header-Zeile + Tags aller passenden ADRs (kompakt, zum Scannen)
   - `list --tag X --full` → vollständiger Text jeder ADR inkl. Beschreibung + verworfene Alternativen
   - `get ID1 ID2 ...` → vollständiger Text für konkrete IDs
   - `tags` → Übersicht aller Tag-Kategorien
   - `refs` → listet alle `// ADR-SXXX-N`-Kommentare im Code und prüft ob die referenzierten ADRs existieren

   **`--full` nur auf einen Tag anwenden, der wirklich eingrenzt.** `scope:` tut das nicht – er
   trägt fast den ganzen Bestand und wächst mit ihm, während der pro Lauf relevante Anteil klein
   und ungefähr konstant bleibt. Trennschärfe liefern die fachlichen Dimensionen (`arch:`,
   `http:`, `frontend:`, `db:`, `resource:`); mehrere `--tag` schneiden sich, engen also weiter
   ein. Prüf im Zweifel erst kompakt, wie viele Treffer ein Filter liefert, bevor du `--full`
   darauf loslässt.

   Überblick verschaffen – kompakt, nur Kopfzeilen:
   ```
   python3 -m prozesscode.decisions tags                    # welche Dimensionen gibt es
   python3 -m prozesscode.decisions list --tag scope:cross-cutting
   python3 -m prozesscode.decisions list --tag story:us-NNN  # NNN aus $ARGUMENTS
   ```

   Vollständig lesen – nur die Kandidaten, gefiltert über die Dimensionen dieses Laufs:
   ```
   python3 -m prozesscode.decisions list --tag arch:<X> --tag http:<Y> --full
   python3 -m prozesscode.decisions get ADR-SXXX-N ADR-SYYY-M ...
   ```

   Falls neue Architekturentscheidung nötig: User fragen. Selbst Entschiedenes in `docs/history/adr.md` dokumentieren.

5. <a id="IMP-td-sichtung"></a>**TD-Sichtung & -Entscheidung:** Überfliege `python3 -m prozesscode.td list` (Titel nennen den Bereich) und hol Kandidaten mit `td get <ID>` – nicht die ganze `docs/tech-debt.md` lesen. Gesucht ist technische Schuld, die die von diesem Lauf berührten Code-Bereiche/Dateien betrifft (aus der bisherigen Analyse: welcher Endpoint/welche UI-Fläche/welche Domain-Typen). Für **jeden** so getroffenen TD-Eintrag *vor* der Umsetzung entscheiden **und schriftlich begründen**:
   - **Mit-erledigen** – nur wenn der Lauf den Code ohnehin anfasst *und* die Behebung kohäsiv + günstig ist (Boy-Scout-Regel, **kein** Gold-Plating; steht im Spannungsfeld zu [YAGNI/KISS-Scope](#IMP-yagni-scope) – im Zweifel aufschieben). Dann Scope + betroffene TD-ID notieren und im TDD-Zyklus mit umsetzen.
   - **Aufschieben** – mit **Grund** (außerhalb des berührten Codes / zu groß / eigener fokussierter Schritt nötig).

   Macht die TD-Mitnahme **bewusst und auditierbar** statt zufällig – verhindert beide Fehler: stilles Übergehen *und* ungebremstes Mitnehmen. TD **ohne** Bezug zu den berührten Bereichen bleibt bewusst außen vor (wird erst angefasst, wenn ein Lauf real dorthin kommt).

   **Teil dieses Laufs:** Was die Agenda unter „Nächster Lauf" so aufführt (TD, offene Frage oder Priorität mit `Szenario:`-Anker auf ein Szenario dieses Laufs), ist kein Fund der Sichtung, sondern dem Lauf **zugeordnet**. Für jeden dieser Einträge entscheidest du hier ausdrücklich: im Lauf erledigen (Schuld beheben, Frage mit dem User klären, Priorität abarbeiten) **oder** mit Begründung auf ein anderes Szenario bzw. eine andere Fälligkeit umhängen (`td.py set` / `oq.py set`). Stillschweigend liegen lassen ist keine Option. Bleibt er trotzdem liegen, meldet ihn die nächste Session als „beim Lauf nicht mitgenommen". Neu ausgeben lässt sich die Liste mit `python3 -m prozesscode.next_run --render docs/AGENT_MEMORY.md`.

   Legst du eine dieser Entscheidungen dem User vor, gilt sie **nie nur per ID**: Kurztitel und ein
   paar erklärende Sätze gehören dazu ([`principles.md`, Kommunikation](../../../docs/kaizen/principles.md#KPI-kommunikation)) – das gilt für ADR- wie für TD-Bezüge.

6. <a id="IMP-modell-eignung"></a>**Modell-Eignung je geplanter Schicht:** Die Komplexitätseinschätzung liegt nach den vorangegangenen Punkten ohnehin vor (YAGNI-Scope, Domain-Typen, ADR-Berührung, TD-Mitnahme). Halte pro erwarteter Schicht fest, welches Modell genügt: **`sonnet` ist der Default** und trägt die normale schichtweise TDD-Arbeit. Im Zweifel beim `sonnet`-Default bleiben. Nur eine Schicht, die klar überdurchschnittlich anspruchsvoll ist (offener Entwurfsraum, mehrschichtig verschränkte Logik), gezielt auf Opus eskalieren (`model`-Parameter beim Spawn). Beim Spawn ([TDD-Zyklus](#IMP-tdd-zyklus)) wird diese Vorab-Einschätzung nur noch bestätigt.

<a id="IMP-tdd-zyklus"></a>
## TDD-Zyklus (Double-Loop)

Ziel: genau die Szenarien des Laufs aus $ARGUMENTS vollständig grün bekommen – nicht mehr, nicht weniger.

### Vorabanalyse: Spec-Ambiguitäten klären (Haupt-Thread)

Bevor die E2E-Tests geschrieben werden, alle Szenarien des Laufs auf offene Entscheidungen scannen – schichtübergreifend:
- **Verhaltensentscheidungen:** Was passiert nach einer Aktion? Dialog-Verhalten nach Erfolg/Fehler, Feldinitialisierung, Reihenfolge von Elementen, exakter Fehlermeldungstext.
- **Backend-Entscheidungen:** HTTP-Statuscodes, Header-Format (z.B. `Location`), DB-Schema-Details (Constraints, Datentypen, Default-Werte).

Gefundene Ambiguitäten mit dem User klären, bevor der E2E-Test entsteht.
Reine Design-Entscheidungen (CSS, Fonts, Abstände) sind kein Klärungsbedarf – diese liegen in den UX-Guidelines und brauchen keine Spec-Anpassung.

<a id="IMP-ui-entwurf"></a>
### UI-Entwurf (nur bei Läufen mit Frontend-Anteil, Haupt-Thread)

Skizziere vor dem E2E-Test, wie
die Szenarien des Laufs auf dem Bildschirm aussehen – Elemente und Anordnung, MUI-Komponenten,
Zustände (leer, lädt, Fehler), Mobile-First. Maßstab sind der Nutzungskontext in der Beschreibung
unter `Feature:` (entsteht im Workshop, [Nutzungskontext & Ablauf](../gherkin-workshop/SKILL.md#GHW-nutzungskontext))
und die UX-Guideline. Führt der Lauf ein neues sichtbares Muster ein (neue Seite, neue Eingabeform,
neuer Komponententyp), lege die Skizze dem User vor, bevor der E2E-Test entsteht – ein ASCII-Mockup
genügt; Selektoren und Assertions des Tests hängen daran. Nutzt der Lauf nur bestehende Muster,
genügt ein Satz dazu. Verlangt die Skizze anderes **Verhalten**, als die Szenarien beschreiben, ist
das kein UI-Detail mehr: zurück in den Workshop, die Spec wird nicht in der Umsetzung angepasst.

<a id="IMP-aeusserer-loop"></a>
### Äußerer Loop – E2E-Test(s) (Haupt-Thread)

Schreibe selbst die Playwright-Test(s) für **alle** Szenarien des Laufs (je Szenario Given/When/Then 1:1) – bevor der erste Subagent gespawnt wird. Ein homogener Cluster (gleiches Setup, gleiche Assertion-Form, nur der Input variiert – das ist per Definition des Clustering-Algorithmus der Regelfall) kollabiert dabei zu **einem** parametrisierten Test (`[TestCase]`/`test.each` o.ä.), jede Zeile = ein Szenario. Führe die Test(s) aus und zeige die Fehlermeldung(en). Das beweist, dass sie echtes Verhalten messen und noch nicht durch bestehende Implementierung zufällig grün werden können. Referenz: `docs/process/e2e-testing.md` (TOC zuerst).

Diese Tests bleiben rot, bis alle inneren Loops abgeschlossen sind – das ist gewollt. Der Haupt-Thread ändert sie während der inneren Loops nicht.

<a id="IMP-innerer-loop"></a>
### Innerer Loop – Subagent pro Schicht (Delegation ist Pflicht)

> **Getestet mit** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in den globalen Settings (Harness-Test 2026-10-09, Claude Code 2.1.295). Laut Doku braucht `SendMessage` das Flag nicht; ohne Flag ist der Ablauf aber ungetestet – nicht abschalten, ohne den Test zu wiederholen.

Für jede Schicht einen Subagenten spawnen. Haupt-Thread lädt KEINE Coding-Guidelines – der
Subagent tut das selbst.

**Schicht-Reihenfolge (outside-in):** Die Schicht des Laufs steht bereits im `# @run-N`-Tag
(Ausgabe von `check-atdd-gate.py` in [Architektur-Check](#IMP-architektur-check)) – kein erneutes Beurteilen pro Szenario nötig,
alle Szenarien eines Laufs teilen dieselbe Schicht (Konsequenz des Clustering-Algorithmus,
Achse „Schicht" im [Schicht-Split](../gherkin-workshop/references/scenario-clustering.md#CLU-schicht-split)).
- **Full-Stack:** ein Frontend-Subagent implementiert Komponente und Service-Client, getestet über die Komponente mit MSW-Handlern → danach ein Backend-Subagent *(Frontend zuerst: implementiert gegen MSW; das Backend liefert danach das echte Verhalten)*.
- **Frontend-only:** nur der Frontend-Subagent (Komponente, kein neuer Service-Client) – **kein Backend-Subagent**. Backend-only-Läufe sind aktuell nicht vorgesehen.

**Schicht-Subagenten (eine Schicht pro Aufruf – Frontend zählt als eine –, alle Szenarien des Laufs in einem Batch):**

- Backend-Schicht: `subagent_type: "backend-layer-implementer"`
- Frontend-Schicht: `subagent_type: "frontend-layer-implementer"`

Befülle die Message mit den konkreten Werten aus [Architektur-Check](#IMP-architektur-check) – **für alle Szenarien des Laufs gemeinsam**:

```
Lauf: <run-N> „<Cluster-Label>" (<Schicht>[, Singleton])

Szenarien (Tag + Titel + Akzeptanzkriterien bleiben je Szenario zusammen – Grundlage
für die `// Szenario: <Titel>`-Traceability-Kommentare je Test):

<TAG> "<TITEL 1>"
<Given/When/Then von Szenario 1 aus dem Architektur-Check>

<TAG> "<TITEL 2>"
<Given/When/Then von Szenario 2 aus dem Architektur-Check>
...

Scope-Grenzen (nicht implementieren):
<YAGNI-Liste aus dem Architektur-Check>

Failing E2E-Test(s): <Pfad(e) zur spec.ts>

Relevante ADRs (von mir bewertet, Volltext – nicht nochmal abrufen):
<Vollständiger Text der ADRs, die du im Architektur-Check als relevant eingestuft hast – oder "keine">

Prüf das unabhängig nach; für deine Schicht einschlägig sind:
  python3 -m prozesscode.decisions list --tag <dimension>:<wert>   # kompakt, zum Scannen
  python3 -m prozesscode.decisions get ADR-SXXX-N                  # Volltext bei Bedarf
Findest du eine relevante ADR, die oben fehlt – oder hältst du eine der genannten für nicht
anwendbar –, sag das in deiner PLANUNG.
```
**Warum Volltext statt nur IDs:** Der Orchestrator hat diese ADRs in [Architektur-Check](#IMP-architektur-check) ohnehin
vollständig gelesen; sie in die Message zu schreiben kostet den Subagenten nicht mehr als sein
eigener `get`, spart aber einen Aufruf. Die Suchbefehle daneben sind kein Ersatz dafür, sondern
der Weg zur unabhängigen Gegenprobe: Eine zweite Meinung, die nur die Auswahl des Orchestrators
sieht, ist keine.

Spawn-Regeln:
- EINE Schicht pro Subagent – keine Mehrfach-Schichten im selben Aufruf (sonst verschwimmt TDD-Disziplin). Der Frontend-Subagent implementiert Komponente und Service-Client in einem Aufruf, weil beide vom selben Komponenten-Test getrieben werden (siehe Schicht-Reihenfolge oben).
- **Modellwahl vor Spawn:** Die im Architektur-Check unter [Modell-Eignung](#IMP-modell-eignung) festgehaltene Einschätzung bestätigen. Default ist `sonnet` (Frontmatter); nur eine klar überdurchschnittlich anspruchsvolle Schicht per `model`-Parameter auf Opus eskalieren. Im Zweifel beim `sonnet`-Default bleiben.
- **Subagent benennen:** `name: "backend-<schicht>"` bzw. `"frontend-<schicht>"` – nötig damit der Haupt-Thread via `SendMessage` für das Test-Review antworten kann.
- **Subagent-Lebenszyklus:** Subagenten laufen im Hintergrund. Rückfragen (PLANUNG), das Test-Review-Signal und den Return liefert ein Subagent, indem er seinen Lauf mit dieser Ausgabe beendet – sie kommt automatisch beim Orchestrator an. Der Orchestrator antwortet per `SendMessage`, und der Subagent macht mit vollem Kontext weiter. Seine Berechtigungsabfragen erscheinen beim User und werden nicht automatisch abgelehnt. `permissionMode: acceptEdits` in den Subagenten-Definitionen stellt sicher, dass Datei-Edits nicht geblockt werden. (Alles belegt im Harness-Test 2026-10-09.)
- **Wiederaufnehmen oder neu starten:** Lässt sich eine Folgeaufgabe gut ohne den bisherigen Kontext des Subagenten erledigen (z.B. ein eng umrissener Fix nach dem Review), starte einen **neuen** Subagenten mit knapper Übergabe (Szenario, freigegebene Tests samt Blob-Anker, Befund), statt den alten wieder aufzunehmen. Grund: Subagenten haben nur 5 Minuten Cache-Lebensdauer; nach einer längeren Pause wird ihr gesamtes Transkript neu in den Cache geschrieben (bis 2026-10 knapp die Hälfte aller Cache-Writes der Layer-Implementer, je 100–340k Tokens). Mitten im TDD-Ablauf (nach PLANUNG oder TEST-REVIEW) trägt der Kontext den Zustand – dort wieder aufnehmen.
- **Arbeitende Subagenten nicht pollen:** Auf den Bericht warten, keine Status-Nachfragen per `SendMessage` („bist du fertig?") – das verschwendet Tokens und stört. Kommt über längere Zeit kein Bericht (Absturz, Session-Limit), den Fortschritt **mechanisch am Arbeitsbaum** prüfen (`git status`, `git diff`, gezieltes `grep` auf die erwartete Änderung); ist die Arbeit erkennbar abgeschlossen, den Verifikationslauf (`qa-check.py`) selbst fahren, statt ihn nachzufordern.
- **PLANUNG-Phase beachten:** Der Subagent beginnt mit einem PLANUNG-Schritt, stellt Rückfragen und berichtet seine eigenständig gefundenen ADRs. Auf diese Ausgabe antworten:
  - **Rückfragen:** Alle Rückfragen in einer Antwort beantworten. Für jede Frage prüfen, ob sie bereits im [Architektur-Check](#IMP-architektur-check) geklärt wurde – bekannte Antworten direkt einschließen (kurz vermerken: „aus dem Architektur-Check bekannt: [Antwort]"), offene Fragen gebündelt an den User weitergeben. Max. 2 Runden; danach dem Nutzer die Situation erklären (offene Fragen auflisten) und fragen wie weiter verfahren werden soll.
  - **ADR-Abgleich:** Findet der Subagent ADRs, die du nicht als relevant eingestuft hast (oder umgekehrt), kritisch prüfen ob sie tatsächlich anwendbar sind. Im Zweifelsfall mit dem Subagenten klären – dessen Begründungen aber ebenfalls kritisch hinterfragen, nicht blind übernehmen. Kein Konflikt: kein weiterer Austausch nötig.
  Erst nach dieser Antwort beginnt der Batch-RED-Zyklus.
- Haupt-Thread reviewt Diff und Test-Run-Output nach jedem Subagent-Return.
- **Suppressions-Politik korrekt formulieren:** Dem Subagenten nie „Ziel: NULL neue Suppressions" vorgeben – eine „null"-Vorgabe drängt ihn, korrekten/guideline-vorgeschriebenen Code zu entfernen. Es gilt [Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung): Suppressionen mit Verweis auf eine erlaubende ADR (oder eine Einzelfall-Freigabe des Users) sind zulässig und werden in [Orchestrator-Check](#IMP-orchestrator-check) validiert.
- Weicht der Subagent von TDD ab → an denselben Subagenten korrigieren (er wartet noch auf Test-Review). Max. 2 Iterationen; nach jeder Korrektur fordert der Subagent erneut Review an, bevor er zu GREEN übergeht. Nach 2 Iterationen ohne Verbesserung: Abbruch + Meldung an User.

<a id="IMP-test-review"></a>
### Batch-Test-Review nach RED im Inneren Loop (Haupt-Thread)

Der Subagent schreibt den **gesamten Test-Batch der Schicht** (alle Tests, die die Szenarien des Laufs auf dieser Schicht fordern – bei einem homogenen Cluster typischerweise ein einziger parametrisierter Test), bestätigt den **kollektiven** Fehlschlag und sendet **einmal** das Signal `TEST-REVIEW: <Testname1, Testname2, ...>` mit allen Tests des Batches. Der Haupt-Thread liest den Test-Code via `git diff` (die Tests sind **nicht** gestaged; neue Dateien via `git diff --no-index /dev/null <datei>` oder direktes Lesen) und prüft den **ganzen Batch** anhand der folgenden Kriterien.

**Freigabe-Anker setzen (erst NACH inhaltlicher Freigabe):** Ist der Batch in Ordnung, friert der Haupt-Thread jede freigegebene Test-Datei als git-Blob ein und **merkt sich die `pfad=sha`-Paare** für [Orchestrator-Check](#IMP-orchestrator-check):
```
git hash-object -w <test-datei-1> <test-datei-2> …    # gibt je Datei einen Blob-SHA aus
```
Gegen diesen Anker prüft [Orchestrator-Check](#IMP-orchestrator-check), dass nach der Freigabe **nur Setup** (Mock-Handler, Testdaten), **keine Assertions** geändert wurden – auch wenn der Subagent die Tests selbst staged (der Blob hängt am Inhalt, nicht am Index). Wird der Batch **nicht** freigegeben: konkrete Korrektur-Anforderung, **kein** Blob. Setup-Änderungen nach Freigabe beschreibt der Subagent im Return; [Orchestrator-Check](#IMP-orchestrator-check) zeigt sie als Diff.

- **Per-Assertion-Pflicht (inkl. Given/When):** Für jede neue oder geänderte Assertion und signifikante Given/When-Schritte: Welches Gherkin-Kriterium erzwingt sie? Falls keines vorhanden – drei Diagnosen, der Haupt-Thread entscheidet:
  - a) **Gold-Plating** → Subagent löscht Assertion und ggf. zugehörigen Produktionscode.
  - b) **User-facing Verhalten ohne Szenario** → User-Freigabe für neues Szenario einholen, erst dann implementieren.
  - c) **Technische API/Architektur-Entscheidung** → Test braucht `// ADR-SXXX-N`-Kommentar der auf den Eintrag in `docs/history/adr.md` verweist; Haupt-Thread verifiziert via `python3 -m prozesscode.decisions refs`.

- **Anpassungen an bestehenden Tests:** Was würde ohne diese Anpassung kaputtgehen, das nicht ohnehin durch andere Assertions auffiele? Keine Antwort → redundant (Diagnose a).

- **Full-State-Assertions:** Bei `BeEquivalentTo` / `toEqual` (C#) bzw. `toEqual` / `toMatchObject` (TypeScript): Sind alle Properties durch ein Gherkin-Kriterium gedeckt? Gibt es `Excluding(...)` oder Partial-Matches? → müssen mit Kommentar begründet sein; unchecked oder excluded Properties sind Gold-Plating-Signal für den Produktionscode.

- **Given/When-Struktur:** Neue Tests sollen durch `// Given`, `// When`, `// Then`-Kommentare gegliedert sein. Fehlen diese → Finding melden (nicht blockierend).

<a id="IMP-orchestrator-check"></a>
## Orchestrator-Check

### E2E-Loop schließen

Playwright-Test erneut ausführen. Noch rot? Ursache identifizieren (Routing? API-Integration? Fehlende Verbindung zwischen Schichten):
- Ursache in bereits implementierter Schicht → an bestehenden Schicht-Subagenten übergeben.
- Ursache in noch nicht implementierter Schicht → neuer Schicht-Subagent.

**Mechanische Verifikation (Script):**

Der Subagent hat in seinem Return einen `=== VERIFIKATIONS-HASH ===`-Block aus einem **frischen** `qa-check.py`-Lauf geliefert. Verifiziere ihn mechanisch – das Script führt **keinen** neuen Stryker-Lauf aus und meldet pass/fail. Übergib dabei die im Test-Review gemerkten Freigabe-Anker (`pfad=sha`-Paare aus [TDD-Zyklus](#IMP-tdd-zyklus)) via `--approved-tests` – das ist bei geänderten Test-Dateien **Pflicht** (sonst bricht qa-check ab):
```
python3 -m prozesscode.qa-check --layer backend  --verify <hash-aus-return> --approved-tests <pfad1=sha1> <pfad2=sha2> …
python3 -m prozesscode.qa-check --layer frontend --verify <hash-aus-return> --approved-tests <pfad1=sha1> <pfad2=sha2> …
```

- `✅` (Exit 0) → Hash stimmt überein UND Score == 100 % → frischer, gültiger Übergabe-Lauf, mechanische Findings vertrauenswürdig.
- `❌` (Exit 1) → zwei Fälle, unterscheidbar am `=== VERIFY ===`-Block:
  - **Hash-Mismatch** (kein frischer Lauf / Zustand geändert) → Subagent auffordern, `qa-check.py` erneut auszuführen.
  - **Hash ✅, aber Score < 100 %** → Hat der Subagent jeden verbleibenden Survivor im Return nach [Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung) gemeldet (Datei:Zeile, Mutant, Tabellenzeile), ist das eine gültige Übergabe: weiter mit der Inhaltlichen Bewertung, dort Punkt „Stryker-Score & Survivor-Fix". Sonst Subagent auffordern, die Survivors zu behandeln.

  Bleibt es nach einem Retry aus anderem Grund rot → STOP, User fragen.

> **Wichtig:** Der Subagent muss `qa-check.py` zur Übergabe **ohne** `--skip-stryker` laufen lassen – nur ein frischer Lauf erzeugt einen gültigen Übergabe-Hash (mit `--skip-stryker` wird kein Hash ausgegeben). `--skip-stryker` ist reiner Diagnose-Modus für den Orchestrator, nie die Übergabe. Den Subagenten NICHT anweisen, `--skip-stryker` zu nutzen.

`--verify`/`--skip-stryker` geben zusätzlich den vollständigen Check-Block aus (auch bei zu niedrigem Score – qa-check bricht nicht mehr früh ab, sondern zeigt alle Checks und gated am Ende per Exit-Code).

Der Script-Output enthält je einen Check für geänderte Test-Dateien, neue Suppressionen,
Unit-Test-Muster, ESLint-Status (nur Frontend) und Test-Struktur/Given-When-Then,
dazu Stryker-Score sowie den **TEST-FREIGABE-AUDIT**.

**Inhaltliche Bewertung (Haupt-Thread):**

1. **Test-Freigabe-Audit:** Der `=== TEST-FREIGABE-AUDIT ===`-Block vergleicht jede geänderte
   Test-Datei gegen ihren Freigabe-Anker. `✅ unverändert` → ok. Meldet er eine Datei als
   `GEÄNDERT` (mit Diff freigegeben→aktuell) oder `KEINE Freigabe-SHA`, den gezeigten Diff prüfen:
   nur Setup (Mock-Handler, Testdaten) → erlaubt; ein **zusätzlicher** Test, den der Return als
   Survivor-Test nach der Freigabe ausweist ([Regel](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung)) → inhaltlich prüfen wie im [Test-Review](#IMP-test-review); Änderung bestehender
   Assertions, nicht ausgewiesener neuer Test oder nie freigegebene Test-Datei → ❌ zurück an den
   Schicht-Subagenten. (Kein Exit-Gate – nur der Haupt-Thread kann
   Setup ≠ Assertion entscheiden.)

2. **Suppression-Validität:** Für jede Suppression aus dem Check „Neue Suppressionen": Nennt die
   Begründung eine ADR, und deckt diese genau die Klasse des Falls – oder eine Einzelfall-Freigabe des
   Users aus diesem Lauf? Sonst ❌ bzw. dem User vorlegen, nach
   [Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung).

3. **Stryker-Score & Survivor-Fix:** Score aus Script-Output lesen. Score < 100 % oder vom Subagenten
   gemeldete Survivors → je Survivor nach [Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung)
   (dort auch, welche Fälle der User entscheidet). Bleibt der Score nach einer Korrekturrunde unter
   100 % → STOP, User fragen; zusätzlich als `lessons_learned` dokumentieren.

4. **Unit-Test-Autorisierung:** Für jeden Treffer aus dem Check „Unit-Test-Muster": Wurde dieser Test explizit
   vom Orchestrator beauftragt, nach Freigabe durch den User (Survivor nicht via Schicht-Grenze beobachtbar)?
   Nein → ❌ Gold-Plating.

**Findings übergeben:** Alle Findings werden **gesammelt** an den jeweiligen Schicht-Subagenten
übergeben – mit der Bitte um Korrektur oder, falls der Subagent gute Gegenargumente hat, um
Begründung. Der Subagent hat den vollständigen Implementierungskontext und kann echte
Gegenpositionen einbringen. Der Haupt-Thread entscheidet nach der Antwort ob die Begründung
trägt – Subagenten-Argumente dabei kritisch hinterfragen, nicht blind übernehmen. Nach
umgesetzten Korrekturen führt der Subagent `qa-check.py` erneut aus und liefert einen
aktualisierten `=== VERIFIKATIONS-HASH ===`-Block.

<a id="IMP-review-loop"></a>
## Review-Loop

Review-Runden mit frischen Agenten pro Runde. Max. 3 Runden.

**Pro Runde:**

1. `.claude/skills/review-code/SKILL.md` laden und den darin beschriebenen Prozess ausführen.
   Eingaben übergeben: Szenario-Tags + Given/When/Then aller Szenarien des Laufs (aus [Architektur-Check](#IMP-architektur-check)), YAGNI-Liste (aus [Architektur-Check](#IMP-architektur-check)), geänderte Dateien (git diff), Check-2-Output (Suppressionen) aus dem [Orchestrator-Check](#IMP-orchestrator-check)-qa-check, gemeinsam ermittelte ADRs ([Architektur-Check](#IMP-architektur-check) + Subagenten-PLANUNG).
   Die von review-code gespawnten spezialisierten Agenten erhalten **kein Iterations-Wissen** –
   weder Findings aus früheren Runden noch Hinweise auf bereits abgelehnte false positives.

2. Findings im **Haupt-Thread** umsetzen – ❌ und ⚠️ gleichermaßen, nach der Scope-Prüfung in
   `review-code` (spätere Phase → Abschluss-Triage; trivial → selbst, danach `qa-check`; alles andere →
   Schicht-Subagent mit Coding-Guidelines + TDD-Pflicht, Tendenz zu einem neuen). Mehrere Findings
   derselben Schicht gehen gebündelt an einen Subagenten. Nach Fixes → nächste Runde.
   - Suppression-Findings → nach [Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung).

   **Vor jedem Fix-Auftrag – Szenario-Frage (gilt für ❌ und ⚠️ gleichermaßen):** Ändert der Fix
   **beobachtbares Nutzerverhalten** (neue Reaktion auf eine Eingabe, geändertes Timing, ein
   zusätzlicher Guard), braucht er dasselbe Outside-In-Fundament wie geplante Funktionalität –
   erst Szenario, dann Test, dann Code. „Kommt aus einem Review-Finding" ist **kein**
   Ausnahmegrund; ein Test für solches Verhalten trägt erst dann einen `US-NNN`-Tag, wenn ein
   Szenario ihn deckt. Grund: Der Blob-Anker aus [TDD-Zyklus](#IMP-tdd-zyklus) sichert nur Test-Änderungen **nach**
   der Freigabe ab – ein Review-Fix führt neues Verhalten daran vorbei ein, und dass sein Test
   einen US-Tag trägt, verdeckt die Lücke zusätzlich. Fehlt das Szenario, gehört es **vor** dem
   Fix ins Feature-File (Ablage-Regel: [`gherkin-workshop`-UI-Verhaltens-Checkliste](../gherkin-workshop/SKILL.md#GHW-ui-verhaltens-checkliste)); ist das zu groß für diesen
   Lauf, ist der Fix zurückzustellen, nicht ungedeckt umzusetzen.

3. **Terminierung:**
   - a) 0 ❌ und 0 ⚠️ in einer Runde → [Review-Loop](#IMP-review-loop) abgeschlossen.
   - b) 0 ❌, aber ⚠️ → umsetzen wie in Schritt 2. Waren alle Fixes trivial (Beleg: `qa-check`),
     ist der Loop abgeschlossen; hat ein Schicht-Subagent etwas geändert, folgt eine weitere Runde.
   - c) Nach 3 Runden ohne Abschluss → STOP, User fragen.


<a id="IMP-abschluss"></a>
## Abschluss

1. **Offene Punkte mit dem User triagieren:** Sammle aus dem gesamten Ablauf alles, was nicht in den Szenario-Code eingeflossen ist – nichts darf nur in der Konversation hängen bleiben oder ungefragt irgendwo eingetragen werden:
   - **Improvement-Vorschläge aus den Subagenten-Returns** (Schicht-Implementer melden am Ende einen „Prozessverbesserung"-/Vorschlags-Abschnitt) – jeden Return durchsehen und **pro Subagent explizit ausweisen**, ob er Feedback gab (Inhalt) oder nicht („keine"). Wird daraus ein OBS/LL erfasst, die **Quelle präzise** eintragen (`Subagent` vs. `Orchestrator`), damit später beobachtbar bleibt, woher das Feedback stammt. Punkte mit `Folge: offen` oder `Ursache: ungeklärt` durchlaufen den [Umwege-Schritt](../closing-session/SKILL.md#CLS-umwege) (bekannt? Ursache? Folge?), bevor sie als Abweichung in einen Commit gehen.
   - **Review-Findings einer späteren Phase** aus dem [Review-Loop](#IMP-review-loop) (nicht gebaut, Vorschlag: Schuld mit Phasen-Auslöser).
   - **Während des Ablaufs entdeckte technische Schuld / Tooling-Reibung.**
   - **TD-Abgleich (mechanisch, nicht aus dem Gedächtnis):**
     ```
     python3 -m prozesscode.td_due --szenarien "<Titel 1>" "<Titel 2>" …
     ```
     (die Szenario-Titel dieses Laufs, exakt aus der Feature-Datei). Das Script listet jeden `docs/tech-debt.md`-Eintrag, der per `Szenario:`-Anker auf ein Szenario dieses Laufs zeigt. Für **jeden** Treffer entscheiden: behoben → Eintrag entfernen; nicht behoben → begründen, warum der Lauf ihn nicht mit-erledigt hat.
     Prüfe zusätzlich, ob ein Eintrag **unbewusst nebenbei** behoben wurde (den fängt kein Anker) → ebenfalls schließen. Verhindert, dass `tech-debt.md` längst erledigte Posten weiterschleppt.
     Warum mechanisch statt als Lese-Aufforderung: Ein TD-Eintrag wurde nachweislich übersehen, während genau der von ihm beschriebene Bereich in einem Lauf verändert wurde. Unvergesslich ist das aber nicht dieser Schritt, sondern das `td-due`-Modul der `session-agenda.py` – es meldet einen Anker, dessen Szenario implementiert ist, auch dann, wenn dieser Schritt übersprungen wurde.

   Lege dem User **jeden** Punkt vor – mit genug **Kontext** zum Entscheiden und einer **begründeten Empfehlung**. Der User entscheidet pro Punkt:
   1. **Direkt umsetzen** → jetzt erledigen (ggf. eigener TDD-Zyklus / Schicht-Subagent).
   2. **Vermerken** → in das passende Dokument bzw. die passenden Dokumente eintragen. Welches Dokument wofür zuständig ist, steht in der `AGENTS.md`-Navigationstabelle (single source of truth – hier bewusst NICHT dupliziert, damit nichts driftet).
   3. **Ignorieren** → bewusst verwerfen.

   Erst eintragen/umsetzen, NACHDEM der User entschieden hat. Kein stilles Eintragen, kein stilles Vergessen.

   Wann die als „vermerken" entschiedenen Punkte geschrieben werden, hängt am nächsten Schritt –
   deshalb hier nur entscheiden; „direkt umsetzen"-Punkte jetzt erledigen.

2. **Vorgehen mit dem User klären** – frage per `AskUserQuestion`, was als nächstes passieren soll. Optionen:
   - <a id="IMP-session-abschluss"></a>**Session abschließen** (Empfehlung) → `closing-session`-Skill laden und ausführen. Er schreibt die als „vermerken" entschiedenen LL/OBS gebündelt (dort beim [Umsetzen der Doku-Änderungen](../closing-session/SKILL.md#CLS-doku-umsetzen) für OBS, beim [Schreiben der Learnings](../closing-session/SKILL.md#CLS-lessons) für LL – nicht erneut abfragen) und besitzt den [Abschluss-Commit](../closing-session/SKILL.md#CLS-abschluss-commit), der auch den Code dieses Laufs enthält. Dieser Skill committet nicht selbst.
   - **Nächster Lauf** → die als „vermerken" entschiedenen Punkte **jetzt** in ihre Tracker schreiben (welcher wofür: `python3 -m prozesscode.tracker`) – bis zum Session-Abschluss liegen weitere Läufe dazwischen, und was nur in der Konversation steht, geht verloren. Kein Commit, `docs/AGENT_MEMORY.md` nicht anfassen (der nächste Lauf löst sich über `{{NEXT_RUN}}` selbst auf). Dann diesen Skill für den nächsten Lauf neu starten.
   - **Etwas anderes** (Freitext) → der Anweisung des Users folgen.
