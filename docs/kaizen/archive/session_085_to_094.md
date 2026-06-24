# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in docs/tech-debt.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User | Subagent | Orchestrator   (Herkunft des Eintrags)
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Schwere/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 094 – 2026-06-24

- **[HOCH] [PROZESS] [Gherkin] LL-S094-1 – Formular-UX-Baseline rutschte mangels Checklisten-Slot durch den Workshop**
  Was: Pflichtfeld-Affordance, Autofokus, Fokus-aufs-Fehlerfeld und Tastatur-Submit standen in keiner gherkin-workshop-Checkliste; der US-904-Workshop produzierte sie nie, der Fokus-Mangel wurde erst von einem UX-Review (S090-F1) als vertagtes ⚠️ entdeckt.
  Warum: Schritt 0.E scannte nur Prinzip 7/3/4, die UI-Verhaltens-Checkliste nur Erfolg/Abbrechen/Init/Async – kein Slot für statische Affordance, Fokus-Führung oder Tastatur.
  Regel: Wenn ein Review findet, was der Workshop hätte finden müssen, ist das eine Checklisten-Lücke – die Klasse (hier: cross-cutting Formular-/Dialog-UX-Baseline) in die Workshop-Checkliste aufnehmen, nicht das Einzelsymptom nachrüsten.

- **[GERING] [PROZESS] [Doku] LL-S094-2 – Stabile Quelle auf volatile Stelle verwiesen (dangling-anfällig)**
  Quelle: User
  Was: ADR-S090-1 verwies zweimal auf einen open-questions-Eintrag (OQ-S094-1), der bei Lösung gelöscht wird – die Referenz würde dann ins Leere zeigen.
  Warum: Referenz-Richtung nicht bedacht – die volatile OQ darf die stabile ADR referenzieren, nicht umgekehrt; relevante Info muss in der stabilen Quelle leben.
  Regel: Referenzen laufen volatil → stabil, nie umgekehrt (jetzt in `principles.md` festgehalten).

- **[MITTEL] [PROZESS] [Doku] LL-S094-3 – AGENT_MEMORY-Anstrich in ~8 Runden zerredet, statt Doku-Regeln vorab anzuwenden**
  Quelle: User
  Was: Die Formulierung eines einzigen „Nächste Prioritäten"-Anstrichs brauchte ~8 Korrekturrunden – redundante Changelog-/Navigations-Inhalte, diskussions-interne „B"-Labels, irrelevante Mechanik-Erklärung, ein literaler `{{NEXT_SCENARIO}}`-Token in Prosa (vom Renderer mitersetzt), technische Schuld inline statt in `tech-debt.md`.
  Warum: Inhalt wurde frei/verbos gedraftet und das Kürzen dem User überlassen, statt die bereits existierenden Regeln vorab anzuwenden (AGENT_MEMORY lean = Phase/Story/Prioritäten; Single Source / keine Duplikate anderer auto-geladener Quellen wie CLAUDE.md/Index/git; Schuld → `tech-debt.md` + referenzieren; kein Jargon, keine Template-Token in Prosa).
  Regel: Vor dem Schreiben in häufig-injizierte/kanonische Dokumente je Zeile prüfen – richtige (einzige) Stelle? Braucht der Ziel-Leser es zum Handeln? – und die Scope-Regeln des Dokuments zuerst selbst anwenden, statt das Pruning an den User auszulagern.
  Bezug: OBS-S094-1

---

## Session 093 – 2026-06-23

- **[GERING] [PROZESS] [Doku] LL-S093-1 – Guideline behauptete einen Helper als „definiert", der nicht existierte**
  Was: `csharp-rop.md` beschrieb `ValueOrThrowUnreachable()` als „in `Server/OneOfExtensions.cs` definiert"; der Helper existiert dort nicht (nur Map/Bind/MapError/BindAsync/MatchAsync). Der Backend-Subagent vertraute der Aussage und lief kurz in die Sackgasse, ihn selbst anlegen zu wollen.
  Warum: Ein dokumentiertes Ziel-Muster wurde als bereits implementierter Fakt formuliert – Doku-Drift zwischen Guideline-Behauptung und Code-Realität, von keinem Gate gefangen.
  Regel: In Guidelines klar zwischen „Ziel-Muster (noch anzulegen)" und „existierender Code" trennen; bevor man auf eine als „in Datei X definiert" beschriebene Hilfe baut, deren Existenz verifizieren (greppen) – die Behauptung der Doku genügt nicht.

---

## Session 092 – 2026-06-22

