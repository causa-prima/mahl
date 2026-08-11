# Session 117 – 2026-08-11

**Phase:** SKELETON | **Art:** OBS-Drain (2 Einträge) mit Tooling-Umbau

---

## Drain-Ergebnis

- **OBS-S112-3** (kein anerkannter Pfad für Infra-Arbeit ohne treibendes Szenario) → `tdd-process.md`: kurzer Absatz, dass TDD unverändert läuft und nur die äußere Schleife entfällt – die prüfbare Anforderung wird aus der fordernden Quelle abgeleitet, das RED liefert ein Querschnitts-/Infra-Test nach ADR-S106-3.
- **OBS-S099-1** (verwaiste Infra-TD bleibt unentdeckt) → nicht wie ursprünglich vorgeschlagen alters-, sondern **ankerbasiert** gelöst. Die alterbasierte Fassung wurde an allen 20 TD-Einträgen gemessen und verworfen: jede Schwelle ≤ 16 hätte 15 von 17 markiert.

## Anker-Grammatik für Fälligkeiten

Neu `td_anchors.py` als kanonische Quelle; `**Fällig:** <Anker>[, <Anker>…] – <Prosa>` mit den Ankern `jetzt`, `Phase:X`, `S<NNN>`, `Szenario:„…"`, `US-NNN`, `TD-S<NNN>-<n>`. Kernregel: Mindestens ein Anker muss **terminieren** (sagen WANN); `US-NNN` und ein `Szenario:` ohne Lauf-Zuordnung tun das nicht und verlangen einen Backstop. `TD-`-Ketten erben und werden zyklensicher aufgelöst (TD-S090-2 ↔ TD-S101-1 verwiesen real wechselseitig aufeinander).

Alle 17 ereignisbasierten `Fällig:`-Zeilen in `docs/tech-debt.md` migriert; `check-td-capture.py` validiert beim Schreiben, `td_due.py` meldet eingetretene Anker beim Session-Start und in `implementing-scenario` Schritt 6.1.

Zwei Korrekturen des Users an meiner Analyse, beide Survivor-Bias: Szenario-Anker waren historisch der **häufigste** Auslöser behobener TDs (im Archiv belegt), und ein `Szenario:` muss nicht existieren – dann nimmt man die Story. Daraus die Einsicht, dass `Szenario:` und `US-NNN` prä-/post-Workshop-Granularitäten desselben Ankers sind.

## session-agenda.py ersetzt session-start.sh

Modularer, prioritätsbasierter Zusammenbau des Session-Starts. Rangfolge, Modulschnitt und Begründungen kanonisch in `docs/kaizen/process.md`, Abschnitt „Session-Agenda". Zehn Module; `open_questions.py` aus `obs-drain.py` herausgelöst (anderer Tracker, anderer Ausgang), `obs-drain.py` trägt wieder nur OBS.

Bewusst **keine** Extremschwellen in der Rangfolge: An den vier verfügbaren Messpunkten (S114–S117) sind Backlog-Stand und Jenga-Score bei S116 konfundiert – eine unkalibrierbare Schwelle kostet dasselbe wie keine, zusätzlich aber Pflege.

`next-run` löst story-gebunden auf; das neue Modul `ungeplante-szenarien` macht sichtbar, was geschrieben ist, aber auf keinem Weg vorgelegt wird (aktuell 8 Szenarien). Beide Hälften nötig – ohne Filter behauptet die Agenda Arbeit, mit Filter Vollständigkeit.

### Formüberarbeitung nach User-Durchsicht

Nach direkter Durchsicht der Ausgabe: „Marschbefehl" → „Nächste Aufgabe"; die zusammenfassende Kopfzeile entfernt (sie doppelte den Inhalt darunter), wodurch jeder Modulinhalt selbsterklärend sein muss; `⚠ Backlog überfüllt` aus `obs-drain.py` entfernt (Priorisierung leistet jetzt die Rangfolge); Platzhalter `<name>` erklärt; HTML-Kommentare aus `principles.md` gestrippt; Rahmen zuerst, Agenda zuletzt mit Zustand/Aufgabe/Einzeiler zusammenhängend; `priorities` zeigt nur den obersten Punkt voll.

Injektion 18.812 → 12.380 Bytes. 568 Tooling-Tests grün.

## Learnings & Beobachtungen

- LL-S117-1: Element wegen einer Wirkung entfernt, ohne seine Funktionen vorher zu trennen.
- OBS-S117-1 bis -4 neu erfasst; OBS-S117-1 teilweise umgesetzt (Sichtbarkeit ja, Einplanungsregel offen). OBS-S111-4 um eine dritte Ausprägung erweitert (Ort statt Formulierung), OBS-S116-1 um einen stillen Korruptionspfad (Backticks in einem Script-Argument wurden von der Shell ausgeführt, das Script quittierte trotzdem Erfolg).
- OBS-S117-4 entstand beim Abschluss aus einer Nachfrage des Users: Offene Fragen haben seit S115 eine Vorlage, aber keinen erzwungenen Ausgang. Der Befund lag bis dahin nur als Nebensatz in OBS-S117-2 (Thema dort: Übergabe an den User) und wäre bei dessen Auflösung mit ins Archiv gewandert; die dortige Begründung war zudem falsch und wurde korrigiert.
- Verworfen statt erfasst: eine Beobachtung zur nicht mechanisch prüfbaren Selbsterklärungs-Pflicht der Agenda-Module – einziger realistischer Drain-Ausgang wäre „nicht mechanisierbar" gewesen (Noise-Filter).

Volltext: `docs/kaizen/lessons_learned.md`, `python3 .claude/scripts/obs.py get <ID>`.
