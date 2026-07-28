# Session 109 – 2026-07-28/29

**Phase:** SKELETON
**Schwerpunkt:** OBS-Drain (Backlog war mit 21 drainbaren Einträgen überfüllt) – kein Feature-Lauf.

---

## Abgearbeitete Beobachtungen

Neun OBS aufgelöst, zwei neu bzw. reaktiviert. Backlog 21 → 16 drainbar.

### Block A – Stryker-Fehlsignale (5 Einträge, alle UMGESETZT)

`OBS-S108-3`, `OBS-S102-1`, `OBS-S103-1`, `OBS-S106-3`, `OBS-S100-3` – gemeinsamer Kern: Ein
Mutations-Lauf konnte „100 %" melden, ohne etwas gemessen zu haben. Die Score-Formel stand wörtlich
doppelt in `stryker-summary.py` und `qa-check.py` und lieferte bei null Mutanten eine 100 %.

Gebaut:

- **`_stryker_report.py`** – einzige Quelle für Score, Umfang und Gate. `total_valid == 0` → Score
  `None`, Gate schlägt fehl; `qa-check` bricht **vor** dem Übergabe-Hash ab.
- **`_stryker_target.py`** – `--mutate`-Muster werden vor dem Lauf gegen die Projektbasis geprüft;
  Treffer-los → Exit 2 mit Korrekturvorschlag, Brace-Globs mit Begründung abgelehnt.
- **`_run_lock.py`** – eigener Exit-Code 99 für „Lauf gar nicht gestartet"; `qa-check` weicht damit
  nicht mehr auf den Report eines fremden, parallel laufenden Prozesses aus.
- **`test-stryker-guards.py`** – 24 Fälle über beide Module.

Beim Verifizieren fiel ein **vierter Fehlsignal-Weg** auf, den keiner der Einträge kannte: Scheitern
alle Mutanten am TypeScript-Checker, meldet StrykerJS `Final mutation score of NaN is greater than or
equal to break threshold 100` und endet mit Exit 0. Nachgetragen im Archiv-Eintrag von `OBS-S108-3`.

Empirisch geklärt (vorher angenommen): Stryker.**NET** akzeptiert mehrere `--mutate`-Flags, aber keine
Kommaliste; Stryker**JS** genau umgekehrt (`createSplitter(',')`). Die Wrapper nehmen einheitlich eine
Kommaliste und übersetzen sie je Schicht.

### Block B – Wrapper-Ergonomie

`OBS-S108-4` (UMGESETZT): Live-Log wird nicht mehr gelöscht (Fortschritt beobachtbar); `--prefix <dir>`
in der Bash-Allow-Liste zugelassen; Puffer-Flush vor Subprozessen. Beim `--prefix`-Fix fiel auf, dass
der naive Weg ein Loch gerissen hätte – die Wrapper-Pflicht-Muster verlangen `npm` und `run`
nebeneinander, `npm --prefix Client run test` wäre daran vorbeigelaufen. Allow- und
Wrong-Approach-Muster teilen sich jetzt ein Fragment (`_NPM_RUN`), abgesichert in
`test-bash-permission.py`.

`OBS-S091-2` (IN BEOBACHTUNG bis S115): Der Hook-Rewrite für cwd-feste Wrapper-Aufrufe wurde bewusst
nicht gebaut – stattdessen wurde mit `--prefix` die Ursache entfernt.

### Block C – Wiedervorlagen-Lane (geleert)

- `OBS-S085-3` (bis S115): Gemessen – **430 von 517 Wrapper-Läufen (83 %) mit nachgelagertem Filter**,
  Tendenz steigend. Der Reihenfolge-Test (User-Vorschlag) widerlegte die Erklärung „Output zu lang":
  in 13 von 19 Kontexten war schon der erste Aufruf gefiltert, in 11 durchgehend. Unabhängig davon
  wurde die Ausgabe-Politik vereinheitlicht (`_wrapper_output.py`): Erfolgsfall nur noch Verdikt,
  Fehlerfall nur Analyse-Relevantes, Rest hinter `--verbose`.
- `OBS-S085-4` (bis S115): LSP-Pilot gemessen – 2 von 41 Sessions, 8 Calls, davon 1 nach dem
  Aktivierungstest. Statt zu verwerfen (User-Entscheid) wurde die Empfehlung geschärft: eigener Block
  in `frontend-layer-implementer` und `code-quality-auditor` statt nur in der TS-Guideline.
- `OBS-S085-2` (VERWORFEN), `OBS-S085-12` (UMGESETZT), `OBS-S092-2` (VERWORFEN).

### Phase-1-Token-Messung (aus `OBS-S085-2`)

23 Sessions inkl. 112 Subagent-Logs, ~23,5M Zeichen. Ergebnis: Tool-I/O 82,5 % (Subagenten 54,1 %),
`Read` allein **49,5 % des Gesamtvolumens**; die vermutete Orchestrator↔Subagent-Kommunikation 8,6 %.
Prämisse des Eintrags damit widerlegt → verworfen, Befund als `OBS-S109-1` erfasst. `OBS-S096-3`
(Scripted-Access-Layer) reaktiviert, da sein Re-Trigger eingetreten ist.

---

## Entscheidungen

- Kein Deny-Hook gegen das Filtern von Wrapper-Ausgaben (Variante B aus `OBS-S085-3`) – bei 83 % Quote
  träfe er zu breit; erst wirkt das kürzere Verdikt, Neubewertung S115.
- `OBS-S085-12` als UMGESETZT geschlossen **ohne** den geplanten Staffel-Schritt B→A: Die Staffel war
  Absicherung, kein Fahrplan, der zu Ende gegangen werden muss.

## Learnings & Beobachtungen

- `LL-S109-1` – Messergebnis vorgelegt, bevor die Datenquelle vollständig war (3× durch Rückfrage gekippt).
- `LL-S109-2` – Empfehlung auf Ressourcen- statt Sach-Argument gestützt.
- `LL-S109-3` – Negativ-Befund aus einem Testfall gezogen, der ihn nicht zeigen konnte.
- `OBS-S109-1` – Datei-Lesen als größter Token-Posten, wächst mit der Codebasis.

Details jeweils in `docs/kaizen/lessons_learned.md` bzw. `docs/kaizen/observations.md`.
