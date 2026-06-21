# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in docs/tech-debt.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User   (optionale Zeile, nur bei user-gemeldeten Einträgen)
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

## Session 090 – 2026-06-21

- **[MITTEL] [QUALITÄT] [TS-Code] LL-S090-1 – Offener MUI-Dialog macht den Hintergrund `aria-hidden` → rollenbasierte Queries finden nichts**
  Was: Bei offenem „Zutat anlegen"-Dialog liefen `getByRole('listitem')` (Komponenten-Test) und `getByRole('listitem')` (E2E) ins Leere, weil MUI v7 den Hintergrund per `aria-hidden` ausblendet — der Test schlug scheinbar grundlos fehl, derselbe latente Bug steckte in beiden Schichten.
  Warum: Ein `Dialog` im `open`-Zustand setzt `aria-hidden` auf den restlichen Baum; Rollen-Queries ignorieren versteckte Elemente per Default.
  Regel: Müssen Hintergrund-Elemente bei offenem Dialog/Overlay über ihre Rolle abgefragt werden, explizit versteckte einschließen — testing-library `{ hidden: true }`, Playwright `{ includeHidden: true }`.

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
