---
name: draining-observations
description: >
  Behandelt einen Satz offener Beobachtungen (OBS) aus docs/kaizen/observations.md –
  Discovery, Kandidaten-Findung und Entscheidung (umsetzen / verwerfen / aufschieben).
  Wird ausgelöst wenn der SessionStart-Hook einen OBS-Drain-Satz vorschlägt (Trigger-Text:
  "OBS-Drain – Backlog:") oder wenn der User OBS abarbeiten/drainen/durchgehen will
  ("OBS drainen", "Beobachtungen abarbeiten", "Backlog abbauen", "lass uns ein paar OBS angehen").
  NICHT für das Erfassen neuer OBS (das ist billig und passiert in closing-session) und NICHT
  für die Kaizen-Retro (die berührt OBS nur als verlinkten LL-Input).
user-invocable: true
---

# OBS-Drain – Beobachtungen behandeln

Dieser Skill arbeitet einen **Drain-Satz** offener OBS ab – OBS-Verarbeitung ist *generatives Design*, das
mit einem strukturierten Pfad bias-arm und entscheidungsfreudig bleibt. Der Mechanismus dahinter
(Wert-/Alters-Lane, Rate, Same-Artefakt-Kolokation, Bias-Modell) lebt kanonisch in `docs/kaizen/process.md`,
Abschnitt „Backlog-Abbau: kontinuierlicher Drain" – schlag dort nach, sobald eine Lane, die Rate oder ein
Marker unklar ist.

## 1. Drain-Satz holen

Der SessionStart-Hook blendet den Satz bereits ein (als „Nächste Aufgabe" der Session-Agenda, beginnend
mit „OBS-Drain – Backlog:"). Ist er noch im
Kontext und aktuell, nutze ihn direkt. Berechne ihn neu, sobald er fehlt oder veraltet ist (mitten/spät in
der Session, oder nachdem schon Items aufgelöst wurden):

```
python3 .claude/scripts/obs-drain.py
```

Meldet das Script „Backlog leer", bestätige das kurz und beende – nichts zu tun. (Die Backlog-Zahl B zählt nur
**drainbare** OBS – Status `NEU` – und ist daher kleiner als die Liste in `observations.md`.)

