---
name: draining-observations
description: >
  Behandelt einen Satz offener Beobachtungen (OBS) aus docs/kaizen/observations.md –
  Discovery, Kandidaten-Findung und Entscheidung (umsetzen / verwerfen / aufschieben).
  Wird ausgelöst wenn der SessionStart-Hook einen OBS-Drain-Satz vorschlägt (Trigger-Text:
  "OBS-Drain vorgeschlagen") oder wenn der User OBS abarbeiten/drainen/durchgehen will
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

Der SessionStart-Hook blendet den Satz bereits ein (Block „OBS-Drain vorgeschlagen"). Ist er noch im
Kontext und aktuell, nutze ihn direkt. Berechne ihn neu, sobald er fehlt oder veraltet ist (mitten/spät in
der Session, oder nachdem schon Items aufgelöst wurden):

```
python3 .claude/scripts/obs-drain.py
```

Meldet das Script „Backlog leer", bestätige das kurz und beende – nichts zu tun. (Die Backlog-Zahl B zählt nur
**drainbare** OBS – Status `NEU` – und ist daher kleiner als die Liste in `observations.md`.)

Der Satz liefert **Wert-Lane** + **Alters-Lane**, dazu ggf. **fällige Wiedervorlagen** (geparkte Items, deren
Termin erreicht ist) und einen **Hygiene-Reminder** (aufgelöst, aber noch nicht archiviert). Definitionen:
`process.md`. Ein **`+Koloc:`-Marker** an
einer Zeile nennt offene OBS an derselben Datei (Kandidaten für Same-Artefakt-Mitnahme, s. Schritt 3). Lege
eine kurze Task-Liste an (ein Task pro OBS; Regeln: `docs/process/task-system.md`).

## 2. Pro Item: Discovery → Entscheidung

Jedes Item bekommt in dieser Behandlung eine Entscheidung – **umsetzen, verwerfen oder aufschieben**. Auch
aufschieben ist eine vollwertige Wahl (mit Grund und Re-Trigger), keine Vertagung der Entscheidung selbst.
Leg die Items in **sinnvoll gruppierten, kleinen Blöcken** vor (z.B. 2–3 thematisch/nach Datei
zusammengehörige, dann die nächsten) und nur **wenige auf einmal** – schon wenige Items gleichzeitig
sind für den User kognitiv anstrengend (Kontext-Switch), erst recht wenn über sie in mehreren Runden
diskutiert wird. Für jedes Item:

1. **Verstehen zuerst.** Sorge dafür, dass Ziel/Problem der Beobachtung wirklich klar ist. Bei Unklarheit
   nutze `grill-me`, bevor Kandidaten entstehen – eine falsch verstandene OBS produziert plausible, aber
   falsche Lösungen.

2. **Kandidaten frisch generieren.** OBS werden ohne vorab notierte Kandidaten erfasst (sonst nudgt die
   Erfassung die Lösung vor und schwächt die Discovery). Erarbeite die Kandidaten jetzt gemeinsam und
   schlage sie dem User vor – Orchestrator schlägt vor, User entscheidet.

3. **Same-Artefakt-Kolokation erwägen.** Berührt ein Kandidat dieselbe Datei wie ein anderes offenes OBS,
   erwäge die Mitnahme (Begründung: `process.md`). Nur bei **gleicher Datei**, nicht bei bloßer Themen-Nähe.

4. **Gefahr & CM-Gate** (s. `process.md` „Gefahr & Kandidaten-Bewertung" + „Wann gehört etwas wohin?"): Bei
   höher-Gefahr/nicht-trivialen Items erst absichern/belegen, dann umsetzen – Sorgfalt und Beweisbarkeit
   skalieren mit der Gefahr. Steht eine *stehende, wiederkehrende* Leitplanke dahinter, lege eine CM an; bei
   einer Einmal-Änderung halte sie inline als `Maßnahme:` fest.

5. **Entscheiden.** Wägst du *verwerfen* ab, prüfe zuerst den **Kalt-Abwertungs-Bias**: Du liest die OBS
   lange nach der Beobachtung und bist strukturell versucht, sie als „nicht mehr dringend" einzustufen.
   Gegenprobe: **„Wäre dieser Punkt noch wertvoll, wenn er gerade jetzt erst beobachtet worden wäre?"** –
   wenn ja, halte ihn (nicht wegen Zeitablauf verwerfen). Ist sein **Gegenstand objektiv entfallen** (z.B.
   der betroffene Code existiert nicht mehr), darf er normal als `VERWORFEN (Grund)` raus – das schützt der
   Prüfsatz nicht.

## 3. Ausgang festhalten

Trag den Ausgang in die feste Eintragsstruktur in `docs/kaizen/observations.md` ein – die Felder
`- Status:`, `- Entscheidung/Maßnahme:`, `- Bezug:` (Layout im Header-Kommentar der Datei). `obs-drain.py`
parst genau diese Präfixe, also halte sie ein.

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
