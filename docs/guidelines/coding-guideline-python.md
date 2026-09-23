# Guideline für Python – der Prozess-Code unter `prozesscode/`

<!--
wann-lesen: Bevor du Python schreibst oder änderst – Werkzeuge, Hooks und Checks liegen alle unter prozesscode (nach docs/guidelines/coding-guideline-general.md)
kritische-regeln:
  - Ein Guard ist erst fertig, wenn er einmal absichtlich gebrochen und beim Anspringen gesehen wurde
  - Jede Änderung an prozesscode/ fährt die Werkzeug-Suite; rot bleiben ist keine Option
  - Werkzeuge laufen über ihre Wrapper in prozesscode, nie direkt aus .venv/bin
  - Meldungen eines Guards sagen, was zu tun ist – nicht nur, was falsch ist
-->

<a id="CGP-inhalt"></a>
## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| [Geltungsbereich](#CGP-geltungsbereich) | Was dieser Code ist und was ihn von Produktcode trennt | Einmal, zum Einordnen |
| [Das Fehlerprofil](#CGP-fehlerprofil) | Warum hier andere Maßgaben gelten als für C#/TypeScript | Vor jeder Diskussion über Qualitätswerkzeuge |
| [Was gilt](#CGP-was-gilt) | Tests, Linter, Gegenprobe, Protokoll | Bevor du etwas schreibst |
| [Was nicht gilt](#CGP-was-nicht-gilt) | Bewusst nicht übernommene Produktcode-Regeln, mit Grund | Wenn du eine Regel vermisst |
| [Werkzeuge](#CGP-werkzeuge) | venv, ruff, Wrapper | Beim ersten Aufsetzen |

---

<a id="CGP-geltungsbereich"></a>
## Geltungsbereich

Diese Guideline gilt für **Python unter `prozesscode/`** – rund 15.000 Zeilen Werkzeuge, Hooks
und Checks, abgesichert durch gut 1.000 Tests. Der Code liegt seit S129 in einem Paket und
nicht mehr unter `.claude/`; der Grund steht in `prozesscode/__init__.py` und läuft darauf
hinaus, dass ein Verzeichnis mit führendem Punkt kein Modulpfad sein kann – und Mutationstests
genau den brauchen. Dieser Code ist kein Produkt: Er hat keinen
externen Nutzer, keine User Story und kein Release. Er **steuert den Arbeitsprozess**, und
genau daraus folgen seine Maßgaben – nicht aus einer abgeschwächten Fassung der
Produktcode-Regeln.

Für C#/TypeScript gelten `coding-guideline-csharp.md` bzw. `-typescript.md` samt 100 %
Branch-Coverage und 100 % Mutation Score. Diese Zahlen gelten hier **nicht** – warum, steht
unter [Was nicht gilt](#CGP-was-nicht-gilt).

---

<a id="CGP-fehlerprofil"></a>
## Das Fehlerprofil: zwei Klassen, eine davon stumm

Der Unterschied zum Produktcode ist keine Frage der Wichtigkeit, sondern der **Art, wie Fehler
sich zeigen**. Produktcode kennt praktisch eine Fehlerklasse; Prozess-Code kennt zwei:

**Klasse LAUT** – das Werkzeug stürzt ab oder liefert Unsinn. Es fällt in derselben Minute auf
und kostet eine Korrekturschleife. Diese Klasse ist durch die Test-Suite und den automatischen
Lauf bei jeder Änderung gut gedeckt.

**Klasse STUMM** – der Guard läuft fehlerfrei durch, prüft aber nicht mehr, was er prüfen soll,
oder seine Wirkung tritt nicht ein. **Nichts schlägt fehl.** Der Ausfall zeigt sich Sessions
später als durchgerutschter Fehler und sieht dann aus wie ein Agentenfehler, nicht wie ein
Werkzeugfehler.

Drei belegte Fälle aus S128, alle in derselben Session gefunden:

- `session-agenda.py` war fehlerfrei und gut getestet – ihre Ausgabe überschritt den
  10.000-Zeichen-Cap des Runtimes, wurde durch eine Vorschau ersetzt, und die Session-Agenda
  kam **in keiner Session an**. Kein Test hätte das gefangen: Der Fehler lag an der
  Schnittstelle, nicht im Code.
- `doc.py` las eine eingerückte Beispiel-Überschrift als echte und lieferte bei
  `get KPI-doku-referenzen` **18 % des Abschnitts** – ohne Fehler, ohne Kürzungshinweis, an
  syntaktisch unauffälliger Stelle.
- `jscpd.config.json` ignorierte `Server/Migrations/**`; die Migrations liegen in
  `Infrastructure/`. Der Eintrag sah richtig aus und traf nichts.

**Die Konsequenz für jede Werkzeug-Entscheidung:** Zuerst fragen, welche Klasse eine Maßnahme
adressiert. Mehr Tests, mehr Coverage und Mutation-Testing wirken auf LAUT – die bereits
gedeckte Klasse. Gegen STUMM hilft nur, die **Wirkung** zu prüfen und Auslösungen zu zählen.

---

<a id="CGP-was-gilt"></a>
## Was gilt

**Tests sind Pflicht, und sie laufen von selbst.** Jede Änderung an `prozesscode` oder
`prozesscode/hooks` fährt die gesamte Werkzeug-Suite (PostToolUse, `checks/tooling_tests.py`).
Rot bleiben ist keine Option; eine bewusste RED-Phase ist es, aber nur bis zum nächsten Schritt.
Dasselbe gilt für die **Injektionsquellen** des Session-Starts – `docs/kaizen/principles.md`
löst die Suite mit aus, weil dort der Text wächst, den ein Guard misst.

**Der Linter läuft automatisch.** `ruff` prüft jede geänderte Datei (PostToolUse,
`checks/ruff_lint.py`); der volle Lauf ist `python3 -m prozesscode.ruff-run`. Die
Regelauswahl steht mit Begründung in `ruff.toml` und ist bewusst schmal: Fehlerregeln ja, Stil
nein. **Jede `# noqa`-Suppression trägt eine Begründung im Code** – dieselbe Regel wie für
`[ExcludeFromCoverageGate]` im Produktcode.

<a id="CGP-gegenprobe"></a>
### Die Gegenprobe – ein Guard ist erst fertig, wenn er angesprungen ist

Nach dem Bauen oder Ändern eines Prüfmechanismus (Hook, Gate, Guard, Wrapper): **einmal
absichtlich brechen und bestätigen, dass er anspringt.** Ein grüner Test zeigt, dass der Aufbau
lief – nicht, dass er das Fragliche geprüft hat. Und ein Mechanismus, der nichts prüft, fällt
per Definition lautlos aus.

Praktisch: eine Wegwerfdatei anlegen, die den Fehlerfall enthält, die Meldung sehen, Datei
löschen. Das kostet zwei Minuten und ist der einzige Beleg, den es für Klasse STUMM gibt.
Die Regel steht kanonisch in
[`principles.md`](../kaizen/principles.md#KPI-kommunikation) – hier steht sie, weil sie beim
Schreiben von Guards der wichtigste Einzelschritt ist.

<a id="CGP-guard-protokoll"></a>
### Guards protokollieren ihre Auslösungen

Jeder Guard meldet beim Anschlagen seine Identität (`checks/guard_log.py`); die Dispatcher tun
das zentral, ein neuer Guard erbt es also. Gesichtet wird der Bestand in der Retro
(`python3 -m prozesscode.guard-stats`). Ein Guard ohne jede Auslösung ist **entweder kaputt
oder überflüssig** – von außen nicht unterscheidbar, also prüfen statt annehmen.

Zwei Regeln dazu:

- **Das Protokoll ist fail-open.** Ein Schreibfehler darf niemals einen blockierenden Guard
  mitreißen; sonst beschädigt die Messung den Mechanismus, den sie überwacht.
- **Tests schreiben nie hinein.** Eine `autouse`-Fixture in `conftest.py` lenkt das Protokoll
  um. Ohne sie zählt das Messinstrument die eigenen Tests mit – in S128 tatsächlich passiert.

<a id="CGP-meldungen"></a>
### Meldungen sagen, was zu tun ist

Ein Guard, der unverständlich scheitert, wird abgeschaltet statt repariert. Jede Meldung nennt
deshalb den **herstellenden Befehl** oder den Ausweg, nicht nur den Befund – so wie
`ruff-run.py` bei fehlendem venv die beiden Zeilen ausgibt, die es anlegen.

<a id="CGP-duplikate"></a>
### Duplikate: gemessen, nicht als Gate

`jscpd` erfasst Python mit (`jscpd.config.json`), gefahren über
`python3 -m prozesscode.jscpd-run`. Duplikate werden beobachtet, nicht als Schwelle
erzwungen – ein Werkzeug, das dauerhaft rot meldet, wird nach zwei Wochen ignoriert und meldet
dann auch echte Funde wirkungslos.

Damit ein grüner Lauf trotzdem etwas aussagt, misst der Wrapper nicht die Menge, sondern den
**Zuwachs**: Die Klone, die der Bestand kennt, stehen als `BEKANNTE_KLONE` im Wrapper – jeder
mit dem Grund, warum er sich nicht auflösen lässt. Anschlagen kann nur ein neues Dateipaar oder
ein zusätzlicher Fund in einem bekannten. Löst sich ein Klon auf, sagt der grüne Lauf an, dass
die Baseline zu kürzen ist.

Der Bestand ist fast durchweg derselbe Fall: der Schlussabsatz des Hook-Docstrings, der
Import-Block und der `sys.path.insert`-Bootstrap davor. Nichts davon ist extrahierbar – der
Bootstrap muss dem ersten Import vorausgehen, und ein Docstring gehört an die Datei, die er
beschreibt. **Ein neuer Baseline-Eintrag ist die Ausnahme:** Lässt sich ein Klon extrahieren,
ist der Fund die Aufgabe.

---

<a id="CGP-was-nicht-gilt"></a>
## Was nicht gilt – und warum

Diese Regeln des Produktcodes werden **bewusst nicht** übernommen. Der Grund steht dabei, damit
niemand sie später als Versehen nachrüstet:

| Nicht übernommen | Grund |
|---|---|
| **User Stories / Gherkin-Szenarien** | Es gibt keinen externen Nutzer. Das Sollverhalten steht in `docs/process/` und den Skills; Szenarien wären eine zweite Ablage, die driftet. |
| **100 % Branch-Coverage als Gate** | Coverage misst berührte Zeilen. Klasse STUMM hat 100 % Coverage und wirkt trotzdem nicht – die Zahl beantwortet die Frage nicht, die hier zählt. Als *Metrik* ist sie zulässig, um Testlücken zu finden; als *Gate* nicht. |
| **100 % Mutation Score als Gate** | Ein Volllauf mutiert 11.606 Stellen gegen eine 1.100er-Suite: Stunden, also kein Hook. Die *Sichtung* dagegen ist wertvoll – und trifft, anders als hier bis S128 vermutet, genau Klasse STUMM: Ein überlebender Mutant in einem Guard heißt, dessen Prüfung lässt sich ändern, ohne dass ein Test es merkt. In S129 direkt gemessen, sobald der Code als Paket erreichbar war: In `check-td-capture` überlebten 10 von 105 bewerteten Mutanten, 11 weitere Stellen berührt **kein** Test – darunter die `main()` **jedes** Hooks, also die Funktion, die stdin liest und den Exit-Code setzt. Nicht mitgezählt sind 38 Mutanten an Meldungstexten: mutmut umschließt den Text mit `XX…XX`, der Originaltext bleibt Substring, und ein `in`-Test kann so einen Mutanten prinzipiell nicht töten (Details: `mutmut-run.string_mutanten`). Werkzeug: `python3 -m prozesscode.mutmut-run --mutate <modul> [--ratchet]`. |
| **Stil-Linting** (Import-Sortierung, Modernisierung) | Erzeugt Diff-Rauschen an Dateien, die sonst niemand anfasst, ohne je einen Fehler zu verhindern. |

---

<a id="CGP-werkzeuge"></a>
## Werkzeuge

Alles Nötige liegt in einem venv im Repo-Root, hergestellt aus `requirements-dev.txt`.
Aufgerufen wird **immer über die Wrapper** in `prozesscode` – `.venv/bin/ruff` steht nicht
auf der Bash-Allow-Liste, und die Wrapper liefern ein Verdikt statt Rohausgabe.

Einrichtung, Befehle und der Grund für das venv (PEP 668):
[`dev-workflow.md`, Python-Werkzeuge](../process/dev-workflow.md#DEV-python-werkzeuge).