Der Satz liefert **Wert-Lane** + **Alters-Lane**, dazu ggf. **fällige Wiedervorlagen** (geparkte Items, deren
Termin erreicht ist), **offene Fragen** und einen **Hygiene-Reminder** (aufgelöst, aber noch nicht archiviert).
Definitionen: `process.md`. Ein **`+Koloc:`-Marker** an
einer Zeile nennt offene OBS an derselben Datei (Kandidaten für Same-Artefakt-Mitnahme, s. Schritt
„**Kolokation & Konsolidierung erwägen**"). Eine `Einheit [Σ …]` fasst *verwandte* Einträge zusammen, die
gemeinsam bearbeitet werden – dazu der Schritt „**Cluster kritisch prüfen**".

**Offene Fragen sind kein Drain-Item.** Erscheint die Sektion „Offene Fragen", leg die Einträge dem **User
zur Klärung** vor (Volltext: `docs/open-questions.md`) – sie werden nicht wie OBS selbst entschieden, denn
sie haben Business-/Architektur-Impact. Ergebnis: Frage geklärt → Eintrag entfernen und das Ergebnis am
stabilen Ort festhalten (ADR, Guideline, `tech-debt.md`); noch nicht klärbar → `Fällig: S<NNN>` setzen, damit
sie zum passenden Zeitpunkt statt nach Alter wiederkommt.

## 2. Pro Item: Discovery → Entscheidung

Jedes Item bekommt in dieser Behandlung eine Entscheidung – **umsetzen, verwerfen oder aufschieben**. Auch
aufschieben ist eine vollwertige Wahl (mit Grund und Re-Trigger), keine Vertagung der Entscheidung selbst.
Leg die Items in **sinnvoll gruppierten, kleinen Blöcken** vor (z.B. 2–3 thematisch/nach Datei
zusammengehörige, dann die nächsten) und nur **wenige auf einmal** – schon wenige Items gleichzeitig
sind für den User kognitiv anstrengend (Kontext-Switch), erst recht wenn über sie in mehreren Runden
diskutiert wird. Für jedes Item:

0. **Tracker-Check – Prozess oder Produkt?** In einem Satz vorab. Betrifft der Eintrag das **Produkt**
   (Code samt Build-/Test-Kette), endet die Behandlung hier: Er **zieht um** – nach `tech-debt.md`,
   `adr.md`, `open-questions.md` oder in die passende Guideline, wenn er reines Wissen ist („diese Falle
   gibt es"). Keine Kandidatenbildung; Status `VERWORFEN (umgezogen nach …)`, der Inhalt lebt am neuen
   Ort weiter. Grund für den Vorrang: Nur dieser Pool ist ratenbegrenzt – ein Produkt-Thema hier kostet
   Kapazität, die es an seinem Ort nie gebraucht hätte. Taxonomie: `CLAUDE.md`, Sektion „Ablage: in
   welchen Tracker gehört dieser Eintrag?".

1. **Verstehen zuerst.** Sorge dafür, dass Ziel/Problem der Beobachtung wirklich klar ist. Bei Unklarheit
   nutze `grill-me`, bevor Kandidaten entstehen – eine falsch verstandene OBS produziert plausible, aber
   falsche Lösungen.

2. **Kandidaten frisch generieren.** OBS werden ohne vorab notierte Kandidaten erfasst (sonst nudgt die
   Erfassung die Lösung vor und schwächt die Discovery). Erarbeite die Kandidaten jetzt gemeinsam und
   schlage sie dem User vor – Orchestrator schlägt vor, User entscheidet.

   **Trägt der Eintrag eine `Vorprägung` (Marker `+Vorprägung` im Drain-Satz, Hinweis im `get`), dann in
   dieser Reihenfolge:** erst eigene Kandidaten bilden und **dem User vorlegen**, danach
   `python3 .claude/scripts/obs.py get OBS-SNNN-N --vorprägung` abrufen und die dortigen Angaben als
   *weiteren* Kandidaten behandeln. Das Feld enthält, was schon genannt oder vermutet wurde – genannte
   Lösungen, Ursachenvermutungen, Analogieschlüsse. Zwei Gründe für die Reihenfolge: Vorher gelesen, prägt es
   die Discovery (deshalb ist es beim Standardzugriff verborgen); und der Text ist **agentenformuliert** – er
   kann den ursprünglichen Wunsch verschoben haben. **Also nicht als Auftrag lesen, sondern das Ziel beim User
   verifizieren** (in S115 belegt: eine so konservierte „Zielvorstellung" hatte das eigentliche Ziel verfehlt
   und den Drain in die falsche Richtung gelenkt, bis der User korrigierte).

   **Behauptete Fakten am Code prüfen, nicht aus dem Eintrag übernehmen.** Die technischen Aussagen im
   Eintrag sind eine Momentaufnahme der Erfassung und altern wie jede andere Quelle – ein Item aus der
   Alters-Lane ist oft ein Dutzend Sessions alt. Pflicht, sobald eine Aussage die **Kostenschätzung oder
   Machbarkeit** trägt („X ist uneinheitlich", „Y hängt an Z", „das ginge nur mit …"): am aktuellen Stand
   verifizieren, bevor sie eine Empfehlung stützt. Eine auf veralteten Angaben gefällte Verwerfung
   schließt den Punkt *und* hinterlässt die falsche Begründung als Präzedenz im Archiv.

3. **Cluster kritisch prüfen, bevor er gemeinsam bearbeitet wird.** Eine `Einheit [Σ …]` im Drain-Satz
   ist eine **Behauptung der Erfassung**, keine geprüfte Tatsache – gemacht, als der spätere Partner noch
   gar nicht existierte. Volltexte der Mitglieder lesen und je Mitglied fragen: *Wird es beim Bearbeiten
   der anderen wirklich mit erledigt – oder ist es nur dasselbe Themenfeld?* Wer danebensteht, wird
   **herausgelöst** und behält seinen Einzel-Score (bei Zweifel Rücksprache); dann die Kante entfernen
   (`obs.py set <ID> --zusammen-erledigen …`) – **auf beiden Seiten prüfen**, denn eine einzige
   verbliebene Kante hält die Einheit zusammen, egal in welcher Richtung sie steht. Welche Einträge auf
   den vorliegenden zeigen, blendet `obs.py get` als eingehende Kanten mit ein. Der typische Fehltreffer ist die **Vorfrage**, die vor den anderen zu entscheiden wäre –
   eine Reihenfolge-Abhängigkeit macht nichts billiger.

4. **Kolokation & Konsolidierung erwägen** (zwei getrennte Fälle):
   - **Same-Artefakt-Kolokation** (gemeinsam *lösen*): Berührt ein Kandidat dieselbe Datei wie ein anderes
     offenes OBS, erwäge die Mitnahme (auch bei verschiedenen Problemen; Begründung: `process.md`). Nur bei
     **gleicher Datei**, nicht bei bloßer Themen-Nähe. Marker: `+Koloc:`.
   - **Thematisch/parametrische Konsolidierung** (zu *einem* Eintrag zusammenführen): Beschreibt ein Item
     **dasselbe oder eng verwandte Problem** wie ein anderes offenes OBS – auch an anderer Stelle, analog
     parametrisierten Tests – dann den tragenden Eintrag erweitern und den anderen als `VERWORFEN
     (konsolidiert in OBS-…)` schließen, oder via `Bezug:` gemeinsam lösbar halten. Senkt Backlog-Redundanz
     und Drain-Last. (Die teure „ist das dasselbe Problem?"-Beurteilung gehört hierher in den Drain, nicht in
     die billige Erfassung – `process.md` „Erfassung ist billig, Klassifikation ist teuer".)

5. **Gefahr & CM-Gate** (s. `process.md` „Gefahr & Kandidaten-Bewertung" + „Wann gehört etwas wohin?"): Bei
   höher-Gefahr/nicht-trivialen Items erst absichern/belegen, dann umsetzen – Sorgfalt und Beweisbarkeit
   skalieren mit der Gefahr. Steht eine *stehende, wiederkehrende* Leitplanke dahinter, lege eine CM an; bei
   einer Einmal-Änderung halte sie inline als `Maßnahme:` fest.

6. **Entscheiden.** Wägst du *verwerfen* ab, prüfe zuerst den **Kalt-Abwertungs-Bias**: Du liest die OBS
   lange nach der Beobachtung und bist strukturell versucht, sie als „nicht mehr dringend" einzustufen.
   Gegenprobe: **„Wäre dieser Punkt noch wertvoll, wenn er gerade jetzt erst beobachtet worden wäre?"** –
   wenn ja, halte ihn (nicht wegen Zeitablauf verwerfen). Ist sein **Gegenstand objektiv entfallen** (z.B.
   der betroffene Code existiert nicht mehr), darf er normal als `VERWORFEN (Grund)` raus – das schützt der
   Prüfsatz nicht.

## 3. Ausgang festhalten

Trag den Ausgang **per Script** ein, statt die Datei zu editieren – das trifft genau die Felder, die
`obs-drain.py` parst, und erspart den Vor-Edit-Read der gesamten Datei:

```
python3 .claude/scripts/obs.py get OBS-SNNN-N          # Eintrag lesen, ohne die Datei zu öffnen
python3 .claude/scripts/obs.py set OBS-SNNN-N --status "UMGESETZT (S<NNN>)" --entscheidung "…"
```

- **umsetzen** → Änderung durchführen (je nach Art via TDD/Guidelines/review-code), Status auf
  `UMGESETZT (S<NNN>)`, gewählte Lösung + CM-Bezug ins Feld `Entscheidung/Maßnahme:`.
- **verwerfen** → Status auf `VERWORFEN (Grund)`; der Grund ist Pflicht (auditierbar, rückholbar).
- **aufschieben** → Status auf `IN BEOBACHTUNG bis S<NNN>`; das **`bis S<NNN>` ist Pflicht**
  (Wiedervorlage-Termin; sinnvoll wählen, nicht beliebig weit – Mechanik: `process.md`). Grund ins Feld
  `Entscheidung/Maßnahme:`. Wird ein Item als **fällige Wiedervorlage erneut** aufgeschoben, ist das ein
  Signal – prüf explizit, ob es nicht besser **verworfen** gehört (der Kalt-Abwertungs-Bias gilt hier
  doppelt). Für event-basierte
  Reaktivierung zusätzlich eine **Re-Trigger-Notiz** („wieder aktiv wenn …"); kein Script wertet sie aus, der
  Termin ist der verlässliche Backstop. Ein **blockiertes** Item (wartet auf X) ist genau dieser Fall: Grund =
  der Blocker, Termin = Spätestens-Wiedervorlage, Re-Trigger = dessen Auflösung.

**Aufgelöste Einträge** (UMGESETZT / VERWORFEN) → mechanisch ins Archiv verschieben:
`python3 .claude/scripts/obs-archive.py` (schneidet sie aus `observations.md` und hängt sie ans
`archive/observations_archive.md` – kein Hand-Cut/Paste). Vorab prüfbar mit `--dry-run`.

## 4. Abschluss

Fass kurz zusammen, was umgesetzt/verworfen/aufgeschoben wurde und wie groß das Backlog jetzt ist
(`obs-drain.py` zeigt den Stand). Stehen aus den Umsetzungen neue Prioritäten oder TD an, berücksichtige
sie beim Session-Abschluss (`closing-session`).
