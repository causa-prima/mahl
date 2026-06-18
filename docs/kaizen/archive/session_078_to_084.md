# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] LL-S<NNN>-<n> – Kurztitel**
    Quelle: User   (optionale Zeile, nur bei user-gemeldeten Einträgen)
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

  ID (neue Einträge): LL-S<NNN>-<n>, HINTER den Tags – vor [ würde es die Script-Regexes brechen.
  Vorausschauende Beobachtungen → docs/kaizen/observations.md.

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

## Session 084 – 2026-06-15

- **[HOCH] [PROZESS] [Review] Überraschendes E2E-/Integrationsergebnis zuerst gegen "läuft aktueller Code?" prüfen**
  Was: Ein E2E-Test schlug deterministisch fehl; ich jagte ~1 h einer vermeintlichen Code-Regression nach, bis sich zeigte, dass die Suite gegen einen veralteten, separat verwalteten Backend-Prozess lief.
  Warum: Das System-under-Test (extern gestarteter Backend) war nicht garantiert der aktuelle Build; kein Mechanismus erzwang Frische.
  Regel: Liefert ein E2E-/Integrationstest ein überraschendes Ergebnis, **zuerst verifizieren, dass das getestete System aus dem aktuellen Quellcode läuft** (frischer Start / Build-Identität), bevor man eine Code-Regression vermutet. Externe, langlebige Test-Targets per Poka-Yoke frisch erzwingen statt auf Disziplin zu setzen.

- **[MITTEL] [TOOLING] [Doku] Dokumentierte Befehle empirisch verifizieren – auch in Guidelines/Allow-Listen**
  Was: Die Stryker-Disable-Syntax in der TS-Guideline (`next line` statt `next-line`) und die Bare-`dotnet ef database update`-Form in `--list`/dev-workflow funktionierten beide real nicht.
  Warum: Beispiele wurden notiert, aber nie ausgeführt; falsche Form sieht plausibel aus.
  Regel: Bevor man sich auf einen dokumentierten Befehl/Snippet verlässt (besonders Suppressions, CLI-Invocations), einmal real ausführen; Doku-Snippets sind keine verifizierte Wahrheit.

- **[GERING] [AGENT] [Bash/Permission] `--allow-once` nicht reflexartig anhängen**
  Was: Ich hängte `--allow-once` an Befehle, deren Wirkung bereits über die Allow-Liste abgedeckt war (z.B. taskkill /pid vs. /im).
  Warum: Bequemlichkeit statt erst die Allow-Liste/Alternativen zu prüfen.
  Regel: Vor `--allow-once` zuerst `--list` prüfen, ob eine erlaubte Variante denselben Zweck erfüllt; die Ausnahme nur für echte Einzelfälle ohne regulären Weg.

## Session 083 – 2026-06-12

- **[HOCH] [AGENT] [Agent-Prompt] „NULL neue Suppressions" als Absolutregel an Subagenten vorgegeben**
  Was: Ich gab dem Frontend-Subagenten als „härtesten Maßstab" vor, Ziel seien NULL neue Stryker-Suppressions; daraufhin entfernte er das guideline-vorgeschriebene `throwOnError: true` (statt es zu behalten und begründet zu suppressen), um einen unausgeübten Survivor zu vermeiden → guideline-widriger Code, jetzt Tech-Debt.
  Warum: Ich habe eine Heuristik (vermeide spekulative ungetestete Zweige) zu einer Absolutregel überdehnt; die Projektregel lautet „keine UNBEGRÜNDETEN Suppressions" – begründete (äquivalent / strukturell unerreichbar / Fehlerpfad bewusst aufs treibende Szenario verschoben) sind erlaubt und werden vom Orchestrator validiert. Beleg der Inkonsistenz: beim Backend habe ich begründete Suppressions (ADR-S000-4/S041-9) korrekt durchgewunken.
  Regel: Suppressions-Politik an Subagenten nie als „null" formulieren, sondern als „keine unbegründeten – jede Suppression braucht eine valide Äquivalenz-/Nichttestbarkeits-Begründung, die der Orchestrator prüft". Eine nötige begründete Suppression ist kein Scope-Verstoß.

- **[MITTEL] [AGENT] [Kommunikation] Eigene Extrapolation einer User-Entscheidung dem User zugeschrieben**
  Was: Ich begründete die „NULL Suppressions"-Vorgabe gegenüber dem Subagenten mit „Genau diese Falle will der User vermeiden" – obwohl der User nur „Mutation-State minimal" entschieden hatte, nicht „null Suppressions global".
  Warum: Aus einer konkreten User-Entscheidung eine breitere Regel abgeleitet und die Autorität des Users dahinter gestellt, statt die Ableitung als meine eigene zu kennzeichnen.
  Regel: Eigene Ableitungen/Extrapolationen explizit als solche kennzeichnen; nur das dem User zuschreiben, was er tatsächlich entschieden hat. Verleiht eine Extrapolation falsche Autorität, dämpft sie zudem die Kritikbereitschaft des Subagenten.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Scope-Philosophie-Entscheidung an Subagenten delegiert statt dem User vorgelegt**
  Was: Die Wahl „validierendes Value Object jetzt (mit Suppression) vs. strikt YAGNI später" (Gold-Plating-Grenzfall) habe ich beim Backend dem Subagenten überlassen und seine Option-A-Begründung akzeptiert – während ich die analoge ETag-Scope-Frage korrekt dem User vorlegte.
  Warum: Inkonsistente Schwelle, wann eine Scope-/Gold-Plating-Abwägung Orchestrator-intern entschieden wird und wann sie dem User gehört.
  Regel: Entscheidungen, die eine Guideline gegen YAGNI/Gold-Plating ausspielen (untestbare Zweige, vorgezogene Struktur, transiente Suppressions), dem User als A/B-Wahl vorlegen – nicht an den Subagenten delegieren.

- **[MITTEL] [QUALITÄT] [C#-Code] Value Object inkl. Validierungslogik angelegt, bevor ein Szenario die Validierung treibt**
  Was: Für den „Zutat anlegen"-Happy-Path wurde `NonEmptyTrimmedString` mit voller Validierungslogik angelegt; deren Error-Zweig ist ungeübt → brauchte eine Suppression (ADR-S000-4).
  Warum: Value-Object-Pflicht gegen YAGNI ausgespielt – die Validierung gehört erst zum @US-904-error-Szenario.
  Regel: Treibt das Szenario die Validierung noch nicht, das Value Object mit dem **Zielnamen** anlegen, die Validierungslogik aber weglassen (Kommentar: Name vorab gewählt, Validierung folgt im Error-Szenario) – das ist die korrekte Variante (kein ungeübter Zweig, keine Suppression). Volle Validierung+Suppression jetzt oder den Typ ganz aufschieben nur bei signifikantem Vorteil. (Hier blieb der Code als Variante „volle Validierung jetzt", weil der Rückbau den Aufwand nicht wert war – nicht weil das die richtige Schreibweise war.)

- **[MITTEL] [PROZESS] [Doku] Working-Memory-Notiz nicht selbsterklärend (nur für Eingeweihte verständlich)**
  Was: In AGENT_MEMORY notierte ich „ADR-S000-12-Präzisierung (Middleware vs. pro Endpoint)" – selbst die beim Entwurf beteiligte Userin konnte daraus die eigentliche offene Frage nicht rekonstruieren.
  Warum: Die Notiz setzte den Session-Kontext voraus, statt die Sache selbst zu enthalten (welcher Widerspruch, welche Entscheidung, woraus).
  Regel: Jede Handoff-/Working-Memory-Notiz so schreiben, dass ein Agent mit **frischem Kontext** allein daraus die offene Frage und die nötige Entscheidung ableiten kann – Substanz statt Stichwort/geprägter Begriff; bei Verweisen präzise auf den Ort des vollen Kontexts zeigen.

- **[GERING] [PROZESS] [Review] Nicht-E2E-beobachtbare Anforderungen am falschen Test-Level verortet**
  Was: Bei ETag erwog ich kurz einen E2E-/Frontend-Treiber, obwohl ein Caching-Header weder nutzer- noch (ohne Conditional-Requests) frontend-beobachtbar ist.
  Warum: Outside-In („kein Code ohne Test darüber", ADR-S041-5) reflexhaft auf eine technische Transport-Eigenschaft angewandt, die auf E2E-Ebene gar nicht beobachtbar ist.
  Regel: Anforderungen auf der **obersten Schicht testen, auf der sie beobachtbar sind** – Caching-Header/Concurrency-Token auf Service-Client- (MSW) bzw. Integrations-Ebene, nicht via Gherkin/E2E. Ein fehlender E2E-Treiber ist für solche Querschnitts-Eigenschaften kein Outside-In-Verstoß (→ geplantes ADR-S041-5-Addendum).

## Session 082 – 2026-06-12

- **[MITTEL] [PROZESS] [Gherkin] Szenario-Reihenfolge invertiert – komponiertes vor atomarem Baustein**
  Was: Ein früherer `gherkin-workshop` ordnete „Felder nach Abbrechen wieder leer" (komponiert) vor „Abbrechen schließt + verwirft" (atomar); Folge bei der Implementierung: das komponierte Szenario musste beide Verhaltensteile auf einmal erzwingen, das atomare wurde zum wirkungslosen Guard-Test ohne RED-Beitrag.
  Warum: Die Sortierregel kannte nur „trivial→komplex" + „ohne Backend vor mutierend" – beide Szenarien sind No-Backend-UI, fielen in dieselbe Gruppe; das Abhängigkeits-/Aufbauprinzip fehlte als Kriterium.
  Regel: Szenarien innerhalb einer Kategorie primär nach Aufbau-Abhängigkeit sortieren – setzt B das in A geprüfte Verhalten voraus, muss A vor B; atomare Verhaltensbausteine vor den darauf komponierten (jetzt in `gherkin-workshop` SKILL Schritt 3.4 + Review-Agent verankert).

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
