# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Bash/Permission | Mutation-Testing |
            Hook/Script | Review | Agent-Prompt | Skill-Nutzung | Gherkin |
            Doku | Kommunikation | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/process.md

Vor dem Eintrag prüfen (alle drei Ja): (1) Gab es ein falsches Agenten-Verhalten das wieder auftreten kann – auch mit Config-Fix? (2) Kann die Situation grundsätzlich wiederkehren bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter? (3) Ist die Regel ein Agenten-Verhalten/-Urteil – keine statische, nachschlagbare Tatsache? Nein → kein Eintrag (Infra-/Tool-Fakt → docs/process/dev-workflow.md / Code-Kommentar; einmalige Situation → gar nicht). Bei (2) auf Klassen-Ebene formulieren. Details: docs/kaizen/process.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/process.md`
> **Archiv:** `docs/kaizen/archive/`

---

## Session 079 – 2026-06-10

- **[MITTEL] [PROZESS] [Hook/Script] Agenten-Guidance/UX nicht am frischen Subagenten verifiziert**
  Was: Hook-Allow-Liste + Framing überarbeitet und für ausreichend gehalten; erst der Subagent-Eval (frischer Agent löst Task-Liste nur anhand `--list`) deckte auf, dass die Wrapper-Scripts unsichtbar waren → `dotnet test`/`npm test` wären weiter in unnötige Denies gelaufen.
  Warum: „Verständlich für mich, der ich den Hook kenne" ≠ „verständlich für einen kalt startenden Agenten" – das eigene Vorwissen maskiert die Lücke.
  Regel: Änderungen an agenten-gerichteter Guidance/Hint-/List-UX an einem frischen Subagenten mit konkreter Aufgabenliste empirisch testen, bevor sie als fertig gelten – nicht am eigenen Verständnis.

- **[MITTEL] [PROZESS] [Hook/Script] Korrekter Weg nur reaktiv (per Deny-Hint) statt proaktiv auffindbar**
  Was: Die Wrapper-Scripts (Tests/Lint/Mutation) standen nur in den WRONG_APPROACH-Hints – der Agent erfuhr den richtigen Befehl erst *nach* einem Deny; proaktiv griff er zum naheliegenden Direktbefehl.
  Warum: Reaktive Hints heilen, verhindern aber den unnötigen Deny nicht; der korrekte Pfad fehlte in der immer geladenen Liste.
  Regel: Für wiederkehrende Tätigkeits-Klassen den korrekten Befehl proaktiv in der ständig sichtbaren Quelle (`--list`, SessionStart) anbieten – nicht darauf bauen, dass der Agent ihn über ein Deny lernt.

## Session 078 – 2026-06-10

- **[MITTEL] [PROZESS] [Hook/Script] Matching-Heuristik nur theoretisch begründet, nicht am Datensatz geprüft**
  Was: Severity-agnostisches CM-Matching (Option A) für `retro_report.py` vorgeschlagen und umgesetzt; erst der Lauf am echten Korpus zeigte massive Über-Maskierung (Wildcard-CM verschluckte distinkte Muster) → revertiert.
  Warum: Die Heuristik klang theoretisch plausibel; der Delta-Effekt auf reale Findings wurde nicht vor der Empfehlung geprüft.
  Regel: Änderungen an Matching-/Scoring-Heuristiken vor der Empfehlung am echten Datensatz laufen lassen und den Vorher/Nachher-Delta inspizieren – nicht aus der Theorie schließen.

- **[MITTEL] [AGENT] [Kommunikation] Tool-/Permission-Verhalten ohne Verifikation behauptet**
  Was: „wc ist nicht auf der Allow-Liste" behauptet, obwohl es das ist – `check-bash-permission.py --list` (im Deny-Hint genannt) hätte es sofort gezeigt.
  Warum: Aus der Fehlermeldung geschlossen statt die dokumentierte Quelle (`--list`) zu prüfen – Rückfall auf das „Unterstützt ≠ beweist"-Prinzip.
  Regel: Behauptungen über Allow-Liste/Tool-Verhalten erst nach `--list`-/Quellprüfung – die Verifikationsquelle steht meist im Deny-Hint selbst.

- **[MITTEL] [PROZESS] [Doku] Tag-Migration nur auf eine Form skopiert**
  Was: Beim Retaggen von `Tooling` wurden nur `[Tooling]`-Einträge erfasst; der `[Session-Struktur]`-Eintrag (eigene Form) wurde vergessen und blieb verwaist.
  Warum: Migrations-Scope an der häufigsten Form festgemacht, nicht an allen von der Revision betroffenen Tags.
  Regel: Vor einer Tag-/Referenz-Migration alle betroffenen Formen auflisten und per Gegen-Grep verifizieren, dass keine zurückbleibt (vgl. S076).