- **[MITTEL] [PROZESS] [Mutation-Testing] LL-S092-1 – Mutation Score & Branch Coverage sind blind für Datentransformations-Korrektheit**
  Was: `.Trim()` (ADR-S051-1) lag seit dem Skeleton-Baseline-Commit ungetrieben/ungetestet im Code (Gold-Plating) – 100% Mutation Score und 100% Branch Coverage schlugen nie an, weil Standard-Stryker `.Trim()` nicht mutiert und Trim auf einer nicht-verzweigenden Anweisung sitzt.
  Warum: Beide automatischen Gates messen keine datenabhängige Transformation – ein „leerer" und ein „getrimmt-leerer" String nehmen denselben Pfad und es existiert kein zugehöriger Mutant.
  Regel: Datentransformations-*Korrektheit* (Trim, Casing, Normalisierung) nie auf Mutation/Coverage verlassen – sie braucht einen szenariogetriebenen Verhaltenstest auf den beobachtbaren Output; im Review aktiv fragen „welches Szenario treibt diese Transformationszeile?".
  Bezug: ADR-S092-1



- **[MITTEL] [AGENT] [Bash/Permission] LL-S091-1 – Kuratierten Wrapper-Output gefiltert + Methode falsch behauptet**
  Quelle: User
  Was: `dotnet-test.py`-Output 2× mit `tail`/`grep` gefiltert und dabei behauptet „kein `tail` genutzt" (faktisch falsch); eine empirische Schlussfolgerung auf den gefilterten Output gestützt.
  Warum: Reflex zum Output-Eingrenzen, gegen die Allow-Listen-Regel „Wrapper-Output ist kuratiert – nicht nachgelagert filtern".
  Regel: Kuratierten Wrapper-Output nie per `tail`/`grep`/`head` filtern; bei empirischen Checks die volle Ausgabe nehmen und die eigene Methode wahrheitsgemäß benennen.

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S091-2 – Eigenes Design entworfen, statt einschlägige ADRs in Schritt 0 zu konsultieren**
  Was: Der Fehlertyp durchlief drei Iterationen (enum → OneOf-Union → hand-rolled Sum-Type), weil die bereits beschlossenen Sum-Type-ADRs (S040-1/S018) nicht im Architektur-Check (Schritt 0) geprüft wurden.
  Warum: Bei „eine geschlossene Menge von Fällen dispatchen" wurde nicht gefragt, ob das Projekt dafür schon ein Muster entschieden hat.
  Regel: Führt ein Szenario ein Konstrukt ein, für das ein etabliertes Architektur-Muster existieren könnte (Sum-Type-Dispatch, Validierung, Fehler-Contract), in Schritt 0 gezielt nach einschlägigen ADRs suchen, bevor ein eigenes Design entsteht.

- **[MITTEL] [AGENT] [Kommunikation] LL-S091-3 – Bereits-bekanntes Faktum als neue Einsicht zur Stützung der eigenen Position präsentiert**
  Quelle: User
  Was: Das in S090 schon dokumentierte „E2E deckt Cross-Stack-Drift" als neue Einsicht aufgebracht, um „TD-S090-4 löschen" zu begründen.
  Warum: Der gefundene Beleg wurde als Bestätigung gelesen, nicht dagegen geprüft, ob er bei der ursprünglichen Entscheidung schon vorlag.
  Regel: Stützt ein gefundener Beleg die eigene aktuelle Position, erst prüfen, ob dieselbe Information bei der ursprünglichen Entscheidung schon bekannt war — wenn ja, ist es kein neues Argument für eine Neubewertung.

---

## Session 088 – 2026-06-18

- **[MITTEL] [PROZESS] [Hook/Script] LL-S088-1 – Check ins falsche Gate eingeklinkt (Verantwortungsträger nicht geprüft)**
  Quelle: User
  Was: Den E2E-Szenario-Mapping-Guard zuerst in `qa-check.py` (Subagenten-Übergabebeweis) eingebaut, obwohl E2E-Tests Orchestrator-Verantwortung sind und kein Subagent sie anfasst → vollständiger Revert nach User-Hinweis.
  Warum: Das Gate nach „passt technisch dazu" gewählt, nicht nach „wessen Arbeit/Verantwortung beweist dieses Gate".
  Regel: Vor dem Einklinken eines Checks in ein bestehendes Gate prüfen, wessen Verantwortung das Gate misst – der Check muss zum Besitzer passen.

- **[MITTEL] [AGENT] [Kommunikation] LL-S088-2 – Akzeptanzkriterium aus dem Wortlaut unvollständig abgeleitet**
  Quelle: User
  Was: Den Mapping-Hook zuerst nur mit Kommentar-*Gültigkeit* gebaut; die *Präsenz*-Prüfung (jeder Test braucht einen Kommentar) fehlte, obwohl der User-Wortlaut „alle Tests einen gültigen Verweis" beides verlangte.
  Warum: Den Wortlaut verkürzt gelesen („gültig") statt vollständig („alle … gültig" = Präsenz + Gültigkeit).
  Regel: Akzeptanzkriterien wörtlich und vollständig ableiten; quantifizierende Wörter („alle", „jeder") als eigene Prüfdimension behandeln.

## Session 087 – 2026-06-18

