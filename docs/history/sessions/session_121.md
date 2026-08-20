# Session 121 – 2026-08-20

**Phase:** SKELETON | **Art:** OBS-Drain – Bash-Permission-Umbau, Hook-Deduplizierung, OQ-Fälligkeitspflicht

Reiner Drain-Durchlauf ohne Produktionscode. Fünf Einträge aufgelöst (Backlog 29 → 24), drei davon
umgesetzt, zwei verworfen. Schwerpunkt war `check-bash-permission.py`: Der Hook lehnte Befehle nach
ihrer Formulierung statt nach ihrem Inhalt ab und übersah dabei eine Lücke, durch die er seinen
eigenen Zweck verfehlte.

Die Bewertung stützte sich durchgehend auf Messungen an den Permission-Logs und den Session-Logs,
nicht auf die Beschreibungen in den Einträgen – in drei von fünf Fällen wichen die dort behaupteten
Fakten vom aktuellen Stand ab.

---

## A – OBS-S111-4: Bash-Hook lehnte nach Formulierung statt nach Inhalt ab

**Analysebasis.** Der erste Anlauf wertete nur `denied-commands.log` aus und trug nicht; der User
korrigierte die Basis dreimal (→ LL-S121-2). Belastbar wurde sie erst mit drei Richtungen, geschnitten
am letzten größeren Umbau (8016a76, S096): was wurde geblockt, was per `--allow-once` freigegeben,
und was geschah danach.

Ergebnis über 354 Rückfragen/Denies gegen 3126 Allows:

| Ausgang eines harten Denies | n | Anteil |
|---|---|---|
| anderer erlaubter Befehl → Umweg gefunden | 137 | 61 % |
| gleiche Signatur kurz darauf erlaubt → nur die Formulierung war das Problem | 37 | 16 % |
| erneut mit `--allow-once` → keine Alternative | 33 | 14 % |
| nichts binnen 180 s → aufgegeben | 16 | 7 % |

Der Hook blockierte also fast nie ein Ziel, er verteuerte es. Aus 57 Transcripts ließen sich 124
`--allow-once`-Aufrufe auflösen: 115 ausgeführt, 4 abgelehnt – und keine der vier war eine
Sicherheitsablehnung, alle waren Themenwechsel oder ein bewusster Test.

**Umgesetzt.** Der Splitter zerlegt jetzt auch Newline, Heredoc-Bodies (als Daten), Zuweisungspräfixe,
`$(…)`/Backtick/Prozess-Substitution, `for`/`while`-Rümpfe sowie `find -exec` und `xargs`; jedes
Teilstück wird einzeln geprüft (`expand_segment`). Das Session-Scratchpad ist Schreibziel und
`python3`-Ort, `.claude/tmp/` nicht mehr. String-Argumente nicht-ausführender Befehle werden vor der
Wrapper-Pflicht maskiert (`mask_data_strings`) – eine Erwähnung ist keine Ausführung. Neu erlaubt:
`awk`, `printf`, `test`/`[`, `date` mit Argument, `xargs` generisch, `docker compose config`,
`git check-ignore`.

**Neue Sperren**, damit die Öffnung kein Loch wird: indirekte Ausführung (`$CMD`, `eval`, `bash -c`)
blockt hart; Dateioperationen im Schleifenrumpf und in `-exec`/`xargs` blocken ohne Eskalation; kein
prüffähiges Kommando bedeutet deny statt durchwinken.

**Verworfen.** `python3 -c` freizugeben – es gibt keinen verlässlichen Weg, ein lesendes von einem
schreibenden Script zu unterscheiden; eine AST-Whitelist wäre lückenhaft und der Scratchpad-Weg ist
ohnehin besser. Ebenso die Verschärfung von `mv`/`cp` auf Projektziele (User-Entscheidung: bisher kein
Problem, git als Netz).

