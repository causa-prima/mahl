# Guideline für Python – der Prozess-Code unter `.claude/**`

<!--
wann-lesen: Bevor du Python schreibst oder änderst – Scripts unter .claude/scripts, Hooks und Checks unter .claude/hooks (nach docs/guidelines/coding-guideline-general.md)
kritische-regeln:
  - Ein Guard ist erst fertig, wenn er einmal absichtlich gebrochen und beim Anspringen gesehen wurde
  - Jede Änderung an .claude/** fährt die Werkzeug-Suite; rot bleiben ist keine Option
  - Werkzeuge laufen über ihre Wrapper in .claude/scripts, nie direkt aus .venv/bin
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

Diese Guideline gilt für **Python unter `.claude/**`** – rund 15.000 Zeilen Scripts, Hooks und
Checks, abgesichert durch gut 1.000 Tests. Dieser Code ist kein Produkt: Er hat keinen
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

**Tests sind Pflicht, und sie laufen von selbst.** Jede Änderung an `.claude/scripts` oder
`.claude/hooks` fährt die gesamte Werkzeug-Suite (PostToolUse, `checks/tooling_tests.py`).
Rot bleiben ist keine Option; eine bewusste RED-Phase ist es, aber nur bis zum nächsten Schritt.
Dasselbe gilt für die **Injektionsquellen** des Session-Starts – `docs/kaizen/principles.md`
löst die Suite mit aus, weil dort der Text wächst, den ein Guard misst.

**Der Linter läuft automatisch.** `ruff` prüft jede geänderte Datei (PostToolUse,
`checks/ruff_lint.py`); der volle Lauf ist `python3 .claude/scripts/ruff-run.py`. Die
Regelauswahl steht mit Begründung in `ruff.toml` und ist bewusst schmal: Fehlerregeln ja, Stil
nein. **Jede `# noqa`-Suppression trägt eine Begründung im Code** – dieselbe Regel wie für
`[ExcludeFromCodeCoverage]` im Produktcode.

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
(`python3 .claude/scripts/guard-stats.py`). Ein Guard ohne jede Auslösung ist **entweder kaputt
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

`jscpd` erfasst Python mit (`jscpd.config.json`). Der Bestand liegt bei **0,25 %**; die
verbleibenden Funde sind Import-Bootstrap (`sys.path.insert` vor dem ersten Import), der sich
nicht extrahieren lässt. Der Wert wird beobachtet, nicht als Schwelle erzwungen – ein Werkzeug,
das dauerhaft rot meldet, wird nach zwei Wochen ignoriert und meldet dann auch echte Funde
wirkungslos. **Steigt der Wert deutlich, ist das der Anlass zu schauen.**

---

<a id="CGP-was-nicht-gilt"></a>
## Was nicht gilt – und warum

Diese Regeln des Produktcodes werden **bewusst nicht** übernommen. Der Grund steht dabei, damit
niemand sie später als Versehen nachrüstet:

| Nicht übernommen | Grund |
|---|---|
| **User Stories / Gherkin-Szenarien** | Es gibt keinen externen Nutzer. Das Sollverhalten steht in `docs/process/` und den Skills; Szenarien wären eine zweite Ablage, die driftet. |
| **100 % Branch-Coverage als Gate** | Coverage misst berührte Zeilen. Klasse STUMM hat 100 % Coverage und wirkt trotzdem nicht – die Zahl beantwortet die Frage nicht, die hier zählt. Als *Metrik* ist sie zulässig, um Testlücken zu finden; als *Gate* nicht. |
| **100 % Mutation Score** | Mutation-Testing trifft Klasse LAUT, die bereits gedeckt ist. Der einzige echte Fund in S128 (`zip()` ohne `strict=`, das eine Regression still falsch rechnen ließ) kam vom Linter, nicht von einer Mutation – der Fehler lag in einer fehlenden Zusicherung, nicht in einer Bedingung. |
| **Stil-Linting** (Import-Sortierung, Modernisierung) | Erzeugt Diff-Rauschen an Dateien, die sonst niemand anfasst, ohne je einen Fehler zu verhindern. |

---

<a id="CGP-werkzeuge"></a>
## Werkzeuge

Alles Nötige liegt in einem venv im Repo-Root, hergestellt aus `requirements-dev.txt`.
Aufgerufen wird **immer über die Wrapper** in `.claude/scripts` – `.venv/bin/ruff` steht nicht
auf der Bash-Allow-Liste, und die Wrapper liefern ein Verdikt statt Rohausgabe.

Einrichtung, Befehle und der Grund für das venv (PEP 668):
[`dev-workflow.md`, Python-Werkzeuge](../process/dev-workflow.md#DEV-python-werkzeuge).