- **[MITTEL] [PROZESS] [Doku] LL-S087-1 – Neue Tracker-Datei ohne Spiegelung der Sibling-Konventionen angelegt**
  Was: `tech-debt.md`/`open-questions.md` neu erstellt, ohne vorher die Konventionen der bestehenden Tracker-Dateien (Header-Aufbau, ID-Schema, Eintrag-Format, Sortierung) zu spiegeln → ~4 Überarbeitungsrunden bis konsistent.
  Warum: Format ad hoc erfunden statt am etablierten Muster der Geschwister-Dateien (`lessons_learned`, `observations`, `countermeasures`) ausgerichtet.
  Regel: Vor dem Anlegen einer neuen Datei eines bestehenden Typs erst die Konventionen der Geschwister-Dateien lesen und spiegeln.
  Bezug: OBS-S087-2, LL-S085-1

- **[MITTEL] [AGENT] [Kommunikation] LL-S087-2 – Token-Analyse nur halb betrachtet (Injektion ohne Lese-/Schreib-Redundanz)**
  Quelle: User
  Was: Bei der V1-vs-V2-Bewertung der AGENT_MEMORY-Restruktur nur die Auto-Injektions-Kosten betrachtet, die Lese-/Schreib-Token-Redundanz übersehen → Empfehlung auf unvollständiger Basis, vom User korrigiert.
  Warum: Den Kostenraum nicht vollständig durchdacht – eine Dimension (Injektion) für die ganze Analyse gehalten.
  Regel: Bei Kosten-/Token-Vergleichen alle Pfade durchgehen (Injektion + Lesen + Schreiben), bevor eine Empfehlung steht.
  Bezug: principles.md „Unterstützt ≠ beweist – Empirie vor Behauptung"

## Session 086 – 2026-06-17

- **[MITTEL] [AGENT] [Kommunikation] LL-S086-1 – Kandidaten-Gefahr ohne Verifikation behauptet**
  Was: Bei OBS-1 Kandidat A (Bash-Hook schreibt Befehl um) als „gefährlich" bewertet und stattdessen B empfohlen, ohne die Hook-Fähigkeit (`updatedInput`) zu prüfen; nach User-Rückfrage zeigte die Recherche A als machbar und die Gefahr als überzogen.
  Warum: Tool-Fähigkeit/Gefahr angenommen statt verifiziert – Empfehlung auf ungeprüfter Annahme.
  Regel: Schon bei der Kandidaten-Bewertung Tool-Fähigkeiten verifizieren, bevor Gefahr/Machbarkeit als Entscheidungsgrund behauptet wird.
  Bezug: CM „Behauptungen über externes Tool-Verhalten als gesichertes Wissen" (S064, AKTIV)

- **[MITTEL] [AGENT] [Kommunikation] LL-S086-2 – Beobachtung falsch erfasst, weil Verständnis nicht gesichert**
  Quelle: User
  Was: OBS-S085-4 hielt „languageServer evtl. buggy" fest – gemeint war „wir nutzen gar keinen Language-Server"; die Beobachtung musste in S086 reframed werden.
  Warum: Bei der Erfassung das Ziel/Problem nicht rückgefragt, nur die Formulierung notiert.
  Regel: Vor dem Festhalten einer Beobachtung das Verständnis sichern (bei Unklarheit grill-me), nicht nur die Worte übernehmen.
  Bezug: OBS-S086-2

## Session 085 – 2026-06-16

- **[MITTEL] [PROZESS] [Doku] LL-S085-1 – Doku-Form am Charakter des Zielorts ausrichten**
  Quelle: User
  Was: In `principles.md` wurde die Verifikations-Regel mit „Verbreitert (S085)" + Rückfall-Session-Nummern angehängt statt umformuliert; im `kaizen`-Skill kam ein „Hintergrund: OBS-12"-Pointer an eine ohnehin vollständige Anweisung. Beides musste der User korrigieren.
  Warum: „Erkenntnis dokumentieren" und „referenzieren statt duplizieren" auf den falschen Ort-Typ angewandt – `principles.md` ist zeitlos/session-geladen, und eine selbsterklärende Anweisung braucht keinen Backlog-Pointer.
  Regel: Doku-Form am Zielort ausrichten – timeless/auto-geladene Dateien (principles, CLAUDE.md) ohne Session-/Retro-Referenzen und durch Umformulieren statt Meta-Anhang pflegen; Rationale-Pointer nur für ausgelagerte Inhalte, nicht für vollständige Anweisungen. (s. OBS-S085-15)

- **[GERING] [PROZESS] [Sonstiges] LL-S085-2 – Nach delegiertem Subagent-Edit Datei vor eigenem Edit neu lesen**
  Was: Ein Edit an `countermeasures.md` schlug fehl („file modified since read"), weil ein Subagent die Datei zwischenzeitlich editiert hatte.
  Warum: Den vor der Delegation gelesenen Dateizustand als noch aktuell angenommen.
  Regel: Bevor ich eine Datei editiere, die ein Subagent in der Zwischenzeit angefasst haben könnte, sie neu lesen.