**Vorbestehende Lücke gefunden und geschlossen (→ LL-S121-3).** Ohne Newline als Segmenttrenner war
jeder mehrzeilige Befehl ein Segment; da Allow-Muster per `.search()` greifen, erlaubte eine passende
erste Zeile den gesamten Rest. Gegen die HEAD-Fassung verifiziert:

```
alt=allow  neu=deny   'ls -la\nrm -rf /tmp/x'
alt=allow  neu=deny   'git status --short\nrm -rf Client/'
alt=allow  neu=deny   'echo hallo\ngit push --force'
```

Unbemerkt blieb das, weil mehrzeilige Befehle praktisch immer mit `VAR=` oder `for` beginnen – der
Deny kam zufällig zustande, nicht durch Prüfung.

**Verifikation.** 662 Tests grün, davon ein neuer Block Guard-Tests mit Gegenprobe je Freigabe.
Replay der historischen Befehle: 57 von 214 harten Denies wären jetzt erlaubt; 30 von 3147 Allows
blocken neu, davon 18 gewollte `.claude/tmp`-Redirects. Dazu Live-Proben am laufenden Hook.

## B – OBS-S119-2: Hook-Duplikation und Beispiel-ID-Kollisionen

Beide Behauptungen des Eintrags wurden am Code geprüft, eine musste korrigiert werden: `main()` ist
**nicht** in fünf Hooks wortgleich (11 Varianten in 12 Dateien) – die Vorprägung baute mit ihrem
`run(check_fn, prefix)`-Wrapper auf derselben falschen Annahme auf und wurde nicht übernommen.

**(a)** `read_file_text` und `compute_post_content` nach `.claude/hooks/_hook_io.py` extrahiert, fünf
capture-Hooks importieren daraus. Redundanz 99 → 35 Zeilen. Die abweichende
`compute_post_content`-Variante in `check-ref-direction.py` und `check-e2e-scenario-ref.py` blieb außen
vor – sie zusammenzulegen hieße, eine Signatur umzubauen.

Ursprünglich wollte ich `read_file_text` als trivial ausklammern; auf Nachfrage des Users verworfen,
weil der Kopplungspreis durch das ohnehin entstehende Modul schon bezahlt ist und eine halbe
Extraktion Willkür hinterließe.

**(b)** Der Eintrag nannte einen betroffenen TD-Eintrag; gemessen wären **8 von 30** aktiven TD-/OQ-Einträgen
bei ihrer Löschung blockiert gewesen, im schwersten Fall durch 34 Fundstellen ohne einen einzigen
echten Verweis. Gelöst über `_SKIP_PREFIXES` in `check-dangling-refs.py`: Tooling-Testverzeichnisse
werden nicht mehr gescannt, weil IDs dort Fixtures sind. Danach 0 blockierte Einträge, echte Verweise
aus Produktionsscripten bleiben erhalten. Verworfen: das Umstellen der Beispiel-IDs auf reservierte
Nummernräume (50 Fundstellen Aufwand, läuft beim nächsten Fixture wieder auf).

Zwei Selbsttreffer unterwegs: Mein Erklärkommentar nannte zunächst eine aktive TD-ID und hätte deren
Löschung blockiert – die Fehlerklasse, die der Fix behebt. Und die geplante Mehrdatei-Ersetzung der
fünf Blöcke wurde durch die vorherige Byte-Identitäts-Prüfung verhindert: es waren drei Varianten,
weil in zwei Dateien andere Funktionen dazwischenliegen.

## C – OBS-S117-4: `Fällig` bei offenen Fragen ist jetzt Pflicht

Der Eintrag war zu großen Teilen überholt – seit S119 nutzen offene Fragen dieselbe Anker-Grammatik wie
Tech-Debt, `check-oq-capture.py` prüft einen gesetzten Anker, und die genannten Belege wurden in S118
geklärt. Übrig blieb: Das Feld war **optional**, wer es wegließ fiel auf die Altersregel zurück. Beleg
am Bestand ist `OQ-S094-2` – ohne Termin, seit 27 Sessions in jeder Session vorgelegt, ohne dass die
Wiederholung von der ersten Vorlage unterscheidbar wäre.

