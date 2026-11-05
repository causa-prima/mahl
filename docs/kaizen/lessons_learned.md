# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in docs/tech-debt.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[IMPACT] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User | Subagent | Orchestrator   (Herkunft des Eintrags)
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).
    CM-Bezug: <CM-ID> | neu     (Pflicht bei KRITISCH/HOCH, sonst optional)

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.
    CM-Bezug: neu

  Zum Feld CM-Bezug: Die ID der Maßnahme, an die das Finding anschließt, oder `neu`, wenn
  dafür erst eine entstehen muss (die ID muss in countermeasures.md existieren). Pflicht bei
  KRITISCH und HOCH; bei MITTEL/GERING optional – besteht ein Bezug, gehört er hinein, sonst
  entfällt die Zeile. `lessons.py add --cm-bezug` erzwingt und prüft es.
  (Zeilenanfang bewusst nicht „CM-Bezug:" – sonst zählt der Auswertungs-grep des kaizen-Skills
  diese Erklärung als Eintrag mit.)

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Impact:     KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Testing | Sonstiges

Alle Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (überall Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Impact/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 145 – 2026-11-04

- **[HOCH] [AGENT] [Kommunikation] LL-S145-1 – Befund per Namens- bzw. Regex-Zählung ausgegeben, ohne die Treffer anzusehen**
  Quelle: Orchestrator
  Was: In der S145-Retro meldete ich zur Testabdeckung von retro_report, die Kandidatenauswahl (_neue_kandidaten, _abgedeckte_kandidaten) sei ungetestet – gezählt hatte ich nur, wie oft die Funktionsnamen in der Testdatei vorkommen. Vier Tests über render_pattern deckten sie längst; der User entschied ‚G4 jetzt' auf dieser Grundlage. Ebenso stand ‚14 von 31 AKTIV-Maßnahmen ohne Kriterium' als Tatsache in process.md, gestützt auf eine grobe Regex; gemessen waren es 17 von 32.
  Warum: Die Zählung konnte indirekte Tests gar nicht sehen, und die Regex zählte frei formulierte Sätze mit – beide Prüfungen hätten beim Gegenteil gleich ausgesehen. Ich habe das Ergebnis weitergegeben, ohne eine Stichprobe der Treffer bzw. Nicht-Treffer anzusehen.
  Regel: Ein Befund aus einer Namens- oder Mustersuche wird erst ausgegeben, wenn mindestens ein Treffer und ein Nicht-Treffer im Kontext angesehen sind und die Frage beantwortet ist, ob die Suche den Fall überhaupt sehen könnte (indirekter Aufruf, andere Schreibweise). Bis dahin als grobe Schätzung kennzeichnen – und nie als Zahl in eine Doku schreiben.
  CM-Bezug: CM-S116-1

- **[HOCH] [AGENT] [Kommunikation] LL-S145-2 – Guard-Entwurf vorgeschlagen, ohne den Durchgangsweg der zu prüfenden Fälle nachzuverfolgen**
  Quelle: Orchestrator
  Was: Für den Poka-yoke zu CM-S070-1 (Review-Fix-Tests ohne Szenario) schlug ich in der S145-Retro eine Prüfung bei qa-check --verify gegen den Freigabe-Anker vor; der User gab das Bauen frei. Erst beim Nachlesen vor dem Bau zeigte sich: Ein Review-Fix läuft über einen eigenen Test-Review und bekommt einen eigenen Anker – die Prüfung hätte die gemeinten Tests nie gesehen.
  Warum: Ich hatte den Durchgangsweg nur als ‚nicht bis ins Detail nachgelesen' markiert, statt ihn vor dem Vorschlag nachzuverfolgen. Für ein Guard-Design verlangt das Prinzip einen Beleg je Dimension, kein Argument – die Dimension ‚Pfade' (welchen Weg nimmt der zu fangende Fall?) blieb ungeprüft.
  Regel: Vor jedem Guard- oder Gate-Vorschlag den Weg des Falls, den er fangen soll, im Skill bzw. Code bis zur geplanten Prüfstelle nachverfolgen: Erreicht der Fall die Stelle in dem Zustand, den die Prüfung sieht? Eine Unsicherheit dazu wird vor dem Vorschlag aufgelöst, nicht nur markiert.
  CM-Bezug: CM-S095-2

## Session 146 – 2026-11-05

- **[MITTEL] [QUALITÄT] [Testing] LL-S146-1 – Ein Test schickte über einen Mutanten SIGHUP an mutmut**
  Quelle: Orchestrator
  Was: Der Sperrklinken-Volllauf brach zweimal an derselben Stelle (Mutant 4195 von 21513) mit Exit -1 ab, rund 10 Minuten je Versuch. Ursache: Ein in S146 von einem Subagenten geschriebener Test (test_dotnet_stryker, Lock-Test) trug os.getppid() als 'lebenden fremden Prozess' in den Lock ein. mutmut mutierte in _run_lock._pid_alive os.kill(pid, 0) zu os.kill(pid, 1) – SIGHUP an den Elternprozess, unter mutmut also an mutmut selbst. Behoben: PID 1 (init), wie der bestehende Lock-Test; als normaler User ist ein Signal an init wirkungslos (PermissionError, gilt als lebend).
  Warum: Ein Test, der einen echten Prozess außerhalb seiner selbst als Ziel einer Signal-Funktion nutzt, ist harmlos, solange der Code das Signal 0 schickt. Mutation verwandelt die Signalnummer in ein echtes Signal; welcher Prozess es empfängt, entscheidet dann der Test. Beim Schreiben denkt niemand an den Mutanten, beim Review auch nicht.
  Regel: Tests übergeben Signal-Funktionen (os.kill, killpg) nur PIDs, die ein echtes Signal nicht trifft oder nicht stört: PID 1 als 'lebt, gehört einem anderen', ein eigener Kindprozess als 'lebt, gehört mir'. Nie getppid() oder die PID eines Werkzeugs, unter dem der Test läuft.

- **[HOCH] [PROZESS] [Doku] LL-S146-2 – LSP-Pilot maß über fünf Runden Nutzung, ohne die Ausführbarkeit der Anweisung zu prüfen**
  Quelle: Orchestrator
  Was: OBS-S085-4 (Language-Server für die Agenten) wurde seit 2026-06-20 fünfmal verlängert und stand in S146 vor dem Verwerfen nach Abbruchklausel. Gemessen wurde stets nur die Nutzung (tool-usage --lsp: null). Erst ein Harness-Test in S146 mit einem echten frontend-layer-implementer zeigte: LSP steht direkt in seiner Tool-Liste, ToolSearch hat er nicht – die Prompt-Anweisung 'deferred: erst per ToolSearch select:LSP laden' war zumindest heute falsch und ließ sich als 'nicht ladbar' lesen. Ob sie in früheren Runden stimmte, ist ungeklärt (Claude Code kann sein Verhalten geändert haben; beim Aktivierungstest war LSP in der Hauptsession vermutlich deferred). Die Log-Auswertung zeigte zudem null Ladeversuche in 52 Agentenläufen.
  Warum: Eine Nullnutzung hat mehrere Ursachen – nicht gewollt, vergessen, nicht erreichbar –, und eine Nutzungszählung unterscheidet sie nicht. Die Pilot-Kriterien setzten die Erreichbarkeit voraus, statt sie je Runde zu prüfen; die Anweisung im Prompt galt als Teil des Aufbaus, nicht als Behauptung über Tool-Verhalten, die altern kann. Fast wäre auf dieser Basis verworfen worden.
  Regel: Ein Pilot, der Nutzung misst, prüft zu Beginn jeder Runde im echten Zielagenten, dass die Anweisung ausführbar ist (Tool sichtbar, Ladeweg stimmt, ein Aufruf gelingt) – erst dann sagt eine Nullnutzung etwas über das Werkzeug.
  CM-Bezug: CM-S116-1

## Session 147 – 2026-11-05

- **[MITTEL] [AGENT] [Review] LL-S147-1 – Vorgabe oder Prüfurteil aus dem Gedächtnis statt aus der Quelle**
  Quelle: Orchestrator
  Was: S147, CROSS-text/run-1, drei Fälle: (a) Im Test-Review bestätigte ich „Given/When/Then: vorhanden“, obwohl fünf Tests kein // Given hatten – erst das Gate von qa-check fing es. (b) Mein Subagenten-Auftrag verlangte als // Beispiel: die Zelle „Eingabe“; TDD-spec-verweis und der Hook verlangen die ganze Tabellenzeile – ein Fehlversuch des Subagenten. (c) Mein Gegenprobe-Auftrag „NFC vor das Entfernen ziehen“ war mehrdeutig; der Subagent setzte NFC zusätzlich davor, das abschließende NFC heilte den Fehler, der erste Versuch war wirkungslos.
  Warum: Ich schrieb die Vorgabe bzw. das Urteil aus der Erinnerung an die Regel, statt die Quelle (Diff, TDD-spec-verweis, gewünschte Mutation) nachzusehen. Bei (c) beschrieb ich die Absicht statt des herzustellenden Codezustands.
  Regel: Prüfpunkte im Test-Review am Diff zählen, nicht schätzen; Formatvorgaben in Aufträgen aus der Regelquelle kopieren; eine Gegenprobe als exakten Zielzustand des Codes formulieren („Zeile X durch Y ersetzen“), nicht als Absicht.

- **[MITTEL] [AGENT] [Review] LL-S147-2 – Testumfang im Subagenten-Auftrag gegen die Full-State-Regel beschnitten**
  Quelle: Orchestrator
  Was: S147, US-602 run-9: Im Auftrag an den Frontend-Subagenten gab ich vor, im Komponententest zu zwei zu langen Schritten den gesendeten Request-Body nicht zu prüfen. Die TS-Guideline (CGT-full-state-assertions) verlangt den vollständigen beobachtbaren Zustand, also auch den Body. Der Test-Auditor verlangte die Prüfung in Review-Runde 2 zu Recht; sie kam per Fix-Subagent nach, eine zusätzliche Runde. Vierter Fall derselben Klasse in dieser Session nach LL-S147-1.
  Warum: Die Vorgabe beruhte auf meiner Einschätzung, der Body sei an anderer Stelle schon geprüft; gegen die Regelquelle habe ich sie nicht gehalten. Die genaue Überlegung von damals ist nach zwei Kontext-Kompaktierungen nicht mehr rekonstruierbar.
  Regel: Wer im Auftrag eine Prüfung ausdrücklich ausschließt, hält das vorher gegen die Test-Regeln der Guideline (CGT-full-state-assertions, CGC-Pendant) – ein Ausschluss ist eine Vorgabe wie jede andere und braucht ihre Quelle.
