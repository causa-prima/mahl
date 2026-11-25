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

## Session 149 – 2026-11-16

- **[HOCH] [QUALITÄT] [Hook/Script] LL-S149-1 – Ausnahme in einem neuen Guard ohne Bestandsfall eingebaut – inkonsistent begründet**
  Quelle: Orchestrator
  Was: Im neuen Check gegen unsichtbare Zeichen in C#/TS-Tests (S149-Retro) nahm ich Variationsselektoren aus, für den Fall eines Emojis im Test. Die C#/TS-Tests enthalten kein Emoji, und dieselbe Begründung (Verlust ändert den sichtbaren Text, Test wird laut rot) hätte für Nullbreiten-Verbinder und Keycaps gegolten, die der Check sperrte. Der code-quality-auditor fand die Inkonsistenz; die Ausnahme ist entfernt.
  Warum: Ich entwarf die Ausnahme aus einem vorgestellten Fall, nicht aus dem Bestand – obwohl ich den Bestand im selben Schritt durchsucht hatte und er keinen Treffer in C#/TS lieferte. YAGNI war bekannt, wurde beim Guard-Bau aber nicht angelegt.
  Regel: Eine Ausnahme in einem Guard braucht einen Fall im Bestand; ohne ihn keine Ausnahme. Mit ihm wird jedes Element, für das dieselbe Begründung gilt, gleich behandelt – und ein Test schreibt die Entscheidung fest.
  CM-Bezug: CM-S047-1

## Session 150 – 2026-11-17

- **[HOCH] [QUALITÄT] [Testing] LL-S150-1 – Review-Fix machte eine C#-Assertion per ?. wirkungslos**
  Quelle: Orchestrator
  Was: Runde 1 des Reviews zur SPA-Auslieferung verlangte, ContentType!.MediaType null-sicher zu prüfen. Der Fix ContentType?.MediaType.Should().Be("text/html") prüfte bei fehlendem Header gar nichts mehr: ?. bricht die ganze Kette samt Assertion ab. Weder Orchestrator noch die Auditoren von Runde 2 bemerkten es; erst der Testqualitäts-Auditor in Runde 3.
  Warum: Null-Sicherheit wurde als Lesbarkeitsfrage behandelt, nicht als Frage, ob die Assertion noch anschlagen kann. Die Gegenprobe (Header weglassen → rot?) lief für diesen Satz nie, weil die Änderung als reines Aufräumen nach der Freigabe galt.
  Regel: In C#-Tests kein ?. vor .Should(): den Wert klammern ((x?.Y).Should()…), damit null in die Assertion läuft. Jede Änderung an einer Assertion – auch eine kosmetische – mit der Frage prüfen, ob sie im Fehlerfall noch rot würde (coding-guideline-csharp.md#CGC-null-conditional-assertion).
  CM-Bezug: CM-S101-1