Der Hook erzwingt das Feld jetzt; der Format-Header von `open-questions.md` ist nachgezogen. Verworfen:
ein Vermerk „Zuletzt vorgelegt: S<NNN>" beim Session-Abschluss – Buchhaltung ohne Konsequenz.

## D – Verworfen: OBS-S120-4, OBS-S099-2, OBS-S110-2

**OBS-S120-4** (kein Werkzeug für Mehrdatei-Ersetzung): Der S120-Schaden entstand nicht beim Ersetzen,
sondern beim Prüfen gegen die falsche Baseline. Gegen ein eigenes Werkzeug sprachen drei Einwände des
Users, der dritte empirisch gestützt: `grepdll.py` bis `grepdll6.py` zeigen, dass ein starres
Wegwerf-Script iterativ zurechtgebogen wird.

**OBS-S099-2** (manuelle Zustandshaltung der Test-Freigabe-Anker): Die vorgeschlagene Alternative hätte
den Mechanismus entwertet – seine Schutzwirkung beruht darauf, dass der *Orchestrator* den Wert hält;
eine Datei im Arbeitsbaum kann der geprüfte Subagent selbst überschreiben. Nach ~22 Sessions in der
Alters-Lane bewusst verworfen statt ein drittes Mal vertagt.

**OBS-S110-2** (Subagent kehrt nicht zurück): Die Wiederaufnahme ist inzwischen in
`implementing-scenario` beschrieben. Der Restschaden – der Return als einziger Träger einer Doku-Pflicht –
ist **nicht** durch die vorhandenen Checks abgedeckt (`decisions.py` und `qa-check` Check 6 arbeiten auf
ID-Ebene, der Schaden war ein Verweis auf einen nie geschriebenen Abschnitt *innerhalb* einer
existierenden ADR). Trotzdem verworfen: Ein Abschnitts-Check müsste aus Prosa erraten, welcher Abschnitt
gemeint ist, und erzeugte vor allem Fehlalarme.

## E – Aufräumen und Doku-Nachzug

`.claude/tmp/` enthält nur noch die beiden Permission-Logs (28 Altlasten entfernt, darunter die sechs
`grepdll`-Varianten). Alle Verweise auf das Verzeichnis wurden repo-weit geprüft und die fünf stale
Stellen korrigiert: `workflow-auditor.md`, `review-docs/SKILL.md` (3×) und die Redirect-Doku im Hook.
`dev-workflow.md` erklärt jetzt Scratchpad und die zulässigen zusammengesetzten Befehle.

Ein beschädigter Tracker-Eintrag wurde repariert – das Feld `Entscheidung/Maßnahme` war in die
Beobachtungszeile gerutscht, wodurch `obs.py set` es nicht mehr fand (→ LL-S121-1, OBS-S121-1). Eine
Prüfung über alle Tracker und das Archiv ergab genau diesen einen Fall.

---

## Learnings & Beobachtungen

- **LL-S121-1** – Tracker-Schreibscript zerstörte einen Eintrag strukturell, Schaden fiel erst zehn
  Sessions später auf. Details: `docs/kaizen/lessons_learned.md`.
- **LL-S121-2** – Gemessen wurde, wofür Daten dalagen, nicht was die Frage beantwortet. Ebenda.
- **LL-S121-3** – 810 Zeilen Hook-Tests übersahen, dass der Hook seinen eigenen Zweck verfehlte. Ebenda.
- **OBS-S121-1** – Schreibscripte prüfen die Eintragsstruktur nach dem Schreiben nicht.
  Details: `docs/kaizen/observations.md`.
- **OBS-S121-2** – Drain-Rate und Backlog-Ziel widersprechen sich (fester Satz gegen variablen
  Zielwert). Ebenda.
- **OBS-S121-3** – Session-Dateien werden zu vier Fünfteln nie gelesen; Erfassung unmechanisiert.
  Ebenda.
