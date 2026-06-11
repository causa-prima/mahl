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

## Session 081 – 2026-06-11

- **[MITTEL] [PROZESS] [Doku] Guideline-Änderung auf unverifiziertem Tool-Verhalten empfohlen**
  Was: Pauschalen `fireEvent.click`→`user.click`-Switch samt Guideline-Umschrift empfohlen, gestützt auf ein plausibles Mentalmodell von user.click; erst auf Nutzer-Nachfrage zeigten Messung (9/13 Timeout-Kills, ~2× Laufzeit) + Wegwerf-Test, dass der Mehrwert eng ist (nur `pointer-events:none`-Vorfahr) → Revert.
  Warum: Das in `principles.md` verankerte „Tool-Verhalten erst nach Verifikation behaupten / Unverifiziertes proaktiv kennzeichnen" wurde nicht angewendet.
  Regel: Vor einer Guideline-Änderung über Tool-/API-Verhalten dieses empirisch verifizieren (Mess-/Wegwerf-Test); unverifizierte Empfehlungen proaktiv als solche kennzeichnen statt auf Nachfrage zu warten.

- **[MITTEL] [AGENT] [Mutation-Testing] Roh-Report manuell geparst statt vorhandene `--detail`-Flag genutzt**
  Was: Subagent versuchte Stryker-Survivor aus `mutation.json` manuell zu parsen (vom Bash-Hook blockiert), obwohl `stryker-frontend.py --detail` Survivors (Datei/Zeile/Mutator/Replacement) bereits ausgibt.
  Warum: Wissenslücke über die `--detail`-Option des vorhandenen Wrapper-Scripts.
  Regel: Vor manuellem Parsen eines Roh-Reports prüfen, ob das Projekt-Wrapper-Script die benötigte Sicht bereits per Flag anbietet.

- **[MITTEL] [PROZESS] [Doku] Offene Punkte ins falsche Ziel-Dokument einsortiert (Wiederholung S080)**
  Was: Playwright-Reinstall (Prozess/Setup-Wissen) zunächst in die tech-debt-Tabelle geschrieben und unabhängige Tooling-Punkte gebündelt; der User korrigierte (gehört in `dev-workflow.md`; der Stryker-Punkt war eine Wissenslücke → lessons_learned).
  Warum: Beim Vermerken nicht am Ist-Zustand klassifiziert – dieselbe Klasse wie S080 („künftige Adoption als Schuld").
  Regel: Offene Punkte am Ist-Zustand einsortieren – tech-debt nur für real suboptimalen Code; Setup-/Prozesswissen → `dev-workflow`/Doku; Wissenslücke/Verhalten → lessons_learned; unabhängige Punkte trennen.

## Session 080 – 2026-06-11

- **[MITTEL] [AGENT] [TS-Code] Laufzeit-grün als Korrektheitsbeweis für typ-betreffende Änderung genommen**
  Was: Nach Umstellung der Tests auf jest-dom-Matcher lief Vitest grün, obwohl TypeScript die Matcher-Typen gar nicht auflöste (Augmentation nicht im TS-Programm, weil `src/test` excluded ist) – erst der ESLint-`no-unsafe-call`-Lauf deckte es auf.
  Warum: Vitest strippt Typen zur Laufzeit; ein grüner Testlauf sagt nichts über die Typ-Auflösung aus.
  Regel: Typ-betreffende Änderungen (neue Augmentations, Matcher, Branded Types) immer mit dem typ-bewussten Check (ESLint/`tsc`) verifizieren – nicht nur mit dem Test-Runner.

- **[GERING] [AGENT] [Doku] Vorausschauende Tool-Adoption als „technische Schuld" etikettiert**
  Was: Beim Schließen der jest-dom/user-event-Schuld user-event als „installiert aber noch ungenutzt → Schuld" in AGENT_MEMORY geführt, obwohl es keinen suboptimalen Code gibt; der User korrigierte.
  Warum: „könnten wir später nutzen" mit „aktueller Missstand im Code" verwechselt.
  Regel: Technische Schuld nur für tatsächlich suboptimalen Ist-Zustand führen; künftige Adoption gehört in Prioritäten/Szenario-Notizen, nicht in die Schuld-Tabelle.

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