- **[MITTEL] [QUALITÄT] [C#-Code] LL-S150-2 – SPA-Fallback unter /api verwandelte 405 in 404**
  Quelle: Orchestrator
  Was: Für die SPA-Auslieferung (ADR-S150-2) gab ich dem Backend-Subagenten in der PLANUNG MapFallback("/api/{**rest}", NotFound) vor. Der Fallback nimmt jede Methode an und gewann dadurch auch bei bekanntem Pfad mit falscher Methode: PUT /api/ingredients lieferte 404 statt 405. Erst der Korrektheits-Auditor meldete es, der RED-Test im Fix-Auftrag belegte es.
  Warum: Beim Entwurf zählte nur der gewünschte Fall (unbekannter API-Pfad → 404), nicht, welche bestehenden Antworten des Routings ein Catch-all-Endpoint überdeckt. Kein Test hielt 405 fest, deshalb blieb die Suite grün.
  Regel: Wer einen Catch-all- oder Fallback-Endpoint einführt, listet vorher die Negativ-Antworten, die das Routing bisher selbst gab (404, 405), und hält sie per Test fest, bevor der Fallback entsteht.

## Session 151 – 2026-11-18

- **[HOCH] [QUALITÄT] [Mutation-Testing] LL-S151-1 – Survivor in einer Schutzbedingung als YAGNI gestrichen – sie schützte ein Verhalten ohne Szenario**
  Quelle: Orchestrator
  Was: US-602 run-15: Ein Mutant überlebte im Effect von useDiscardQuestion, der einen während des Speicherns abgefangenen Navigationsversuch still zurücknimmt. Der Orchestrator las die Bedingung als überflüssig und ließ den Effect entfernen; Stryker stand danach bei 100 %. Drei Auditoren fanden den Fehlerpfad: Scheitert das Speichern, öffnet sich die Nachfrage „Eingaben verwerfen?“ nachträglich. Behoben mit einem neuen Szenario und dem zurückgeholten Effect.
  Warum: Geprüft wurden nur die Pfade, die schon ein Szenario hatten. Der Pfad „Speichern scheitert nach abgefangenem Versuch“ hatte keins – deshalb hielt kein Test die Bedingung, und der Survivor sah wie toter Code aus.
  Regel: Überlebt ein Mutant in einer Schutzbedingung, zuerst fragen, welches Verhalten sie schützt und ob dafür ein Szenario fehlt; erst streichen, wenn kein Pfad sie braucht. Ein Survivor heißt „kein Test hält das“, nicht „das braucht niemand“.
  CM-Bezug: CM-S095-2

- **[HOCH] [TOOLING] [Mutation-Testing] LL-S151-2 – Schwerer Lauf ohne Parallelitäts- und Speichergrenze brachte die WSL-VM zum Absturz**
  Quelle: User
  Was: S151: mutmut-run startete mutmut mit der Standard-Parallelität (ein Prozess je Kern, 20) – rund 30 GB, OOM in init.scope. Die Distro wurde dreimal beendet, die Agent-Sitzung ging jeweils verloren; die Ursache fand erst eine Analyse der Claude-Desktop-App unter Windows. Der Orchestrator verfolgte nach dem ersten Absturz zunächst eine falsche Spur (Freigabe-Dialog/Notification-Hook, als ungeprüft gekennzeichnet). Behoben: OOMPolicy=continue für init.scope (Windows-Seite) und mutmut-run mit 2–4 Workern in einer systemd-run-Speichergruppe (gemessen rund 1,9 GB).
  Warum: Der Wrapper hatte keine Grenze. Auf den gleichartigen Vorfall vom 29.07.2026 (node-Prozesse) wurde mit mehr RAM und Swap reagiert, nicht mit einer Ursachenprüfung – das Problem galt als Eigenschaft der Umgebung.
  Regel: Ein Absturz wird an der Ursache behoben, nicht mit mehr Ressourcen überdeckt. Werkzeuge, die Prozesse parallel starten, laufen mit fester Parallelität und Speichergrenze; nach jedem schweren Lauf Exit-Code (137) und OOM-Ereignisse prüfen.
  CM-Bezug: CM-S140-3

- **[HOCH] [PROZESS] [Hook/Script] LL-S151-3 – Bash-Hook gegen ein angenommenes Bedrohungsmodell gehärtet statt nach der Intention gefragt**
  Quelle: User
  Was: S151: Der Orchestrator verschärfte die Auditor-Sperre des Bash-Hooks (sed-Positivliste) und plante eine Absicherung gegen Umgehung per Kommando-Substitution – also gegen Absicht. Die Positivliste blockierte eine im Log 26-mal belegte harmlose Form (sed -n N,Mp $f) und wurde zurückgebaut; dabei entstanden zwei selbst eingebaute Lücken (unquotiertes \$, \\.), die erst ein Auditor fand, und ein NameError, der jedes Bash blockierte. Erst die Klarstellung des Users (Ziel: Versehen verhindern und aufs richtige Werkzeug lenken, keine Sicherheitsgrenze) korrigierte die Richtung; daraus entstand der Abschnitt DEV-schutzziel.
  Warum: Die Intention des Hooks stand nirgends. Der Orchestrator leitete sie aus sicherheitslastigen Auditor-Befunden ab, statt sie zu klären, und baute auf dieser Annahme weiter.
  Regel: Nur Änderungen vornehmen, die der Intention des Artefakts entsprechen. Steht sie nicht fest, nachfragen – nicht bei jeder Kleinigkeit, sondern wenn die Änderung Blast Radius hat (Guards, Gates, Architektur, schwer Umkehrbares).
  CM-Bezug: neu

- **[HOCH] [PROZESS] [Kommunikation] LL-S151-4 – Triage-Empfehlung in sich widersprüchlich, bestehende Regel nicht vorher gesucht**
  Quelle: User
  Was: US-602 run-14: Zur langen Testdatei empfahl der Orchestrator „ignorieren, Aufteilung vor run-15/16“ – mitten in run-14, „vor run-15“ hieß also jetzt. Die ESLint-Regel, die eine Aufteilung allein wegen der Länge verwirft (Client/eslint.config.js), fand er erst nach der Rückfrage des Users.
  Warum: Die Empfehlung wurde aus der Lage formuliert, ohne die Zeitangabe gegen den aktuellen Stand zu lesen und ohne nach einer bestehenden Regelung im Projekt zu suchen (Dimension Quellen).
  Regel: Vor einer Empfehlung zu einer Strukturfrage zuerst die bestehende Regelung im Projekt suchen; eine Empfehlung mit Zeitangabe gegen den aktuellen Stand gegenlesen, bevor sie dem User vorliegt.
  CM-Bezug: CM-S095-2

## Session 153 – 2026-11-23

- **[MITTEL] [AGENT] [Agent-Prompt] LL-S153-1 – Prämisse an Subagenten als „geprüft“ gekennzeichnet, ohne die Stelle gelesen zu haben**
  Quelle: Orchestrator
  Was: US-803 run-4, Review-Fix Runde 2: Im Auftrag an den Backend-Fix-Subagenten stand „Der PUT-Test … prüft ebenfalls nur DB-Zustand (geprüft: Datei gelesen)“ – als Konsistenzargument dafür, den GET-Teil nur aus dem DELETE-Test zu entfernen. Tatsächlich prüfte der PUT-Test ebenfalls über GET. Gelesen hatte ich nur das Testinventar und einen Diff-Ausschnitt, der den Edge-Case-Test zeigte. Dieselbe falsche Aussage stand in meiner Begründung an den User. Der Subagent fing es ab; der Fix wurde auf beide Tests ausgedehnt.
  Warum: Die Aussage stammte aus einer Erinnerung an einen ähnlich aussehenden Nachbartest, nicht aus dem Lesen der genannten Stelle; das „geprüft“ wurde aus Gewohnheit angehängt, weil die Datei in der Session schon einmal (teilweise) zu sehen war.
  Regel: Vor „(geprüft: …)“ in einem Auftrag oder einer Vorlage die genannte Stelle in diesem Zug lesen; „Datei gelesen“ heißt die konkrete Zeile, nicht die Datei irgendwann oder ihr Inventar. Sonst „(ungeprüft)“ schreiben.

## Session 154 – 2026-11-25

- **[GERING] [AGENT] [Agent-Prompt] LL-S154-1 – ADR-Text als Bauzustand an einen Subagenten weitergegeben**
  Quelle: Orchestrator
  Was: Im Spawn-Auftrag für den Frontend-Subagenten von US-201 run-1 stand als Tatsache, Ladefehler zeige der zentrale Toast aus QueryCache.onError an. Der Toast ist noch nicht gebaut (Kommentar in Client/src/hooks/useCreateIngredientWithReactivation.ts, Szenarien in features/resilience.feature offen). Der Subagent übernahm die Aussage in einen Testkommentar; im Test-Review fiel sie auf und wurde korrigiert.
  Warum: Die Aussage stammte aus dem Text von ADR-S056-1, per decisions get gelesen. Eine ADR beschreibt eine Entscheidung, nicht, was davon gebaut ist – das habe ich gleichgesetzt und die Aussage ohne Prüfung im Code und ohne „(ungeprüft)" weitergegeben.
  Regel: Eine ADR belegt die Entscheidung, nicht den Bauzustand. Wer aus einer ADR ableitet, dass etwas im Code existiert oder sich so verhält, prüft es im Code oder kennzeichnet es als (ungeprüft), bevor es an einen Subagenten geht.

- **[GERING] [AGENT] [Agent-Prompt] LL-S154-2 – Subagent legte PLANUNG und Test-Review zusammen, weil er Warten für unmöglich hielt**
  Quelle: Subagent
  Was: Der Frontend-Subagent von US-201 run-1 schrieb seine PLANUNG nicht als eigene Rückgabe, sondern zusammen mit dem RED-Batch und dem TEST-REVIEW-Signal. Er entschied die offenen Punkte selbst. Folge hier gering: Die Entscheidungen passten, das Test-Review fing den einen Fehler.
  Warum: Die Agent-Definition (.claude/agents/frontend-layer-implementer.md, Schritt PLANUNG) sagt „warte auf Antwort des Orchestrators“. Der Subagent schloss daraus, Warten sei unmöglich, weil sein einziger Rückkanal den Lauf beendet. Dass der Orchestrator ihn per SendMessage mit vollem Kontext fortsetzt, steht im Skill implementing-scenario, nicht in der Agent-Definition. Der Backend-Subagent bekam das im Auftrag ausdrücklich gesagt und hielt die Reihenfolge ein. Vom User als einmaliger Ausrutscher eingestuft: erst bei Wiederholung handeln.
  Regel: Im Subagenten heißt Warten: den Lauf mit der PLANUNG beenden. Der Orchestrator setzt per SendMessage fort. PLANUNG und TEST-REVIEW nur dann zusammenlegen, wenn es keine Rückfragen gibt.

- **[HOCH] [AGENT] [Agent-Prompt] LL-S154-3 – Mehrdeutiger Fix-Auftrag ließ den Subagenten die Test-Freigabe überspringen**
  Quelle: Orchestrator
  Was: Im Review-Fix-Auftrag (US-201 run-2, Frontend) stand: „Bevor du den Lauf abschließt, sende ein TEST-REVIEW-Signal“. Der Subagent schrieb Teständerungen und Produktionscode (shoppingListApi.ts, PlannedRecipesPage.tsx, ShoppingListPage.tsx) und sandte das Signal erst am Ende. Das Test-Review fand damit nach dem Produktionscode statt; ich prüfte nachträglich, behob einen Formatfehler selbst und setzte neue Anker.
  Warum: „Vor dem Abschluss“ beschreibt den Zeitpunkt relativ zum Laufende, nicht zum ersten Produktionscode. Der Subagent hat wörtlich befolgt. Für den TDD-Zyklus gibt die Vorlage im Skill den Halt vor; für Fix-Aufträge schreibe ich frei, und dort fehlte er. Der Blob-Anker sichert nur Teständerungen NACH der Freigabe – ein Halt, der nie stattfand, fällt ihm nicht auf.
  Regel: Jeder Auftrag, der Tests ändert, nennt den Halt am Produktionscode ausdrücklich: „Erst die Teständerungen, RED zeigen, dann mit TEST-REVIEW beenden – vor dem ersten Produktionscode.“
  CM-Bezug: CM-S070-1

- **[MITTEL] [TOOLING] [Sonstiges] LL-S154-4 – Edit verwarf ein Leerzeichen am Ende von new_string – Token im Roh-SQL verklebt**
  Quelle: Subagent
  Was: Ein Backend-Subagent ersetzte per Edit Tabellennamen im Roh-SQL der Migration; danach stand dort "ShoppingListItems"( statt "ShoppingListItems" (. Er bemerkte es erst beim Lesen vor der Gegenprobe. In S154 nachgemessen (Claude Code 2.1.332): Endet new_string auf ein Leerzeichen, fehlt es in der Datei; old_string wird exakt verglichen.
  Warum: Ungeklärt, ob beabsichtigt oder ein Fehler des Harness und ob es so bleibt. Issue-Berichte (nur über Spiegel der GitHub-Issues gefunden, nicht am offiziellen Tracker geprüft) beschreiben das Entfernen von Leerraum am Zeilenende als länger bekannt und als offenen Wunsch nach wörtlichem Schreiben. Unbemerkt hätte es im SQL zu einem Laufzeitfehler oder bei verklebten Bezeichnern zu stiller Bedeutungsänderung führen können.
  Regel: old_string und new_string nie auf Leerraum enden lassen, sondern bis zum nächsten sichtbaren Zeichen fassen (claude-code-anknuepfung.md, Zeile „Zeichentreue von Edit“); beim nächsten Claude-Code-Update nachmessen.
