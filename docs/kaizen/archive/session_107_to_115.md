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

  Beispiel:
  - **[HOCH] [PROZESS] [TDD] LL-S084-1 – Content-Hash ohne stabile Sortierung nicht killbar**
    Was: ETag-Mutant überlebte, weil die Collection-Reihenfolge nicht deterministisch war.
    Warum: OrderBy(name) fehlte → Insertion-Order ≠ alphabetisch.
    Regel: Content-Hash über Collections immer auf eine stabile Sortierung stützen.

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

Impact:     KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Testing | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Dieser Header ist die kanonische Format-Quelle** (Eintrag-Format, IDs, Erfassungs-Test).
> **Definitionen** (Impact/Kategorie/Kontext) + Reaktionsregeln: `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 113 – 2026-08-01

- **[HOCH] [PROZESS] [Doku] LL-S113-1 – Behauptung aus einem projekteigenen Dokument ungeprüft zur Entscheidungsgrundlage gemacht**
  Quelle: User
  Was: Beim Drain von OBS-S088-1 (Hook-Dispatcher) stützte sich die Verwerfungs-Empfehlung auf die im Eintrag notierte Aussage „uneinheitlicher Input-Vertrag (Fragment-`HookInput` vs. voller Post-Edit-Inhalt + Datei-Reads)". Erst nach Widerspruch des Users wurde geprüft: Alle sechs Scripts lasen bereits identisch (`json.load(sys.stdin)` → `tool_name` → `tool_input` → `file_path`); die Uneinheitlichkeit betraf nicht den Input, sondern eine daraus abgeleitete Berechnung, die drei Scripts fast wortgleich duplizierten. Der Umbau war danach in einer Sitzung erledigt. Ohne den Widerspruch wäre ein umsetzbarer Punkt mit falscher Begründung geschlossen worden – und die Begründung wäre als Präzedenz im Archiv gelandet.
  Warum: `principles.md` verlangt Empirie vor Behauptung ausdrücklich für „Aussagen über externes Tool-Verhalten"; projekteigene Dokumente wurden als bereits verifiziert behandelt. Ein OBS-Eintrag ist aber eine Momentaufnahme der Lage bei der Erfassung – hier 25 Sessions alt – und altert wie jede andere Quelle.
  Regel: Vor einer Drain-Entscheidung die im Eintrag behaupteten technischen Fakten am aktuellen Code prüfen, nicht aus dem Eintrag übernehmen – besonders wenn sie die Kostenschätzung tragen und der Eintrag mehrere Sessions alt ist.

- **[MITTEL] [TOOLING] [Hook/Script] LL-S113-2 – Hook-Test mit absichtlich ungültigem Edit ist falsch-negativ**
  Quelle: Orchestrator
  Was: Um zu prüfen, ob `check-dependency-allowlist` über den neuen Dispatcher noch blockt, wurde ein Edit auf `Client/package.json` mit einem `old_string` abgesetzt, der garantiert nicht in der Datei steht – die Absicht war, bei ausbleibendem Deny keine echte Änderung zu riskieren. Der Aufruf endete in „String to replace not found", **ohne** Deny. Die naheliegende Lesart wäre gewesen, der Check sei durch den Umbau kaputt.
  Warum: Die Gültigkeitsprüfung von `old_string` läuft vor dem PreToolUse-Hook; ein absichtlich ungültiger Edit erreicht den Hook nie. Der vermeintlich sichere Test hat genau den Mechanismus umgangen, den er prüfen sollte.
  Regel: Einen PreToolUse-Hook nur mit einem Aufruf testen, der ohne den Hook tatsächlich durchliefe – für Datei-Werkzeuge also mit echtem `old_string` bzw. per `Write`; ausbleibendes Blocken sonst erst als Hook-Befund werten, nachdem derselbe Input über die CLI gegengeprüft wurde.

- **[HOCH] [PROZESS] [Testing] LL-S113-3 – Die Testsuite der eigenen Werkzeuge lief in keinem Gate**
  Quelle: Orchestrator
  Was: Beim ersten Testlauf dieser Session waren vier Tests in `test_qa_check.py` rot – auf unverändertem `main`. Eine Signaturänderung an `_parse_report` (Rückgabe von 2 auf 3 Werte, Score als float statt formatiertem String) war ohne Anpassung der Tests eingecheckt worden. `pytest` kam weder in `qa-check.py` noch in der Definition of Done, im TDD-Prozess oder in `implementing-scenario` vor; die Suite lief nur, wenn jemand sie von Hand startete.
  Warum: Die Suite sichert Hooks und Wrapper-Scripts ab – also genau die Mechanismen, die alle anderen Gates durchsetzen –, war selbst aber durch keines gedeckt. Ein Sicherungsmechanismus ohne eigene Sicherung fällt lautlos aus, weil sein Ausfall per Definition nichts auslöst.
  Regel: Beim Bauen oder Ändern eines Gates prüfen, wodurch dieses Gate selbst abgesichert ist – und die Prüfung an den Auslöser hängen, der es brechen kann, nicht an einen Ablauf, den die betreffende Arbeit gar nicht durchläuft.

## Session 111 – 2026-07-29/30

- **[MITTEL] [PROZESS] [Agent-Prompt] LL-S111-1 – Doku-Pflicht ausschließlich über den Subagenten-Return transportiert, Return fiel aus**
  Quelle: Orchestrator
  Was: Beide Nachbesserungs-Aufträge von run-11 trugen die Auflage „keine neue ADR anlegen – melde mir im Return, was dokumentiert gehört". Das Session-Limit beendete beide Subagenten, bevor sie antworten konnten. Der Backend-Agent hatte zu diesem Zeitpunkt bereits einen Code-Kommentar geschrieben, der auf ein ADR-Addendum verwies – das Addendum selbst existierte nie, weil nur der Orchestrator es hätte schreiben dürfen und die Meldung mit dem Return verschwand. Der tote Verweis wäre in den Commit gegangen: Tests, Stryker und `qa-check` Check 6 waren grün, letzterer prüft nur die Existenz der ADR-ID, nicht die des referenzierten Abschnitts.
  Warum: Die Auflage trennt Ausführung (Subagent schreibt den Verweis) von Pflicht (Orchestrator schreibt das Ziel) und verbindet beide allein über den Return – einen Kanal ohne Persistenz, dessen Ausfall keine Spur hinterlässt außer dem bereits geschriebenen Verweis.
  Regel: Verbietet man einem Subagenten das Schreiben eines Dokuments, auf das sein Code verweisen wird, die Pflicht beim Erteilen des Auftrags notieren – nicht erst aus seinem Return erfahren; und einen Verweis auf noch nicht geschriebene Doku vor dem Commit gegen den Zielabschnitt prüfen, nicht nur gegen die ID.

- **[MITTEL] [PROZESS] [Doku] LL-S111-2 – Rein reaktiver tech-debt-Trigger griff nicht, obwohl das Auslöse-Ereignis eintrat**
  Quelle: Orchestrator
  Was: `TD-S108-4` (Toast auf Touch nicht manuell schließbar) trug den Trigger „der nächste Lauf, der den Toast ohnehin verändert". run-11 hat genau das getan – den Undo-Toast-Lebenszyklus geändert und einen zweiten Toast eingeführt –, ohne dass der Trigger jemandem auffiel. Der Eintrag blieb liegen, und die Lücke wurde durch den neuen Toast mit 10 s Anzeigedauer sogar ausgeweitet; bemerkt wurde es erst beim TD-Abgleich im Abschluss-Schritt.
  Warum: Ein Trigger, der auf ein künftiges Code-Ereignis wartet, wird nur wirksam, wenn beim Implementieren jemand `tech-debt.md` nach passenden Triggern durchsucht. Der TD-Abgleich am Lauf-Ende (`implementing-scenario` Schritt 6) fragt nur „wurde ein Eintrag durch diesen Lauf behoben?" – nicht „ist die Vorbedingung eines Eintrags jetzt erfüllt?". **Korrektur in der S116-Retro (die ursprüngliche Ursachen-Notiz war unvollständig):** Für die zweite Frage existiert der Mechanismus sehr wohl – Schritt 0, Punkt 5 verlangt wörtlich, für *jeden* TD-Eintrag, der die berührten Code-Bereiche betrifft, vor der Umsetzung zu entscheiden **und schriftlich zu begründen**. TD-S108-4 betraf den Toast, run-11 änderte den Toast-Lebenszyklus – der Eintrag war also area-berührt und vom Mechanismus abgedeckt. Er wurde nur nicht ausgeführt. Damit ist dies nach LL-S095-4 ein **Rückfall auf CM-S107-2**, keine Abdeckungslücke; der Fix liegt in der Ausführungsdisziplin von Schritt 0, nicht in einer Umformulierung von Schritt 6.
  Regel: TD-Trigger an einen Ort hängen, der im Ablauf ohnehin gelesen wird (z. B. als aufzunehmendes Szenario im `gherkin-workshop`), statt auf einen zufällig vorbeikommenden Lauf zu warten.

- **[MITTEL] [QUALITÄT] [Mutation-Testing] LL-S111-3 – Assertions gegen einen Survivor geschrieben, den keine Komponenten-Assertion töten kann**
  Quelle: Subagent
  Was: Ein Stryker-Survivor in der Status-Verzweigung von `restoreIngredient` wurde zweimal mit einer Komponenten-Assertion angegangen (Wertevergleich, dann Ternary), beide wirkungslos. Erst der empirische Test – Mutant manuell einsetzen, Einzeltest laufen lassen – zeigte, warum: Der Mutant erzeugt einen `TypeError` **innerhalb** eines React-Query-`onSuccess`-Callbacks, wo das Framework ihn abfängt; der Test bleibt grün, obwohl der Code defekt ist. Laut Bericht des Implementierers die größte Zeitquelle des Laufs.
  Warum: Die Wahl der Testschicht wurde aus der Vermutung abgeleitet, wo der Effekt sichtbar sein *müsste*, statt aus einer Messung, wo er tatsächlich sichtbar ist – und Frameworks, die Callback-Fehler schlucken, verletzen genau diese Vermutung stillschweigend.
  Regel: Bei einem Stryker-Survivor in einem Framework-Callback (`onSuccess`, Event-Handler, Effekt) erst empirisch prüfen – Mutant kurz manuell einsetzen, Einzeltest laufen lassen –, ob die geplante Assertion ihn überhaupt töten kann, bevor sie geschrieben wird.

## Session 110 – 2026-07-29

- **[HOCH] [PROZESS] [Review] LL-S110-1 – Test-Batch freigegeben, obwohl die Hauptassertion unter dem naheliegenden Mutanten vakuös war**
  Quelle: Orchestrator
  Was: Im Test-Review von run-9 wurde der Batch freigegeben; die einzige Then-Assertion (`expect(loeschenButton).toBeDisabled()`) war jedoch unter dem naheliegenden `===`→`!==`-Mutanten bereits **vor** jeder Interaktion erfüllt – ein von Anfang an deaktivierter Button feuert nativ kein `onClick`, der DELETE lief also nie. Der Mutant wurde faktisch von einem nachgelagerten Block gekillt, den der Kommentar als „kein Szenario-Assert, reine Test-Infrastruktur" auswies. Gefunden erst vom `test-quality-auditor` in Schritt 5, danach empirisch bestätigt (Mutant eingesetzt: Fehlschlag lag im Cleanup, nicht an der Assertion).
  Warum: Der 100-%-Mutation-Score war ein Fehlsignal – er belegt, *dass* ein Mutant stirbt, nicht *wo*. Die Per-Assertion-Pflicht des Test-Reviews fragt „welches Gherkin-Kriterium erzwingt diese Assertion?", aber nicht „welcher Block trägt tatsächlich die Beweislast?"; ein als Infrastruktur deklarierter Block wurde deshalb gar nicht auf Assertion-Wirkung geprüft.
  Regel: Bei einer Assertion über einen Zustands**übergang** („X ist während Y", „erst nach Z") auch die Vorbedingung explizit assertieren – und im Test-Review prüfen, an welcher Stelle der Test unter dem naheliegenden Mutanten rot wird. Scheitert er woanders als an der Assertion, die das Kriterium trägt, ist die Assertion vakuös, egal wie hoch der Mutation Score ist.
  Bezug: OBS-S110-2

---

## Session 109 – 2026-07-28/29

- **[HOCH] [AGENT] [Kommunikation] LL-S109-1 – Messergebnis dreimal als Befund vorgelegt, bevor die Datenquelle vollständig war**
  Quelle: User
  Was: Bei der Phase-1-Token-Messung (OBS-S085-2) wurde dreimal ein Ergebnis mit Prozentzahlen und daraus abgeleiteter Empfehlung präsentiert, das jeweils durch eine User-Rückfrage kippte: (1) Subagent-Logs liegen unter `<session-id>/subagents/` und fehlten im Glob – mit ihnen verdoppelt sich das Gesamtvolumen; (2) injizierte Skill-Texte liefen als „echte User-Eingaben" mit; (3) `SendMessage` war unter Tool-I/O statt unter Agent-Kommunikation einsortiert, was den fraglichen Posten von 8,6 % auf 2,1 % kleingerechnet hätte. Ohne die Rückfragen wäre eine Verwerf-Entscheidung mit falscher Ursachenzuschreibung in `observations.md` gelandet.
  Warum: Nach jedem Lauf wurde die Plausibilität des *Gesamtbilds* geprüft, nicht die Vollständigkeit der *Quelle* – auffällige Einzelwerte (0,3 % für Subagent-Reports, 17 % „getippte" User-Eingaben) wurden gesehen, aber erst auf Nachfrage verfolgt statt sofort als Kalibrierungs-Signal genommen.
  Regel: Vor dem Vorlegen einer Messung jeden Wert, der um Größenordnungen von der Erwartung abweicht, als Fehler in der *eigenen Erhebung* behandeln und ihm nachgehen, bevor Anteile berichtet werden; die Vollständigkeit der Datenquelle explizit prüfen (welche Stränge/Verzeichnisse gibt es überhaupt?), nicht nur die Konsistenz des Ergebnisses.
  Bezug: OBS-S109-1

- **[MITTEL] [AGENT] [Kommunikation] LL-S109-2 – Empfehlung auf Ressourcen-Argument gestützt statt auf die Sache**
  Quelle: User
  Was: Für die fällige Wiedervorlage OBS-S085-2 wurde „aufschieben" empfohlen, begründet mit „diese Session hat schon zwei Umbauten geliefert" und „am Stück hätte es mehr Qualität". Auf Nachfrage war beides nicht haltbar – das erste ist kein Sach-Argument, das zweite war unbelegt und eher falsch herum (der Kontext zur Messung war gerade frisch). Die Messung war read-only, die Daten lagen vor, der Re-Trigger war erfüllt.
  Warum: Der eigene Aufwand wurde unausgesprochen in die Sachabwägung eingerechnet und dann nachträglich mit einem Qualitätsargument verkleidet.
  Regel: Eine Empfehlung nur auf Eigenschaften der Sache stützen (Risiko, Reversibilität, Datenlage, Abhängigkeiten). Spielt der eigene Aufwand eine Rolle, ihn als solchen benennen statt ihn als Qualitätsargument zu tarnen – und bei einer bereits zweimal aufgeschobenen Wiedervorlage gilt Aufschub ohnehin als begründungspflichtig, nicht als neutrale Option.

- **[MITTEL] [QUALITÄT] [Mutation-Testing] LL-S109-3 – Negativ-Befund aus einem Testfall gezogen, der ihn gar nicht zeigen konnte**
  Quelle: Orchestrator
  Was: Ob Stryker.NET mehrere `--mutate`-Flags akzeptiert, wurde an zwei Dateien getestet und aus „nur 1 Datei im Report" geschlossen, das Tool nehme nur das letzte Flag. Die zweite Datei hat jedoch generell 0 Mutanten – der Testfall konnte einen Erfolg gar nicht anzeigen. Mit zwei nachweislich mutantenhaltigen Dateien war das Ergebnis das Gegenteil (2 Dateien, 13 = 10+3 Mutanten).
  Warum: Der Testfall wurde nach Verfügbarkeit gewählt, ohne vorher zu prüfen, ob er im Erfolgsfall ein unterscheidbares Signal liefert.
  Regel: Vor einem Verhaltenstest an fremdem Tooling festlegen, wie Erfolg und Misserfolg **unterschiedlich** aussehen, und die Testdaten danach auswählen – sonst ist ein Negativ-Ergebnis nicht vom untauglichen Messaufbau unterscheidbar.

## Session 107 – 2026-07-22

- **[MITTEL] [PROZESS] [Skill-Nutzung] LL-S107-1 – Retro-Auftakt-Sonde beim Retro-Start übersprungen**
  Quelle: Orchestrator
  Was: Die für den Retro-Beginn geplante blinde LL-Impact-Re-Rating-Sonde (OBS-S092-3, in AGENT_MEMORY „Nächste Prioritäten" vermerkt) lief nicht zu Beginn – `retro_report.py` (Schritt 2) lief davor; die Sonde wurde erst mitten in der Retro selbst nachgeholt.
  Warum: Die Sonde lebte nur als AGENT_MEMORY-Prosa; der `kaizen`-Skill hatte keinen Schritt, der retro-spezifische Auftakt-Items aus AGENT_MEMORY konsultiert und ausführt.
  Regel: Retro-/session-spezifische Auftakt-Aufgaben nicht nur als AGENT_MEMORY-Prosa parken – im Skill einen Schritt verankern, der solche Items zu Beginn zieht und abarbeitet. (Fix gelandet: Impact-Sanity-Check ist jetzt fester `kaizen`-Schritt 0.)

- **[MITTEL] [AGENT] [Kommunikation] LL-S107-2 – CM-BEWÄHRT-Evidenz vorgelegt ohne Zerlegung der Mechanismus-Aktivität**
  Quelle: Orchestrator
  Was: CM-S070-1 als BEWÄHRT-reif mit „6 sauberen Läufen" vorgelegt und freigeben lassen; erst tieferes Lesen des S104-Commits zeigte, dass das Blob-Anker-Gate für Backend bis S104 aus war → nur 2 valide Backend-Läufe. C1 musste nach bereits erteilter Freigabe revidiert werden.
  Warum: „Läufe fanden statt" nicht zerlegt in „war der wirksame Mechanismus (Gate) über die ganze Periode aktiv?" – die auffällige Lauf-Zahl fürs Ganze genommen.
  Regel: Vor einer CM-BEWÄHRT-/Wirksamkeits-Aussage prüfen, ob der steuernde Mechanismus über den **gesamten** Bewertungszeitraum aktiv war (Gate-off-Perioden zählen nicht) – Lauf-Zahl ≠ gate-gedeckte Lauf-Zahl.
  Bezug: CM-S095-2

---

## Session 108 – 2026-07-23/25

- **[HOCH] [AGENT] [Agent-Prompt] LL-S108-1 – Beide Frontend-Subagenten endeten ohne Übergabe-Report; passives Warten sah dabei korrekt aus**
  Quelle: Orchestrator
  Was: Zwei Frontend-Subagenten wurden beendet, ohne ihren `=== VERIFIKATIONS-HASH ===`-Block zu liefern; der Orchestrator wartete jeweils weiter und erfuhr erst durch den User, dass kein Agent mehr läuft – beide Übergabeläufe (`qa-check --layer frontend` inkl. vollem Stryker) musste er danach selbst nachfahren.
  Warum: Es kam nie eine Abschluss-Meldung an, sondern nur wiederholte idle-Zwischensignale. Die Skill-Regel „idle ignorieren, bei gemeldetem Abschluss ohne Report per `SendMessage` nachfordern" greift damit nicht: Sie deckt nur den Fall ab, in dem ein Abschluss *gemeldet* wird – bleibt beides aus, ist Weiterwarten regelkonform und trotzdem endlos.
  Regel: Bleibt ein beauftragter Subagent über mehrere idle-Signale ohne inhaltlichen Return, den Fortschritt **mechanisch am Arbeitsbaum** prüfen (`git status`/`git diff`/gezieltes `grep` auf die erwartete Änderung) statt weiter passiv zu warten – und bei erkennbar abgeschlossener Arbeit ohne Report den Verifikationslauf selbst fahren, statt ihn nachzufordern.
  Bezug: OBS-S108-3

- **[MITTEL] [PROZESS] [Testing] LL-S108-2 – Test-Kategorie pauschal vorgegeben statt pro Test geprüft**
  Quelle: Orchestrator
  Was: In der Beauftragung des Backend-Subagenten wurden **beide** Restore-Tests pauschal als „Kategorie-1-Protokolltest nach ADR-S106-3, kein US-Tag" vorgegeben. Für den 404-Test trug das, für den Erfolgs-Test nicht: Er prüft Domänenverhalten (Restore setzt `DeletedAt = null`, Name/Einheit unverändert) und ist damit von Gherkin-Szenario 2 getrieben. Der test-quality-auditor deckte es auf, der Test musste nachträglich auf `US904_HappyPath_…` umgetaggt werden.
  Warum: Die Einordnung wurde für einen ganzen Arbeitspaket-Block auf einmal getroffen, weil beide Tests denselben Endpoint betreffen – das Kriterium ist aber nicht der Endpoint, sondern ob der einzelne Test Protokoll-Mechanik oder Domänenverhalten prüft. Die vom Subagenten übernommene Begründung („das Gherkin-Szenario beschreibt nur UI-Verhalten, nicht diese API-Mechanik") hätte, konsequent angewandt, jeden Backend-Integrationstest von der US-Tag-Pflicht befreit, da Gherkin nie HTTP-Status oder Bodies beschreibt.
  Regel: Traceability-Kategorien (US-Tag ja/nein) pro Test einzeln begründen, nie pauschal für ein Arbeitspaket – und die Begründung daraufhin prüfen, ob sie bei konsequenter Anwendung die Regel selbst aushebeln würde.

- **[MITTEL] [PROZESS] [Gherkin] LL-S108-3 – Frontend-Verhalten ohne treibendes Szenario gebaut, Widerspruch erst durch den User bemerkt**
  Quelle: User
  Was: Der clickaway-Guard des Undo-Toasts wurde als Review-Fix implementiert und getestet, ohne dass ein Gherkin-Szenario ihn forderte – der zugehörige Component-Test trug trotzdem einen `US904_HappyPath_`-Präfix. Kurz zuvor hatte der Orchestrator im selben Lauf einen Backend-Test wegen genau dieses Musters umtaggen lassen. Der User bemerkte den Widerspruch bei der Frage, ob für den nächsten Fix (Toast-Timer) nicht ein Szenario fehle.
  Warum: Review-Findings wurden als „Fix" behandelt und damit implizit von der Outside-In-Pflicht ausgenommen; ein Auditor hatte das fehlende Szenario sogar gemeldet, es wurde aber als ⚠️ eingeordnet statt als Prozessverstoß. Dass der Test einen US-Tag trug, verdeckte die Lücke zusätzlich.
  Regel: Ein Review-Fix, der **beobachtbares Nutzerverhalten** ändert, braucht dasselbe Gherkin-Fundament wie geplante Funktionalität – erst Szenario, dann Test, dann Code. „Kommt aus einem Review-Finding" ist kein Ausnahmegrund.
  Bezug: OBS-S108-2

## Session 112 – 2026-07-31

- **[MITTEL] [PROZESS] [Doku] LL-S112-1 – Gerade diagnostizierten Trigger-Defekt wenige Schritte später selbst reproduziert**
  Quelle: User
  Was: Beim Durchgang durch `docs/tech-debt.md` wurden in Batch A mehrere Einträge als „Phantom-Trigger" identifiziert und korrigiert – Auslöser, die nie eintreten („eigene UX-Foundation-Aufgabe") oder verfallen sind, ohne je gefeuert zu haben („mit run-4"). Wenige Schritte später schrieb der Orchestrator beim Neufassen von TD-S083-2 in Batch B erneut einen Eintrag mit ausformulierter Behebung und ohne jeden Auslöser; der User musste nachfassen: „was ist denn nun der Trigger?".
  Warum: Die Eintrags-Vorlage definiert ein einziges Feld als „geplante Behebung **oder** auslösende Bedingung". Wer die Behebung ausformuliert, hat die Vorlage formal erfüllt – das Fehlen des Auslösers erzeugt keine sichtbare Lücke. Das kurz zuvor gewonnene Wissen über das Muster reichte nicht, um es im eigenen Text zu bemerken.
  Regel: Ein gerade diagnostiziertes Muster schützt nicht davor, es selbst zu wiederholen – solange die Vorlage den Fehler zulässt, ist die eigene Aufmerksamkeit die schwächste Absicherung. Beim Schreiben eines Schuld-Eintrags **Behebung und Auslöser getrennt beantworten**, auch wenn das Feld beides zusammenfasst, und den Auslöser daran prüfen, ob ein konkretes Ereignis ihn auslöst.
  Bezug: OBS-S112-1

- **[MITTEL] [PROZESS] [Doku] LL-S112-2 – Dreimal eine Struktur geändert, ohne vorher deren dokumentierte Regeln zu lesen**
  Quelle: User
  Was: Drei Vorschläge des Orchestrators musste der User zurückweisen, jeweils aus demselben Grund. (1) Das Feld „Behebung/Trigger" in `tech-debt.md` wurde in zwei Felder aufgesplittet – das Eintrags-Format steht im Kopf-Kommentar derselben Datei und wurde nicht gelesen. (2) Der Begriff „als Workshop-Input aufnehmen" wurde ab Batch A wiederholt verwendet, ohne zu prüfen, ob der `gherkin-workshop` `tech-debt.md` überhaupt liest – er tut es nicht, die Skill-Datei enthält kein einziges Vorkommen. (3) Eine ADR sollte eine Abweichung von einer Guideline erklären, statt die Guideline zu korrigieren – der User wies darauf hin, dass die Guideline damit dauerhaft falsch bliebe.
  Warum: In allen drei Fällen wurde auf eine **angenommene** Struktur gebaut statt auf die dokumentierte, obwohl die Regel jeweils in Reichweite lag (Datei-Header, Skill-Datei, die Guideline selbst). Der Auslöser war jedes Mal Schreibdruck: Die Struktur wurde erst beim Schreiben mitgedacht, nicht davor geprüft.
  Regel: Bevor eine Struktur geändert oder ein Mechanismus in Anspruch genommen wird, dessen Regeln woanders stehen – Eintrags-Format, Skill-Schritt, Konvention –, **erst die Quelle lesen, dann schreiben**. Der Test ist billig: „Wo steht, dass es so funktioniert?" Lässt sich das nicht in einem Satz mit Fundstelle beantworten, ist es eine Annahme.
  Bezug: OBS-S112-7

## Session 114 – 2026-08-03

- **[HOCH] [PROZESS] [Kommunikation] LL-S114-1 – Arithmetik auf zitierten Zahlen als eigene Messung ausgegeben**
  Quelle: User
  Was: Für die Gewichtung von OBS-S096-3 wurden fünf Pro-Datei-Zahlen aus dem OBS-Eintrag addiert und durch eine sechste aus demselben Eintrag geteilt; das Ergebnis (Tracker = 9 % des Read-Volumens) trug die Empfehlung zu verwerfen und wurde als `nachgerechnet statt zitiert` präsentiert. Auf Rückfrage des Users, mit welchen Zahlen gerechnet wurde, stellte sich heraus: Es war keine Messung, sondern eine Ableitung aus fremden Angaben – und sie war falsch, weil zwei Einzeldateien für einen ganzen Bereich genommen wurden. Die zurückgeholte Original-Messung ergab 13,5 %.
  Warum: Eine Rechnung auf zitierten Zahlen fühlt sich wie Verifikation an: Man hat etwas selbst getan, und das Ergebnis ist neu. Der entscheidende Unterschied – ob die Eingangsgrößen aus der Realität oder aus einem Dokument stammen – verschwindet dabei, weil beide als Ziffern vorliegen. `principles.md` verlangt Empirie vor Behauptung; die Regel wurde formal befolgt und inhaltlich verfehlt.
  Regel: Eine Rechnung auf fremden Zahlen ist keine Messung. Bevor eine Zahl eine Empfehlung trägt: entweder die Quelle real ausführen, oder sie ausdrücklich als abgeleitet kennzeichnen und die Unsicherheit benennen. Wer ein abgeleitetes Ergebnis als `gemessen` bezeichnet, nimmt sich selbst die Gelegenheit zur Gegenprobe.

- **[HOCH] [PROZESS] [Skill-Nutzung] LL-S114-2 – Kosten einer Vorschrift beziffert, ohne zu prüfen ob sie befolgt wird**
  Quelle: User
  Was: OBS-S111-2 beschreibt, dass `implementing-scenario` den vollständigen ADR-Dump in jede Subagenten-Message vorschreibt. Daraus wurde der aktuelle Preis errechnet (101.722 Zeichen je Message, ~51k Token je Full-Stack-Lauf) und als laufender Kostenposten berichtet. Die Messung der 24 real abgesetzten Schicht-Prompts ergab: größter Prompt 11.099 Zeichen – die Vorschrift wurde nie befolgt, übergeben wurden stets handverlesene IDs. Der Kostenposten existierte nicht; er lag stattdessen bei den `--full`-Aufrufen des Orchestrators, und dort war er im Log unsichtbar, weil große Ausgaben ausgelagert werden.
  Warum: Eine dokumentierte Vorschrift wurde als Beschreibung der Praxis gelesen. Der Eintrag selbst nannte sogar eine Abweichung (`in S111 wurde bewusst davon abgewichen`), was als Einzelfall statt als Hinweis auf den Normalfall gewertet wurde. Dass die S109-Messung Orchestrator-zu-Subagent-Prompts mit nur 1,5 % auswies, hätte den Widerspruch sofort gezeigt – die Zahl lag vor und wurde nicht gegen die eigene Rechnung gehalten.
  Regel: Bevor die Kosten oder der Nutzen einer Vorschrift beziffert werden, am Bestand prüfen ob sie befolgt wird – eine Regel im Skill ist eine Absicht, kein Messwert. Widerspricht die eigene Rechnung einer vorliegenden Messung um Größenordnungen, ist zuerst die Rechnung verdächtig.

- **[MITTEL] [TOOLING] [Hook/Script] LL-S114-3 – Eigenes Klassifikations-Ergebnis ungeprüft als Befund berichtet**
  Quelle: User
  Was: Die neue Session-Klassifikation in `read-breakdown.py` wurde mit ihrer Verteilung berichtet (23 Implementierungs-, 7 Drain-, 2 Retro-Sessions), ohne dass irgendein Ergebnis gegen eine unabhängige Quelle gehalten wurde – geprüft waren nur die 12 Sessions, die der Automatik durchgefallen waren. Der User hielt zwei Retros für wenig und wies auf das Archiv als ableitbare Gegenquelle hin. Die Gegenprobe bestätigte die Retro-Zahl (die beiden Sessions treffen exakt die mtimes der Archiv-Perioden), deckte aber auf, dass `gherkin-workshop` als Implementierung galt – Szenario-Entwurf mit völlig anderem Leseprofil.
  Warum: Das Signal wirkte autoritativ: `attributionSkill` kommt vom Harness selbst, also schien die Zuordnung eine Tatsache statt einer Abbildung zu sein. Übersehen wurde, dass die Tatsache nur der Skill-Name ist – die Zuordnung Skill zu Session-Art ist eine eigene, ungeprüfte Behauptung. Geprüft wurde deshalb nur dort, wo die Automatik sichtbar nichts lieferte, nicht dort, wo sie etwas Falsches lieferte.
  Regel: Ein abgeleitetes Klassifikations-Ergebnis vor dem Berichten gegen eine unabhängige Quelle halten – und dabei gezielt die Fälle ansehen, in denen die Automatik ein Ergebnis geliefert hat, nicht nur die Lücken. Eine plausible Verteilung ist kein Beleg; eine unerwartet kleine Kategorie ist der billigste Einstiegspunkt für die Gegenprobe.

## Session 115 – 2026-08-09

- **[HOCH] [AGENT] [Doku] LL-S115-1 – Empirie-Prinzip nur auf Messungen angewandt, nicht auf Doku- und Ablage-Handlungen**
  Quelle: User
  Was: Fünf User-Korrekturen in einer Session, alle nach demselben Schema: gehandelt, bevor der tragende Fakt geprüft war. (1) Sechs Befehle in `dev-workflow.md` auf `--prefix` umgeschrieben, ohne einen davon auszuführen – erst auf Nachfrage verifiziert (Ergebnis: es funktioniert, aber das war Glück, nicht Wissen). (2) Zur Frage, ob der Re-Trigger von OBS-S091-2 eingetreten ist, dreimal die Aussage gewendet, weil Transkript-Einträge (abgewiesene *Versuche*) mit ALLOW-Log-Zeilen (tatsächliche *Ausführungen*) vermischt wurden; die Quelle wurde erst nach der Behauptung geklärt. (3) `observations.md` direkt editiert statt per Script – sachlich unvermeidbar, weil `obs.py` das Erweitern einer Beobachtung nicht konnte, aber stillschweigend statt benannt. (4) Den Anker-Plan in ein `IN BEOBACHTUNG bis S120` gelegt und behauptet, eine Folgesession könne ohne Neu-Recherche starten – der Status nimmt den Eintrag aber aus dem Drain-Vorschlag, der Plan wäre fünf Sessions unsichtbar gewesen. (5) Den AGENT_MEMORY-Eintrag als Kopie des OBS-Inhalts geschrieben statt als Kurzzusammenfassung mit Verweis.
  Warum: Das Prinzip `Unterstützt ≠ beweist – Empirie vor Behauptung` existiert in `principles.md` und wurde in dieser Session **penibel befolgt** – aber ausschließlich dort, wo es wörtlich adressiert ist: bei Aussagen über Tool- und Messverhalten. Dort lief alles korrekt (Filter-Quote gemessen statt gerechnet, `--since` gebaut um eine Ableitung zu ersetzen, Formatter gegen echte Report-Objekte geprüft, Gate durch temporäres Brechen verifiziert). Die fünf Fehlgriffe lagen sämtlich in einer anderen Klasse von Handlung: Doku schreiben, Zustand ablegen, Information platzieren. Dort fühlte sich nichts wie eine `Behauptung über Tool-Verhalten` an, sondern wie Redaktionsarbeit – und der Selbst-Check sprang nicht an. Verstärkend: Bei (4) und (5) waren die verletzten Regeln sogar wörtlich in `principles.md` vorhanden (Vorlage-Trigger für Zustandsdokumente; Kurzzusammenfassung statt Kopie), was bestätigt, dass nicht Wissen fehlte, sondern die Anwendung – der in `principles.md` selbst notierte häufigste Fehlerursprung.
  Regel: Vor jeder **Doku-Änderung und Ablage-Entscheidung** denselben Selbst-Check fahren wie vor einer Tool-Aussage, mit drei konkreten Fragen: (a) **Befehl/Snippet:** Habe ich ihn in dieser Session ausgeführt? Wenn nein – ausführen oder ausdrücklich als ungeprüft kennzeichnen, nie stillschweigend als gültig hinschreiben. (b) **Beleg:** Bezeugt meine Quelle einen *Versuch* oder eine *Ausführung*? Diese Unterscheidung benennen, bevor daraus ein Schluss wird. (c) **Ablage:** Welcher Mechanismus legt das gerade Abgelegte wieder vor – und ist der Zielstatus mit ihm vereinbar? Zusätzlich: Weiche ich von einer Skill-Vorgabe ab (etwa Datei-Edit statt Script), ist die Abweichung **auszusprechen**, nicht auszuführen.

- **[MITTEL] [PROZESS] [Doku] LL-S115-2 – Erledigtes bleibt in Zustandsdokumenten stehen, weil nur die präventive Regelhälfte einen Auslöser hat**
  Quelle: User
  Was: Der User meldet als periodenübergreifende Beobachtung, dass Agenten wiederholt Dinge erfassen, die bereits erledigt oder nicht mehr relevant sind. Am Bestand belegbar ist bislang die verwandte, aber engere Ausprägung: Die drei per `check-td-capture.py` erzwungenen TD-Punkte in `docs/AGENT_MEMORY.md` tragen je 5–8 Zeilen Volltext-Begründung statt einer Kurzzusammenfassung mit Verweis auf `tech-debt.md` – nicht mehr benötigter Inhalt an einer Stelle, die bei jedem Session-Start vollständig injiziert wird. **Anmerkung aus der S116-Retro:** Der zunächst angeführte zweite Beleg (der Prioritäten-Punkt „alle Läufe der Story US-904 implementiert") trägt **nicht** – die Datei enthält dort den Platzhalter `{{NEXT_RUN}}`, der Text ist gerenderte Ausgabe von `next_run.py` und beschreibt den Zustand korrekt. Der Fehlgriff ist selbst eine Instanz des Musters aus dieser Periode: aus einer gerenderten Ansicht auf den Dateiinhalt geschlossen, ohne die Quelle zu öffnen.
  Warum: CM-S102-1 und das principles.md-Prinzip 'Zustandsdokumente tragen nur den offenen/aktuellen Zustand' nennen beide Richtungen ausdrücklich – präventiv und kurativ. Nur die präventive hat einen Auslöser: Sie greift beim Schreiben eines Eintrags. Die kurative hat keinen; niemand liest ein Zustandsdokument mit der Frage 'ist hiervon inzwischen etwas erledigt?', solange nicht ohnehin ein Anlass dazu besteht. Eine Regel, deren eine Hälfte ohne Auslöser bleibt, wirkt nur zur Hälfte.
  Regel: Beim Schreiben an einem Zustandsdokument nicht nur den eigenen Eintrag prüfen, sondern die berührte Liste einmal danach durchsehen, ob ein Eintrag inzwischen erledigt ist oder nur noch als Verweis nötig wäre – der kurative Teil der Regel braucht denselben Schreib-Trigger wie der präventive.
