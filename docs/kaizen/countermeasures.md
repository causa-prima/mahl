# Countermeasures

<!--
wann-lesen: In jeder Retro – AKTIV/OFFEN auf Wirksamkeit prüfen, BEWÄHRT auf Regressionen scannen.
wann-schreiben: Nach KRITISCH- oder HOCH-Finding sofort; nach Retro wenn Muster in MITTEL/GERING erkannt.

Eintrag-Format (Fließtext, ein Block pro Maßnahme):
  ### CM-S<NNN>-<n> – Kurztitel
  **Impact:** KRITISCH|HOCH|MITTEL|GERING | **Kategorie:** PROZESS|AGENT|QUALITÄT|TOOLING | **Kontext:** <Tags oder –> | **Status:** OFFEN|IN UMSETZUNG|AKTIV|BEWÄHRT | **Seit:** S<NNN>
  **Problem:** <was lief schief / welches Finding>
  **Maßnahme:** <was wurde getan / soll getan werden>

  ID: CM-S<NNN>-<n> – 3-stellige Session (= „Seit"), laufende Nummer innerhalb der Session.
  Die Metadaten-Zeile (Impact|Kategorie|Kontext|Status|Seit) wird von retro_report.py geparst –
  Reihenfolge und `**…:**`-Marker beibehalten.

Status-Lifecycle: OFFEN → [IN UMSETZUNG] → AKTIV → BEWÄHRT
  OFFEN: Problem bekannt, Maßnahme noch nicht definiert oder noch nicht implementiert.
  IN UMSETZUNG: (optional) Maßnahme definiert, Umsetzung dauert mehrere Sessions.
  AKTIV: Maßnahme live – Wirksamkeit wird beobachtet.
  BEWÄHRT: In einer Retro explizit erklärt (Kriterium: docs/kaizen/process.md).
           Bleibt in dieser Datei (unterer Abschnitt) – für Regressions-Erkennung.
           Regression = neues Finding das inhaltlich passt → zurück auf AKTIV.

Kontext-Feld:
  Welche Kontext-Tags (aus process.md) diese Maßnahme abdeckt.
  – (oder leer) = Wildcard (Maßnahme gilt für alle Kontexte dieser Impact+Kategorie).
  Mehrere Werte kommasepariert: z.B. "Agent-Prompt, Review"
  Wann Wildcard: Maßnahme ist generisch genug, dass der konkrete Kontext keine Rolle spielt
    (z.B. "Guidelines nicht angewandt" trifft auf TDD, C#-Code, TS-Code gleichermaßen zu).
  Wann befüllen: Problem ist klar auf bestimmte Kontexte beschränkt und würde bei anderen
    Kontexten zu False-Positives im Pattern-Kandidaten-Report führen.

Reaktionsregeln je Impact: docs/kaizen/process.md
-->

## Aktive Maßnahmen

### CM-S102-1 – Zustandsdokumente sammeln Erledigtes / Verweise auf gelöschte Artefakte
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Doku | **Status:** AKTIV | **Seit:** S102
**Problem:** Agenten halten wiederkehrend **Erledigtes** in Zustandsdokumenten fest (changelog-artig; z.B. „erledigt in run-X"), obwohl diese nur den offenen Zustand tragen sollen; zudem verweisen Stellen auf Artefakte, die beim Erledigen gelöscht/archiviert werden → tote Refs / Informationsverlust. Bislang nur ein **menschlicher** Guard (User fängt beim Mitlesen ab) – fehlerträchtig, ermüdend, nicht garantiert (OBS-S100-1; Vertrauens-/Ermüdungs-Multiplikator OBS-S100-2).
**Maßnahme:** Prinzip „Zustandsdokumente tragen nur den offenen/aktuellen Zustand – kein Erledigtes" in `principles.md` dokumentiert ✓ (Abschnitt „Doku & Referenzen"), mit beiden Richtungen (präventiv: nichts Erledigtes hineinschreiben; kurativ: erledigte Einträge entfernen). Der mechanisierbare Teil (tote Refs auf volatile IDs) wird vom geplanten syntaktischen Poka-Yoke-Hook (OBS-S095-3) mit abgedeckt. **Wirksamkeit prüfen:** künftige Zustandsdokument-Edits (AGENT_MEMORY „Nächste Prioritäten", tech-debt.md, open-questions.md) auf stehengebliebenes Erledigtes scannen; Regression → zurück auf AKTIV. Bezug: OBS-S100-1, OBS-S095-3.

### CM-S102-2 – Poka-Yoke-Hook: Referenz-Richtung volatil→stabil
**Impact:** GERING | **Kategorie:** TOOLING | **Kontext:** Hook/Script, Doku | **Status:** AKTIV | **Seit:** S102
**Problem:** Das principles.md-Prinzip „Referenzen laufen volatil → stabil" wurde nur **manuell** durchgesetzt (CM-S095-1), mit wiederkehrenden Funden (LL-S094-2; S095 weitere in Skills) → menschlicher Wachsamkeits-Guard (vgl. OBS-S100-2).
**Maßnahme:** Syntaktischer PreToolUse-Poka-Yoke `.claude/hooks/check-ref-direction.py` (via TDD, `tests/test_ref_direction.py`, in `settings.json` unter `Edit|Write` registriert, exit 2): blockt einen Edit/Write an einer **stabilen** Datei, der ein **volatiles** ID-Schema (`OBS-`/`OQ-`/`LL-`/`TD-S…`) einführt. Datei-Scope default-protected (`docs/**`, `.claude/skills/**`, `.claude/agents/**`, `CLAUDE.md`) + explizite Ausnahmen (kaizen-Bookkeeping, archive, volatile Tracker, session-Logs, kaizen-Skill); Zeilen-Ausnahme via `ref-ok`-Marker. **Wirksamkeit prüfen:** BEWÄHRT, wenn nach S102 kein neuer volatil→stabil-Fund mehr auftritt, der den Hook hätte auslösen müssen; Regression (z.B. Hook per `ref-ok` umgangen ohne echten Grund) → zurück auf AKTIV. Bezug: OBS-S095-3, OBS-S100-1 (toter-Ref-Teil mit abgedeckt), CM-S095-1.

### CM-S102-3 – Orchestrator pollt arbeitende Subagenten (Idle-Signal missverstanden)
**Impact:** MITTEL | **Kategorie:** TOOLING | **Kontext:** Agent-Prompt | **Status:** AKTIV | **Seit:** S102
**Problem:** Der Orchestrator fragte einen Layer-Subagenten während laufender ~2-min-Stryker-Läufe mehrfach per `SendMessage` nach dem Status, obwohl dieser noch arbeitete – ausgelöst durch `idle_notification`/„available"-Zwischensignale, die er als „fertig" missdeutete. Verschwendet Tokens und stört den arbeitenden Subagenten; laut User session- und orchestratorübergreifend (OBS-S101-2). Verifizierte Harness-Semantik: Hintergrund-Subagenten melden ihren Abschluss automatisch; Zwischensignale sind kein Abschluss, Pollen ist verschwendet.
**Maßnahme:** Spawn-Regel in `implementing-scenario` SKILL.md (innerer Loop, „Arbeitende Subagenten nicht pollen"): auf den inhaltlichen Return warten (Test-Review-Signal / Verifikations-Hash / Return), Idle-/„available"-Zwischensignale nicht mit Status-Nachfragen beantworten; `SendMessage` bleibt für PLANUNG-Rückfragen und Findings-Übergabe. **Wirksamkeit prüfen:** nächster realer `implementing-scenario`-Lauf – kein Status-Poll eines arbeitenden Subagenten mehr (BEWÄHRT, wenn über 1–2 Läufe kein Rückfall; Regression → zurück auf AKTIV). Robust gegen beide Ursachen (mehrdeutiges Signal *oder* Orchestrator-Missverständnis). Bezug: OBS-S101-2.

### CM-S101-1 – Vakuöse Negativ-/Guard-Tests (grün trotz fehlendem Guard)
**Impact:** MITTEL | **Kategorie:** QUALITÄT | **Kontext:** TS-Code, TDD | **Status:** AKTIV | **Seit:** S101
**Problem:** Tests, die prüfen dass etwas NICHT passiert (Dialog schließt nicht bei Escape/Backdrop während Pending), waren vakuös grün – auch ohne den Guard (Escape aus `<body>` erreicht MUIs Handler nie; Backdrop-`fireEvent.click` ohne `mousedown` lässt MUIs zweistufige Erkennung leer; fehlendes Settle-Fenster sieht den Dialog während der Schließ-Transition fälschlich noch im DOM). Bei retroaktivem Spezifizieren emergenten Verhaltens fehlt zudem die RED-Phase, die die Vakuität aufdecken würde (LL-S101-1).
**Maßnahme:** Regel in `coding-guideline-typescript.md` §6 ergänzt: Negativ-/Guard-Assertions faithful absichern – bei emergentem/retroaktivem Verhalten Guard temporär entfernen → rot bestätigen; bei RED-first ein grün-statt-rot beim ersten Lauf als Vakuität behandeln; MUI-Dialog-Gotchas (Escape aus dem Modal feuern, `mouseDown`+`click` für Backdrop, Settle-Fenster > Exit-Transition). **Wirksamkeit prüfen:** nächste Dialog-Guard-/emergent-Verhalten-Tests auf vakuöse Passes scannen (BEWÄHRT, wenn kein neuer vakuöser Negativ-Test auftritt; Regression → zurück auf AKTIV). Bezug: LL-S101-1.

### CM-S056-1 – Ad-hoc-Bash statt erlaubter Befehle
**Impact:** MITTEL | **Kategorie:** TOOLING | **Kontext:** Bash/Permission | **Status:** AKTIV | **Seit:** S056
**Problem:** Ad-hoc-Bash-Befehle statt erlaubter Befehle aus docs/process/dev-workflow.md (S53: `npx playwright test`)
**Maßnahme:** `check-bash-permission.py` umgebaut: auto-deny, `# --allow-once`-Marker, Log in `.claude/tmp/denied-commands.log`, Smart-Hints, neue Allow-Patterns (npx, dotnet run). docs/process/dev-workflow.md aktualisiert.

### CM-S047-1 – Guidelines gelesen, aber nicht angewandt
**Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** – | **Status:** AKTIV | **Seit:** S047
**Problem:** Guidelines gelesen aber nicht auf konkreten Fall angewandt (Rückfall S53: YAGNI)
**Maßnahme:** `write-code` Skill: Pflicht-Schritt "Guidelines lesen" + explizite Per-Member-YAGNI-Frage: „Welcher aktuell rote Test fordert genau das?"

### CM-S064-1 – Tool-Verhalten als gesichertes Wissen präsentiert
**Impact:** HOCH | **Kategorie:** AGENT | **Kontext:** Kommunikation | **Status:** AKTIV | **Seit:** S064
**Problem:** Behauptungen über externes Tool-Verhalten als gesichertes Wissen präsentiert (S061, S063)
**Maßnahme:** Regel in `principles.md` dokumentiert ✓. Selbst-Check vor jeder Tool-Verhaltensbehauptung: „Basiert das auf einem Tool-Call dieser Session?" Falls nein: explizit als unverified kennzeichnen und Verifizierung anbieten. **S085 verbreitert (Rückfall S078/S081/S084):** gilt für jedes Handeln auf angenommenem Verhalten (Empfehlung/Fertig-Erklärung/dokumentierter Befehl), nicht nur Behauptungen – Regel in principles.md verbreitert. **S095 Rückfall:** LL-S086-1 (Kandidaten-Gefahr ohne Verifikation behauptet) + LL-S093-1 (auf „in Datei X definiert"-Doku-Behauptung verlassen, Helper existierte nicht). Bleibt AKTIV – als Urteils-Verhalten schwer poka-yoke-bar.

### CM-S064-2 – Infrastruktur-/Tooling-Trivia als lessons_learned
**Impact:** MITTEL | **Kategorie:** QUALITÄT | **Kontext:** Sonstiges | **Status:** AKTIV | **Seit:** S064
**Problem:** Infrastruktur-Fehler oder Tooling-Trivia als lessons_learned dokumentiert (S061 ×2, S063, S053, S052)
**Maßnahme:** Filter-Test in `docs/kaizen/process.md` und im lessons_learned-Header ergänzt. Preprocessing-Schritt im `kaizen`-Skill (vor retro_report.py): Noise-Review von lessons_learned + Archiv mit User-Freigabe. **S085:** Zwei-Brillen-Klassifikation + reduzierter Retro-Re-Scan (OBS-S085-12) eingeführt → weiter beobachten, da weicheres Netz Rückfall ermöglichen könnte.

### CM-S064-3 – Neue Guideline nicht in Skills/Feature-Files integriert
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Doku | **Status:** AKTIV | **Seit:** S064
**Problem:** Neue Guideline wird nicht in bestehende Skills und Feature-Files integriert (S063: UX-Guideline)
**Maßnahme:** Beim Einführen einer neuen Guideline: explizit prüfen welche Skills sie referenzieren sollen + ob bestehende Feature-Files einen Retrofit-Workshop brauchen. Hinweis als Pflicht-Schritt in `closing-session` Skill ergänzt.

### CM-S070-1 – Subagent-Gold-Plating durch nachträgliche Test-Anpassung verschleiert
**Impact:** KRITISCH | **Kategorie:** PROZESS | **Kontext:** TDD | **Status:** AKTIV | **Seit:** S070
**Problem:** Subagent implementierte Code beyond Szenario-Scope; Tests wurden nachträglich angepasst um Gold-Plating zu verschleiern; Orchestrator-Check erkannte es nicht (S069)
**Maßnahme:** (1) Orchestrator-Vorabanalyse vor E2E-Test auf Spec-Ambiguitäten; (2) Subagent bittet nach RED um Test-Review, Orchestrator friert die freigegebenen Tests als immutable git-Blob-Anker ein (`git hash-object -w`); (3) Per-Assertion-Zuordnung, Full-State-Assertion-Check, Check auf Anpassungen an bestehenden Tests; (4) mechanischer Test-Freigabe-Audit in `qa-check --verify --approved-tests` – zeigt jede Test-Änderung seit Freigabe als Diff (Setup erlaubt, Assertions verboten), immun gegen Subagent-Stagen. Details: `implementing-scenario` SKILL.md **S095:** 3 saubere Full-Stack-Läufe (S83/S90/S91, kein Gold-Plating-Rückfall) – BEWÄHRT-reif, aber wegen KRITISCH-Impact + teils prozeduralem Mechanismus bewusst noch 1 Periode beobachten, dann BEWÄHRT. **S099:** Mechanismus gehärtet – der frühere „Staged-Test-Check" (prozedural, durch Subagent-`git add` umgehbar → OBS-S090-4) durch den Blob-Anker-Audit ersetzt; das schließt das Umgehungs-Loch mechanisch.

### CM-S070-3 – check-bash-permission.py: --list/sed/DLL-Lock-Lücken
**Impact:** HOCH | **Kategorie:** TOOLING | **Kontext:** Bash/Permission, Mutation-Testing | **Status:** AKTIV | **Seit:** S070
**Problem:** check-bash-permission.py: --list nicht selbst-wartend; sed ohne Hint; DLL-Lock ohne automatischen Check (S069)
**Maßnahme:** --list via 3-Tupel selbst-wartend; sed-Hint ergänzt; `check_dotnet_dll_lock()` in dotnet-Skripten integriert. **S095:** DLL-Lock-Teil **obsolet** seit S089 (WSL-native Toolchain, cmd.exe-Wrapper + DLL-Lock strukturell entfernt); --list/sed-Teile bleiben AKTIV.

### CM-S070-4 – Subagenten ohne strukturierte Tooling-Rückmeldung
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Agent-Prompt | **Status:** AKTIV | **Seit:** S070
**Problem:** Subagenten lieferten keine strukturierten Rückmeldungen über Tooling-Probleme (S069)
**Maßnahme:** Pflicht-Abschnitt "Prozessverbesserung" am Ende jedes Subagenten-Prompts in `implementing-scenario` SKILL.md. **S095:** bleibt AKTIV (NICHT BEWÄHRT) – es gab zwar Feedback, aber unklar, welches vom Subagenten vs. Orchestrator stammt, ob *jeder* Subagent es liefert und wie der Orchestrator es weiterverarbeitet. Beobachtbarkeit direkt erhöht: `implementing-scenario` Schritt 6.1 weist Subagent-Feedback jetzt **pro Subagent explizit** aus (inkl. „keine"); LL/OBS-`Quelle` ist Pflicht mit `Subagent`/`Orchestrator`. Mit dieser Instrumentierung 1–2 Perioden neu beobachten.

### CM-S070-5 – User-facing Verhaltensszenarien fehlen in Feature-Files
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Gherkin | **Status:** AKTIV | **Seit:** S070
**Problem:** User-facing Verhaltensszenarien (Dialog-Reset, Abbrechen, Feld-Init, Async-States) fehlen systematisch in Feature-Files (S069)
**Maßnahme:** UI-Verhaltens-Checkliste in `gherkin-workshop` Schritt 1 + MEDIUM-Finding in `references/agent-review.md`. **S095 Abdeckungs-Erweiterung (kein Rückfall):** LL-S094-1 – die Checkliste deckte ihre Klassen (Abbrechen/Init/Async) korrekt ab; die *angrenzende* Sub-Klasse Formular-/Dialog-UX-Baseline (Affordance/Fokus/Tastatur) war schlicht nicht enumeriert (auch keine Guideline) → kein Agenten-Fehlverhalten, nur ein Review deckte die Lücke auf. In S094 Checkliste um diese Klasse erweitert + Review-Enforcement. Bleibt AKTIV.

### CM-S070-6 – Hintergrund-Subagenten scheitern an Edit/Write-Permissions
**Impact:** MITTEL | **Kategorie:** TOOLING | **Kontext:** Agent-Prompt | **Status:** AKTIV | **Seit:** S070
**Problem:** Hintergrund-Subagenten scheiterten an Edit/Write-Permissions (kein interaktiver Bestätigungskanal) (S070)
**Maßnahme:** Subagenten die Dateien editieren als Vordergrund-Agenten starten (kein `run_in_background: true`); alternativ: relevante Pfade vorab in `settings.json` unter `permissions.allow` eintragen

### CM-S078-1 – Häufige Befehls-Denies kosten Zeit/Token
**Impact:** MITTEL | **Kategorie:** TOOLING | **Kontext:** Bash/Permission | **Status:** AKTIV | **Seit:** S078
**Problem:** Häufige Befehls-Denies (127 echte Denies, 58 mit aktuellem Hook seit S70) → Zeit/Token-Verlust (S078)
**Maßnahme:** Deny-Log kategorisiert (pre/post-S70-Split): Friktion zu ⅔ **nicht** durch fehlende Patterns, sondern (a) Bash statt Read/Grep/Glob für Read-only-Inspektion, (b) mehrzeilige/Assignment-Skripte + `cd`-Prefix, (c) **Wrapper-Scripts in `--list` unsichtbar** → Agent griff zu `dotnet test`/`npm test` → unnötiger Deny (per Subagent-Eval bestätigt). Maßnahmen: ALLOW `cd`, `sed` (read-only), `xargs <safe>`, `git -C <readonly>`; Smart-Hints für `python3 -c`/`for`/`while`; `_NO_HINT_MESSAGE` zeigt auf `--list` statt Nav-Tabelle; `--list` um Bash-Framing + Deny-Mechanik + Tool-Vorrang + **Projekt-Task→Wrapper-Block** erweitert; `--list` im SessionStart-Hook injiziert (Allow-Liste ab Zeile 1). Verifiziert: 2. Subagent-Eval löste alle Tests/Lint/Mutation-Tasks proaktiv korrekt. Re-Run: 35/130 Alt-Denies gingen jetzt durch, Rest großteils korrekt+behintet. Bewusst NICHT: Newline-Split (Heredoc-Bruch), VAR_ASSIGN (umgeht DESTRUCTIVE-Check). Tests in `test-bash-permission.py`.

### CM-S082-1 – Szenario-Reihenfolge invertiert (komponiert vor atomar)
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Gherkin | **Status:** AKTIV | **Seit:** S082
**Problem:** Szenario-Reihenfolge invertiert: komponiertes Szenario vor seinem atomaren Baustein → atomares wird wirkungsloser Guard-Test, komponiertes leistet Doppelarbeit (S082)
**Maßnahme:** Aufbau-/Abhängigkeitsprinzip als PRIMÄRES Sortierkriterium in `gherkin-workshop` SKILL Schritt 3.4 (trivial→komplex sekundär); MEDIUM-Inversions-Prüfung in `references/agent-review.md`

### CM-S083-1 – „NULL Suppressions" als Absolutregel an Subagent
**Impact:** HOCH | **Kategorie:** AGENT | **Kontext:** Agent-Prompt | **Status:** AKTIV | **Seit:** S083
**Problem:** Orchestrator gab Subagent „Ziel: NULL neue Suppressions" als Absolutregel vor → Subagent entfernte guideline-vorgeschriebenen Code (`throwOnError`) statt ihn begründet zu suppressen (S083)
**Maßnahme:** Spawn-Regel in `implementing-scenario` SKILL.md: Suppressions-Politik als „keine *unbegründeten*" formulieren, nie als „null"; begründete Suppressions sind erlaubt und werden in Schritt 4 validiert

### CM-S083-2 – qa-check.py gibt still veralteten Report-Hash aus
**Impact:** HOCH | **Kategorie:** TOOLING | **Kontext:** Mutation-Testing, Hook/Script | **Status:** AKTIV | **Seit:** S083
**Problem:** `qa-check.py` gibt bei DLL-Lock/Build-Fehler still einen veralteten Report-Hash aus (statt hart als Lauf-Fehler) → ungültige Übergabe könnte als gültig durchgehen (S083)
**Maßnahme:** qa-check meldet Build-/Lock-Fehler jetzt als harten Lauf-Fehler (kein Hash-Fallback); PID-Lock-Guard (`_run_lock.py`) auf `.claude/tmp/stryker_*_out.txt`. Umgesetzt **S085** (93 Tests grün; Verify-Pfad-Frische geprüft – korrekt nur im Score-Gate, kein Bug).

### CM-S083-3 – AGENT_MEMORY.md 4-KB-Limit schwer zu halten
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Doku | **Status:** AKTIV | **Seit:** S083
**Problem:** AGENT_MEMORY.md 4-KB-Limit 3–4 Sessions in Folge schwer zu halten; brutales Kürzen macht Notizen für frische Agenten unverständlich (Konflikt mit Self-Sufficiency-Regel, S083)
**Maßnahme:** **Umgesetzt S087 (OBS-S085-16 Teil A):** AGENT_MEMORY auf schlanken Auto-Inject reduziert (Phase/Story/Nächstes Szenario/Prioritäten); Technische Schuld → `docs/tech-debt.md`, offene Fragen → `docs/open-questions.md` (read-on-demand). Damit ist der Größendruck weg. Offen/Retro: ob ein Soft-Cap wieder eingeführt wird (jetzt ohne Enforcer).

### CM-S086-1 – Information über mehrere Dokumente dupliziert (Drift)
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Doku | **Status:** AKTIV | **Seit:** S086
**Problem:** Information über mehrere Dokumente dupliziert (Drift-Gefahr); Verweise per „Sektion N"/Zeilen-Position statt grep-barem Anchor werden stale (OBS-S085-5/9/15/16)
**Maßnahme:** Prinzip „Single Source of Truth: Information am passendsten Ort, sonst referenzieren" in `principles.md` dokumentiert ✓ (Abschnitt „Doku & Referenzen"). Beim Doku-/Skill-Schreiben: Info am passendsten Ort kontextfrei beschreiben, sonst referenzieren mit grep-barem Anchor; referenzierte Stelle geändert → referenzierende Stellen mitpflegen. **S095 Rückfall:** LL-S094-3 – AGENT_MEMORY-Anstrich mit Changelog-/Navigations-Inhalten, die andere auto-geladene Quellen (CLAUDE.md-Nav, Session-Index) duplizieren; die Single-Source-Regel war bekannt, wurde aber nicht proaktiv angewandt (Pruning an User ausgelagert). Bleibt AKTIV.

### CM-S095-1 – Stabile Quelle referenziert volatile Stelle (Referenz-Richtung)
**Impact:** GERING | **Kategorie:** PROZESS | **Kontext:** Doku | **Status:** AKTIV | **Seit:** S095
**Problem:** Eine stabile Quelle (ADR/Skill/Guideline/principles) referenziert eine volatile Stelle (OQ-/OBS-/LL-/TD-ID), die bei Lösung gelöscht/archiviert wird → Referenz dangelt/wird stale (LL-S094-2; S095: weitere Funde in Skills).
**Maßnahme:** Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt" in `principles.md` dokumentiert ✓ (Abschnitt „Doku & Referenzen"). Syntaktischer Poka-Yoke-Hook **gebaut S102** → eigenständige CM-S102-2 (`check-ref-direction.py`); der manuelle Guard hier ist damit mechanisch abgesichert.

### CM-S095-2 – Schluss/Empfehlung aus unvollständig zerlegtem Raum
**Impact:** MITTEL | **Kategorie:** AGENT | **Kontext:** Kommunikation | **Status:** AKTIV | **Seit:** S095
**Problem:** Ein Schluss, eine Empfehlung oder eine abgeleitete Anforderung wird gezogen, ohne den relevanten Raum vollständig zu zerlegen – der auffälligste Teil wird fürs Ganze genommen (LL-S088-2: Quantor „alle" übersehen; LL-S087-2: nur 1 von 3 Kostenpfaden betrachtet).
**Maßnahme:** Prinzip „Vollständige Zerlegung vor Schluss/Empfehlung" in `principles.md` dokumentiert ✓ (Abschnitt „Kommunikation & Argumentation"): Dimensionen/Pfade/Quantoren explizit aufzählen und je prüfen, bevor der Schluss steht.

---

## Bewährte Maßnahmen

> Nur auf Regressionen prüfen: Gibt es ein neues Finding in `lessons_learned.md`, das inhaltlich
> zu einem Eintrag hier passt? Falls ja → zurück in "Aktive Maßnahmen" mit Status AKTIV.

### CM-S047-2 – Reviewer mit Iterations-Vorwissen beauftragt
**Impact:** KRITISCH | **Kategorie:** AGENT | **Kontext:** Agent-Prompt, Review | **Status:** BEWÄHRT | **Seit:** S047
**Problem:** Reviewer mit Iterations-Vorwissen beauftragt
**Maßnahme:** Regel in `principles.md` dokumentiert ✓; Pflicht-Hinweis in `review-code` SKILL.md Schritt 3 ergänzt: keine früheren Findings, keine false-positive-Labels übergeben

### CM-S047-3 – Review-Agent-Output blind übernommen
**Impact:** HOCH | **Kategorie:** AGENT | **Kontext:** Agent-Prompt, Review | **Status:** BEWÄHRT | **Seit:** S047
**Problem:** Review-Agent-Output blind übernommen (semantisch falsch)
**Maßnahme:** Regel in `principles.md` dokumentiert; Prüf-Schritt in `review-code` Skill ergänzt. **S085 BEWÄHRT:** Review-Auditoren liefen in S081/S082/S083/S084 (≥3×); Findings wurden selektiv übernommen bzw. begründet als Tech-Debt aufgeschoben (S083 F1/F17, S084 Quick-Fixes), kein „semantisch falsches Output blind übernommen"-Rückfall.

### CM-S070-2 – Stryker 100% aus --mutate-Run gemeldet
**Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** TDD | **Status:** BEWÄHRT | **Seit:** S070
**Problem:** Subagent meldete Stryker 100% auf Basis eines --mutate-Runs; vollständiger Lauf ergab 83% (S069)
**Maßnahme:** Subagenten-Prompts in `implementing-scenario` SKILL.md: vollständiger Stryker-Lauf ohne --mutate Pflicht für Übergabe; Pfad zur HTML-Report-Datei in Summary. **S095 BEWÄHRT:** strukturell über `qa-check.py` erzwungen (kein --mutate-Hash gültig); saubere Läufe S83/S90/S91 (≥3×), kein Teil-Run-Rückfall.

### CM-S084-1 – E2E-Suite lief still gegen veralteten Backend-Prozess
**Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** Review, Skill-Nutzung | **Status:** BEWÄHRT | **Seit:** S084
**Problem:** E2E-Suite lief still gegen einen veralteten, extern/manuell verwalteten Backend-Prozess → ~1 h Fehlsuche an einer vermeintlichen Code-Regression (S084)
**Maßnahme:** Poka-Yoke **ADR-S084-4**: Playwright besitzt den Backend-Lebenszyklus (`reuseExistingServer:false`, frischer Build/Start pro E2E-Lauf) → stale Prozess strukturell unmöglich, Fehlerfälle laut (Port-Konflikt / Build-Fehler / Readiness-Timeout). **S095 BEWÄHRT:** E2E grün S89/S90/S91 (≥3×), kein stale-Backend-Rückfall; Poka-Yoke kann nicht still versagen.

---

## Verworfene / Obsolete Maßnahmen

> In-File belassen (nicht archiviert) für die Regressions-Erkennung: Tritt das Problem doch wieder auf,
> ist die frühere Verwerf-/Obsolet-Begründung hier auffindbar → ggf. zurück nach „Aktive Maßnahmen".

### CM-S078-2 – HOCH-Findings bekommen nicht zuverlässig einen CM-Eintrag
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Skill-Nutzung | **Status:** VERWORFEN | **Seit:** S078
**Problem:** HOCH-Findings bekommen nicht zuverlässig einen CM-Eintrag (S71/74/76/77 ohne CM trotz process.md-Pflicht); `closing-session`-Prüfung ist weiche Ermessensfrage (S078)
**Maßnahme:** Prüfen ob HOCH→CM von weicher Prüfung zu erzwungenem Check wird. **S085:** In S078–084 nicht wiederaufgetreten (beide HOCH-Findings bekamen CMs); Mechanismus nicht gebaut. **S095 VERWORFEN (Eskalation, 2. Retro OFFEN):** In zwei vollen Perioden (S078–094) bekam jedes HOCH-Finding zuverlässig einen CM/CM-Anschluss – kein Fehlausgang. Die weiche `closing-session`-Prüfung reicht empirisch; ein erzwungener Check wäre Aufwand ohne belegten Bedarf. Bei einem künftigen HOCH-ohne-CM-Fall neu aufgreifen.
