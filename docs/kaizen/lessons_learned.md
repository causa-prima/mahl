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

- **[HOCH] [AGENT] [Subagenten] LL-S108-1 – Beide Frontend-Subagenten endeten ohne Übergabe-Report; passives Warten sah dabei korrekt aus**
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
