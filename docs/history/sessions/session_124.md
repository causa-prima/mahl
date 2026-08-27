# Session 124 – 2026-08-25/27

**Phase:** SKELETON | **Art:** OBS-S112-7 – Abschnitts-Anker statt Prosa-Verweise

Verweise zwischen Projektdokumenten standen als Prosa („§2", „Sektion Security", „Schritt 4").
Kein Werkzeug konnte prüfen, ob das Ziel existiert; Verweise starben unbemerkt in beide
Richtungen. Diese Session ersetzt sie durch geprüfte Anker, entfernt die Nummern, gegen die
sie zeigten, und sichert beides mechanisch ab. Der größere Teil der Arbeit entstand danach:
Der User trieb die Vollständigkeitsfrage durch vier Runden, und jede Runde förderte Fälle
zutage, die die vorige für erledigt gehalten hatte.

---

## Anker statt Prosa

Format nach User-Entscheid: HTML-Anchor über der Überschrift, Verweis als echter
Markdown-Link. Bewusst kein Eigenbau-Marker – der wäre grep-bar, aber nicht klickbar
gewesen; das Repo liegt auf GitHub. Ebenso verworfen: GitHubs Auto-Anchors, die sich aus dem
Titeltext ableiten und bei jeder Umbenennung brechen. Prüfer ist `.claude/scripts/anchors.py`
(Modul + CLI) samt PreToolUse-Hook `check-anchors.py`, der drei Richtungen deckt: Verweis
ohne Ziel, Link auf die falsche Datei, gelöschter Anker mit verbliebenen Verweisen.

## Die Nummern selbst

Auf die Frage, was die Nummern eigentlich tragen, blieb wenig übrig: Ein Name sagt, *wohin*
man springt, eine Nummer nur, *wie weit*. Entschieden wurde, alle selbstvergebenen Nummern
durch Namen zu ersetzen – Überschriften, Verweistexte, Absatz-Leads. Legitim bleibt allein
**fremdbestimmte** Nummerierung (RFC, Norm, Gesetz); „steht in einer anderen Datei" zählt
nicht, eine ADR-Punktnummer schreiben dieselben Autoren. Dieses Urteil fiel erst, nachdem
ein Prüfer-Subagent die ursprüngliche Begründung als Kategorienfehler widerlegt hatte.

Zwei Verweise lagen bereits tot im Bestand („kaizen Schritt 5" für einen Schritt 7,
„Script-Output Abschnitt 9" ohne Entsprechung) – der Beleg dafür, dass das Problem kein
hypothetisches war. Bis zum Ende der Session kamen drei weitere hinzu: ein „Guideline 6"
ohne Ziel (aus S072–076), zwei Verweise auf einen Retro-Berichtsabschnitt, den diese Session
selbst umbenannt hatte, und ein Verweis auf Code-Zeilennummern, die längst verschoben waren.

## Poka-Yoke: `check-ordinale.py`

Die Migration wäre ohne Absicherung eine Momentaufnahme geblieben – `check-anchors.py` sieht
eine Nummer im Anzeigetext nicht. Der neue Hook prüft nur **neu hinzugekommene** Zeilen und
blockt: nummerierte Überschrift, Nummer im Verweistext, ordinaler Absatz-Lead,
Nummernbereich, Paragraphen-Verweis, Verweis auf eine Zeilennummer. Ausnahmen mit Beleg:
fremdbestimmte Norm (RFC/ISO/DIN/Gesetz), Zitat in Anführungszeichen oder Backticks, Nummer
aus dem Dateinamen (`szenario_3_einkauf.md`), Session-ID in einer Überschrift.

**Mengenangaben** („alle vier Agenten") laufen bewusst **nicht** scharf, sondern ins Log
(`.claude/tmp/mengenangaben.log`). Am Bestand wären 65–75 % Fehlalarm – aber das misst den
falschen Gegenstand, denn der Hook sieht neue Zeilen, deren Quote unbekannt ist. Statt zu
schätzen wird gesammelt; die Entscheidung fällt nach einigen Sessions anhand der Messung.

## Die Vollständigkeitsfrage – vier Runden

Jede Runde hielt die vorige für abgeschlossen, und jede folgende widerlegte das:

1. **Eigene Suchnetze** – drei Stück, jedes mit einer Wortliste. Alle drei unvollständig,
   jeweils aus demselben Grund: Sie kodierten, woran gerade gedacht wurde.
2. **Vier Sichter-Subagenten** über Werkzeuge, Docs, Code und Prozessdateien. Ergebnis:
   16 Befunde, darunter tote Verweise im Produktionscode und drei widerlegte Behalte-Urteile.
3. **Prosa-Nachlauf** auf Verweisformen ohne Anker-Nachbarschaft – fand die zwei toten
   Verweise, die diese Session selbst erzeugt hatte.
4. **Vollinventur** auf User-Auftrag: alle 22.723 Ziffern- und Zahlwort-Vorkommen aufgenommen,
   klassenweise mit Stichprobenbeleg abgezogen, die verbleibenden 1.144 Zeilen gesichtet.
   Acht weitere Fundstellen – darunter `ordinale.py` selbst, das seine Muster nummerierte und
   per Nummer darauf verwies, mit `2b`/`2c`-Einschüben als Beleg für bereits eingetretenes
   Rutschen. Das Werkzeug trug den Defekt, gegen den es gebaut war.

## Zweistufiger Ausschluss

Aus der Inventur folgte ein Umbau der Prüf-Blacklist (User-Entscheid). **Erste Stufe** – die
Datei wird nicht gelesen, weil nichts zu prüfen ist: eingefrorene Historie, generierte
Dateien (`package-lock.json`, `Infrastructure/Migrations/`), Laufzeit-Artefakte
(`RESUME.md`, `session-types.json`, `scheduled_tasks.lock`). **Zweite Stufe** – die Datei
wird gelesen, aber einzelne Musterklassen zählen dort nicht (`anchors.MUSTER_AUSNAHMEN`): In
den Tests der Prüfwerkzeuge sind Anker- und Gliederungsmuster die Eingabe.

Der Unterschied ist nicht kosmetisch. Vorher fiel jede `test_*.py` pauschal heraus – 48
Dateien – und genau dort lag ein toter Paragraphen-Verweis. Jetzt sind vier Dateien
musterweise ausgenommen statt 48 pauschal; der gemessene blinde Fleck bei Testdateien ist 0.

## Was sonst entstand

- `.editorconfig`, `eslint.config.js`, `IngredientsEndpoints.cs`, `IngredientsPage.test.tsx`,
  `useCreateIngredientWithReactivation.ts`, `test_primitives.py`: tote Verweise auf entfernte
  Nummerierungen durch Anker-Verweise ersetzt.
- `ADR-S106-3`: Der Guard-Satz verlangt die Zuordnung zu einer **benannten** Kategorie statt
  zu „Kategorie 1 oder 2"; die sieben Kommentare in `IngredientsEndpointsTests.cs` folgen.
- `check-bash-permission.py`: `--help` verlangt keine Freigabe mehr (User-Meldung) – geprüft
  auf der maskierten Kommandozeile, damit `--help` im Eintragstext weiterhin fragt.
- `anchors.py`: `.pytest_cache/` und `Server/wwwroot/` wurden bei jedem Edit mitgelesen.
- Bestandsprüfer `ordinale.py` als Session-Agenda-Modul, das seinen eigenen Ausfall meldet
  (CM-S116-1).

68 neue Tests (870 → 938). Gegenproben für jedes blockierende Muster und für beide
Ausschluss-Stufen geführt.

## Learnings & Beobachtungen

- LL-S124-1 (HOCH) – Nummer entfernt, ohne nach Verweisen darauf zu suchen; zweimal
  aufgetreten. → `docs/kaizen/lessons_learned.md`
- LL-S124-2 (HOCH) – Prüfung behauptet, die ihren Gegenstand nicht prüfen konnte.
- LL-S124-3 (MITTEL) – Fehlalarmquote auf dem bereits bereinigten Bestand gerechnet.
- LL-S124-4 (MITTEL) – Befund aus einer Subagenten-Liste verloren, weil der nächste Bericht
  dazwischenkam.
- OBS-S124-2 – Befundlisten leben nur im Kontext. → `docs/kaizen/observations.md`
- Zwei neue Prinzipien in `docs/kaizen/principles.md`: „Ein Filter findet nur, woran beim
  Bauen gedacht wurde" und „Vor dem Ausgeben eines Prüfergebnisses fragen, ob die Prüfung
  hätte anschlagen können".

OBS-S112-7 umgesetzt und archiviert; OBS-S114-2 war daran gekoppelt und ist entblockt.
