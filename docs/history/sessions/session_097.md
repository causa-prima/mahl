# Session 097 – 2026-07-01

**Phase:** SKELETON
**Fokus:** Szenario-Clustering Teil (b) – `implementing-scenario` auf Lauf-Konsum umgebaut. Kein Produktionscode (US-904).

## Ausgangslage
Teil (a) (Clustering-Algorithmus + 31 Lauf-Tags in `features/ingredients.feature`) war aus einer
Vorsession uncommitted liegen geblieben (`docs/handoff-scenario-clustering.md`). Teil (b) – der
eigentliche Skill-/Tooling-Umbau auf Lauf-Konsum – war bewusst auf diese Session verschoben.

## Umgesetzt

### OBS-S097-1 dokumentiert (Alternativen-Rationale)
Auf Wunsch des Users die verworfenen Clustering-Alternativen (Dialog/Endpoint-Grenze, Gherkin-Tag,
reine Capability, Capability+Größendeckel, erster intuitiver 7er-Split) samt Verwerfungsgründen als
OBS-Eintrag konserviert – als „Verbesserungspotential + gewählte Lösung", nicht als LL/ADR.

### Tooling auf Lauf-Konsum umgebaut
- `_feature.py`: parst `# @run-N · Label · Schicht[ · Singleton]`-Kommentare pro Szenario (Lookahead-
  Puffer für Kommentar-/Leerzeilen – entscheidet erst beim nächsten inhaltstragenden Element, ob ein
  Kommentarblock Run-Tag-Kandidat oder normale Body-/Background-Zeile ist).
- `check-atdd-gate.py`: neuer Modus `<@story-tag> run-N` (liefert Background + alle Szenarien des
  Laufs); alter Tag+Titel-Modus bleibt erhalten.
- `next_scenario.py` → umbenannt zu `next_run.py`: löst den nächsten offenen **Lauf** auf (Gruppierung
  über Run-Nummer, **sortiert nach Run-Nummer** = Build-Reihenfolge, nicht nach Datei-Position);
  ungetaggte Szenarien bleiben rückwärtskompatible Einzel-Läufe. Neu: `--story US-NNN`-Filter für
  `--open`/`--done`. Neu: `--check` erkennt zusätzlich kaputte Run-Tag-Kommentare
  (`find_malformed_run_comments`) und inkonsistente Metadaten bei gleicher Run-Nummer
  (`check_run_consistency`). Platzhalter `{{NEXT_SCENARIO}}` → `{{NEXT_RUN}}`.
- Alle Referenzen aktualisiert: `check-e2e-scenario-ref.py`, `session-start.sh`, `AGENT_MEMORY.md`,
  `closing-session/SKILL.md`, `e2e-testing.md`, `tech-debt.md`, ADR-S041-7 (Addendum S097).

### `implementing-scenario`-Skill umgebaut
Aufruf `@US-NNN run-N` statt Einzel-Szenario. Architektur-Check, E2E-Tests, Batch-Test-Review,
Commit-Message laufen über alle Szenarien des Laufs; Frontend-only-Läufe brauchen keinen
Backend-Subagenten (Schicht steht im Run-Tag). Neu: Sibling-Läufe-Vorschau in Schritt 0
(`next_run.py --open --story <US-NNN>`, nur Titel, keine Details) – User identifizierte über einen
unabhängig beauftragten Opus-Subagenten das Gold-Plating-Risiko, wenn ein früher Lauf (z.B. run-1
„Anlegen·Success") dieselbe UI-Fläche berührt wie ein späterer (run-7 „Liste"): der Implementer soll
die Capabilities des späteren Laufs jetzt explizit in die YAGNI-„NICHT implementieren"-Liste aufnehmen
statt sie zu erraten.

### Bugfixes (im Zuge der kritischen Prüfung, User-getrieben)
- **Reihenfolge-Bug:** `group_runs()` sortierte zunächst nach Datei-Position des ersten Auftretens
  statt nach Run-Nummer → `run-7` wurde fälschlich vor `run-1` als „nächster Lauf" gemeldet (echtes
  `ingredients.feature` hat `run-7` als erstes Szenario in der Datei, `run-1` aber die niedrigere
  Nummer/Build-Priorität). User bemerkte die falsche Empfehlung beim Testen von `next_run.py`.
- **Kommentar-Kontext-Bug** (bei der ersten Fix-Iteration selbst eingebaut): eine naive
  `current is None`-Prüfung hätte Background-/Szenario-Body-Kommentare stillschweigend verschluckt
  bzw. fälschlich als Run-Tag fürs nächste Szenario gewertet – gelöst über den Lookahead-Puffer.
- **Zwei stille Fehlerquellen** in den Rohdaten proaktiv abgesichert (auf explizite Bitte des Users,
  weitere Fälle zu suchen): kaputte Run-Tag-Kommentare (Tippfehler) und inkonsistente Metadaten bei
  gleicher Run-Nummer wurden bisher lautlos ignoriert/reduziert – jetzt von `next_run.py --check`
  erkannt.

### AGENT_MEMORY präzisiert
„Nächstes Szenario" → „Nächster Lauf"; TD-S094-1/TD-S077-1-Priorität von vager „nächste
Baseline-Szenarien"-Formulierung auf konkrete Lauf-Nummern umgestellt (run-4/run-1/run-2); Roadmap-
Kontext-Zeile ebenfalls mit Lauf-Referenzen versehen. Handoff-Doc gelöscht (Teil a+b fertig).

## Probleme / Korrekturen
- Reihenfolge-Bug (s.o.) – User bemerkte falschen `next_run`-Output, bevor committet wurde → LL-S097-1.
- Erster Vorschlag für die Sibling-Läufe-Vorschau (reines `grep "# @run-"`) war zu informationsarm
  (nur Labels wie „Liste", keine Szenario-Titel) – User bat um empirischen Test vor der Umsetzung;
  `next_run.py --open` (Label + Titel) erwies sich als die bessere, bereits vorhandene Lösung.
- Ein unbegründeter `--done`-Zusatz im Sibling-Vorschau-Hinweis wurde vom User als nicht hergeleitet
  zurückgewiesen und entfernt (nur `--open` ist für den Zweck relevant).

## Ergebnisse
- 207 Tests grün (`.claude/hooks/tests/`), reale Feature-Datei `next_run.py --check` = ✅ konsistent.
- Opus-Subagent bestätigte unabhängig: run-1-vor-run-7 ist kein Architekturproblem, nur die
  YAGNI-Schärfung (Sibling-Vorschau) war eine sinnvolle Ergänzung.

## Offene Punkte
- Keine unmittelbar offenen Punkte zum Szenario-Clustering-Umbau; nächster Schritt ist die reguläre
  US-904-Weiterarbeit (`{{NEXT_RUN}}`).
