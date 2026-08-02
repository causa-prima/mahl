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

### CM-S114-2 – Gemessen statt geschätzt: Zugriff auf große Dateien gezielt statt vollständig
**Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** Agent-Prompt, Doku, Hook/Script | **Status:** AKTIV | **Seit:** S114
**Problem:** `Read` ist mit Abstand der größte Token-Posten und wächst mit der Codebasis (OBS-S109-1). Drei Annahmen darüber erwiesen sich beim Nachmessen als falsch: (a) *„der Harness erzwingt das Lesen"* – nur rund ein Drittel des Lesens auf Code/Tests ist Vor-Edit, zwei Drittel sind Orientierung; (b) *„die ADR-Übergabe an Subagenten kostet ~50k Token je Lauf"* (OBS-S111-2) – die Vorschrift wurde über 24 Schicht-Aufträge **nie** befolgt, der Aufwand lag bei den `--full`-Aufrufen des Orchestrators; (c) *„Tracker-Dateien sind ein Nebenposten"* – `docs/kaizen` ist zu 50 % erzwungener Vor-Edit-Read, davon nur 23 % gezielt (OBS-S096-3). Zusätzlich fehlte die Messgüte: Tool-Ausgaben über ~60 KB werden aus dem Session-Log ausgelagert, die Vorgänger-Messung untercountete sie, und ihr Script lag als Wegwerf-Code in `.claude/tmp/` und musste aus einem alten Log rekonstruiert werden.
**Maßnahme:** **Messen wurde reguläres Werkzeug**, nicht Wegwerf-Code: `read-breakdown.py` (Read-Volumen nach Session-Art/Bereich/Datei, löst ausgelagerte Ausgaben auf) und `tool-usage.py` (Filter-Quote, LSP-Nutzung) mit dem Modul `_session_logs.py`. Neu darin die **Aufschlüsselung nach Session-Art** – die Vorgänger-Messung scannte nur Sessions mit Subagenten und traf damit unbemerkt eine Aussage über allein implementing-scenario-Sessions. Erkennung primär über `attributionSkill`, Rest über eine Heuristik auf den editierten Dateien (abzüglich der Dateien, die `closing-session` ohnehin in jeder Session anfasst) und die kuratierte `.claude/session-types.json`. **Abgeleitete Eingriffe:** (1) `test-inventory.py` gibt Testnamen mit **Zeilenbereich** (C#/TS) – beide Layer-Implementer nehmen sie statt des Voll-Reads, der Bereich macht den Folge-Read gezielt; (2) `implementing-scenario` filtert ADRs nicht mehr über `scope:` (trägt fast den ganzen Bestand), sondern über die fachlichen Dimensionen, und übergibt Volltext plus Suchbefehl für die unabhängige Gegenprobe des Subagenten; (3) `obs.py`/`lessons.py` schreiben Tracker-Einträge, ohne die Datei zu lesen. **Wirksamkeit prüfen:** BEWÄHRT, wenn `read-breakdown.py --by-area --type implementierung` bis S120 einen sinkenden Anteil vollständiger Reads auf `Client/` und `Server/` zeigt; bleibt er gleich, war das Werkzeug nicht die Antwort und die Ursache liegt tiefer. Bezug: OBS-S109-1, OBS-S111-2, OBS-S096-3, OBS-S085-3 (Nudges bewegen die Quote nicht), OBS-S111-3 (Wegwerf-Auswertungen desselben Reports).

### CM-S114-1 – Poka-Yoke-Hook: TD-Eintrag ohne belastbare Fälligkeit
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** tech-debt, Hook/Script | **Status:** AKTIV | **Seit:** S114
**Problem:** Die Eintrags-Vorlage in `docs/tech-debt.md` definierte ein Feld als „geplante Behebung **oder** auslösende Bedingung" – wer die Behebung ausformulierte, erfüllte die Vorlage formal, ohne dass jemand einen Zeitpunkt schuldete (OBS-S112-1, LL-S112-1). Daneben stand ein `**Priorität:**`-Feld, das im gesamten Tooling nachweislich keinen einzigen Leser hatte und entsprechend nichts steuerte (OBS-S112-2): TD-S089-1 lag ~22 Sessions mit „Hoch" unbearbeitet. Drittens wurden Verletzungen **heute geltender** Regeln wie optionale Posten mit weichem Auslöser geführt und erbten deren Unverbindlichkeit (OBS-S112-6). Dass Lese-Disziplin hier nicht trägt, ist belegt: Das Muster unterlief dem Orchestrator beim Neuschreiben eines Eintrags erneut, unmittelbar nachdem es in derselben Session diagnostiziert worden war (LL-S112-1).
**Maßnahme:** Vorlage auf drei Pflichtfelder umgestellt (`**Fällig:**` / `**Problem:**` / `**Behebung:**`), `**Priorität:**` ersatzlos gestrichen, alle 20 Bestandseinträge migriert. Abgesichert durch den syntaktischen PreToolUse-Poka-Yoke `.claude/hooks/check-td-capture.py` (via TDD, `tests/test_td_capture.py`, im Dispatcher `dispatch-edit-write.py` registriert, exit 2): geprüft werden **neu hinzukommende und geänderte** Einträge – unberührte Altlast blockt nie. Der Hook fordert die drei Felder, blockt die abgeschafften (`**Priorität:**`, `**Behebung/Trigger:**`) und koppelt `**Fällig:** jetzt` daran, dass die TD-ID in `docs/AGENT_MEMORY.md` vorkommt – nur diese Datei wird bei jedem Session-Start injiziert, `tech-debt.md` dagegen nur situativ; ein „jetzt", das nur im Tracker steht, wird nie vorgelegt. Bewusst **keine** abschließende Feldliste (anders als CM-S107-1): TD-Einträge führen legitime fettgesetzte Prosa-Absätze. Bewusst **keine** Ausnahme-Klappe (`obs-ok`-Pendant): Für die denkbaren Fälle wäre sie die Umgehung der Regel selbst, und eine auf Vorrat gebaute Klappe wird zur Formalie (OBS-S112-8). Nicht mechanisierbar und daher als Regel im Datei-Header: Ein Auslöser muss eintreten, nicht nur eintreten *können* (sonst Fallback), und eine Verletzung geltender Regeln ist immer `jetzt`. Fail-open bei Hook-eigenen Fehlern. **Wirksamkeit prüfen:** BEWÄHRT, wenn nach S114 kein TD-Eintrag mehr ohne realen Zeitpunkt entsteht und kein `jetzt`-Eintrag ohne `AGENT_MEMORY`-Punkt bleibt; Regression → zurück auf AKTIV. Bezug: OBS-S112-1, OBS-S112-2, OBS-S112-6, LL-S112-1, CM-S102-2 + CM-S107-1 (Muster-Vorbilder).

### CM-S107-1 – Lösungskandidat bei OBS-Erfassung ankert den Drain-Agenten
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Skill-Nutzung | **Status:** AKTIV | **Seit:** S107
**Problem:** Bei der OBS-Erfassung (closing-session / mid-session) wird wiederholt eine Lösungs-/Kandidaten-Richtung ins Feld `- Entscheidung/Maßnahme:` geschrieben, obwohl es bis zum Drain „offen" bleiben soll → ankert den bewusst frischen Drain-Agenten (Anchoring-Bias) und untergräbt dessen Debiasing-Zweck. 2× in dieser Periode (LL-S102-1, LL-S106-1), beide flaggen Poka-Yoke; Bestandsdrift auch in OBS-S103-1/-S105-2. Instanz von CM-S047-1 – die Regel steht im `observations.md`-Header + `closing-session` Schritt 2, wird aber wiederholt verletzt → Lese-Disziplin reicht nicht.
**Maßnahme:** Syntaktischer PreToolUse-Poka-Yoke `.claude/hooks/check-obs-capture.py` (via TDD, analog CM-S102-2 `check-ref-direction.py`): bei Edit/Write an `docs/kaizen/observations.md` darf das `- Entscheidung/Maßnahme:`-Feld eines **neu** hinzugefügten OBS nur den Kanon-Wert tragen; ein bei Erfassung befüllter Kandidat blockt (exit 2). **Gebaut** (`tests/test_obs_capture.py`, in `settings.json` unter `Edit|Write` registriert): geprüft werden nur OBS-IDs, die im Post-Inhalt neu gegenüber dem Pre-Inhalt sind – Bestands-Einträge bleiben frei änderbar, genau das tut der Drain beim Entscheiden. **Zulässig ist genau eine von zwei Whitelist-Zeichenketten** (`offen` bzw. `offen - beim Drain Kandidaten erstellen und bewerten`), nichts davor und nichts dahinter: freie Prosa hinter dem Token wäre der Schlupfweg, über den der Kandidat trotzdem im Feld landet („offen – Richtung: …“) – genauso wie eine offene *Frage*, die dort ebenfalls nichts zu suchen hat. Rein typografische Abweichungen (Gedankenstrich-Variante, Groß-/Kleinschreibung, Mehrfach-Leerzeichen) werden wegnormalisiert, fehlendes Feld blockt ebenfalls. **Gegen den Wasserbett-Effekt** (Kandidat weicht in ein anderes Feld aus) prüft der Hook zwei weitere Dinge am neuen Eintrag: (2) **Feldnamen-Whitelist** – nur `Quelle/Status/Impact/Kategorie/Beobachtung/Entscheidung-Maßnahme/Bezug`, `Bezug` optional, der Rest Pflicht; ein erfundenes `- Lösungsidee:`/`- Kandidaten:`-Feld blockt (Nebeneffekt: hält das Format parse-stabil für `obs_parse.py`). Eingerückte Sub-Bullets gelten als Prosa, nicht als Feld. (3) **Explizite Lösungs-Ansagen** im Eintrags-Text (`Lösungsvorschlag/-richtung/-idee/-ansatz/-kandidat`, `Kandidat:`, `Vorschlag:`, `Idee:`, `Abhilfe:`, `Fix:`) blocken. **Bewusst NICHT reglementiert:** modale Wendungen (`sollte`/`müsste`/`könnte`) – am 66-Einträge-Korpus (Backlog + Archiv) gemessen ~50 % Fehlalarm, weil sie meist ein **Risiko** beschreiben statt eine Abhilfe; ebenso wenig lösungsförmige Titel (4/66, zu unscharf). Messung derselben Regeln am Bestand: 0 Fehlalarme im Erfassungs-Kontext, 2 echte Leckagen (`Idee:` im Beobachtungs-Feld). **Grenze:** ein als reine Prosa formulierter Kandidat („X müsste Y abbilden") passiert – Marker fangen die Ansage, nicht die Absicht. Ausnahme für den ganzen Eintrag via `obs-ok`-Marker (bewusste Einzelfälle, z.B. ein umnummerierter Bestands-Eintrag). Fail-open bei Hook-eigenen Fehlern. **Wirksamkeit prüfen:** nach Bau kein neuer OBS mit vorab notiertem Kandidaten (BEWÄHRT über mehrere Erfassungen ohne Rückfall; Regression → AKTIV). Bezug: LL-S102-1, LL-S106-1, CM-S047-1, CM-S102-2 (Muster-Vorbild).

### CM-S107-2 – Schritt-0-Architektur-Check: aktiver ADR-/TD-Scan statt Verlass auf Erinnerung
**Impact:** MITTEL | **Kategorie:** PROZESS | **Kontext:** Skill-Nutzung | **Status:** AKTIV | **Seit:** S107
**Problem:** Der Architektur-Check (implementing-scenario Schritt 0) fand fällige Kontexte nicht, weil er sich auf AGENT_MEMORY/Erinnerung stützte: einschlägige ADRs nicht konsultiert (LL-S091-2 – Fehlertyp in 3 Iterationen statt des vorhandenen Sum-Type-ADR) und fällige technische Schuld nicht gescannt (LL-S098-3 – TD-S083-5 erst reaktiv beim E2E-Fehlschlag gefunden).
**Maßnahme:** Bereits mechanisiert; in der S107-Retro nur als CM nachdokumentiert. `implementing-scenario` Schritt 0 **Punkt 4** (ADR-Sichtung via `decisions.py list --tag story:us-NNN --full` + `scope:cross-cutting`, Ergebnisse in die Subagenten-Message) und **Punkt 5** (TD-Sichtung: für **jeden** die berührten Bereiche betreffenden `tech-debt.md`-Eintrag vor der Umsetzung mit-erledigen/aufschieben + **schriftlich begründen**). Gebaut S099 (Commit `ac6c46b`, direkte Reaktion auf LL-S098-3) → **kein Rückfall**. **Grenze bewusst:** fängt nur area-berührte TD; Waisen-/Infra-TD ohne Lauf-Bezug bleibt offen (OBS-S099-1). **Wirksamkeit prüfen:** künftige Läufe – kein reaktiv-entdecktes fälliges TD/ADR, das Schritt 0 hätte fangen müssen (BEWÄHRT nach mehreren Läufen ohne Rückfall). Bezug: LL-S091-2, LL-S098-3, OBS-S090-5, OBS-S099-1.

### CM-S105-1 – Postgres-Init-Config aus einer Single Source (Test == Prod by construction)
**Impact:** HOCH | **Kategorie:** PROZESS | **Kontext:** Testing, C#-Code | **Status:** AKTIV | **Seit:** S105
**Problem:** Testcontainer (`en_US.utf8`) und `docker-compose` (`--locale=C`) hatten getrennte Config-Quellen → das Locale divergierte → grüne Suite, aber das Deployment hätte die Umlaut-Eindeutigkeit still gebrochen (LL-S105-1).
**Maßnahme:** `config/postgres.env` ist die einzige Quelle der Postgres-Init-Config; `docker-compose.yml` lädt sie via `env_file:`, die `PostgresContainerFixture` liest dieselbe Datei (`PostgresTestConfig`) und setzt `WithEnvironment(...)`. Locale/Encoding können damit nicht mehr zwischen Test und Deployment auseinanderlaufen. Backstop: die config-sensitiven Öl-Duplikat-Tests (Server.Tests-InlineData + E2E) fallen, falls eine Seite doch aufhört, Umlaute zu falten. `.env` ist gitignored (für spätere Secrets reserviert).

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
**Maßnahme:** Spawn-Regel in `implementing-scenario` SKILL.md (innerer Loop, „Arbeitende Subagenten nicht pollen"): auf den inhaltlichen Return warten (Test-Review-Signal / Verifikations-Hash / Return), Idle-/„available"-Zwischensignale nicht mit Status-Nachfragen beantworten; `SendMessage` bleibt für PLANUNG-Rückfragen und Findings-Übergabe. **Verfeinerung (S102, run-3):** idle/„available" = Zwischensignal (ignorieren); ein **Abschluss/„finished"** ist dagegen das Signal, den Endbericht zu haben – kommt der inhaltliche Report bei einem als finished gemeldeten Subagenten *nicht* ohnehin als Return an, ihn aktiv per `SendMessage` anfordern statt passiv weiterzuwarten. **Verifizierte Ursache (Log-Nachschau):** In run-3 gab ein Review-Auditor (security) seinen Findings-Report als **plain-text-Output** aus statt per `SendMessage` – und Text-Output eines Team-Subagenten ist für den Orchestrator **nicht sichtbar** (SendMessage-Doku); der Report lag im Subagent-Log, kam aber nie an, bis der Orchestrator ihn nach User-Hinweis aktiv anforderte. Kein Zustellungs-Bug, sondern falscher Ausgabekanal des Subagenten (Root-Cause separat als OBS-S102-3 erfasst). Diese Regel hier ist der **Orchestrator-Fallback** dagegen; der eigentliche Fix liegt beim Subagenten. **Wirksamkeit prüfen:** nächster realer `implementing-scenario`-Lauf – kein Status-Poll eines arbeitenden Subagenten, aber auch kein übersehener finished-Report (BEWÄHRT, wenn über 1–2 Läufe kein Rückfall in beide Richtungen; Regression → zurück auf AKTIV). Robust gegen beide Ursachen (mehrdeutiges Signal *oder* Orchestrator-Missverständnis). Bezug: OBS-S101-2.

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
**Maßnahme:** `write-code` Skill: Pflicht-Schritt "Guidelines lesen" + explizite Per-Member-YAGNI-Frage: „Welcher aktuell rote Test fordert genau das?" **S107:** Weitere Instanzen LL-S102-1/-S103-1/-S106-1 (Regel bekannt, im selben Schritt nicht angewandt). Gezielte Mechanisierungen einzelner Hotspots: CM-S107-1 (OBS-Erfassung), CM-S107-2 (Schritt-0-Scan). Bleibt AKTIV.

### CM-S064-1 – Tool-Verhalten als gesichertes Wissen präsentiert
**Impact:** HOCH | **Kategorie:** AGENT | **Kontext:** Kommunikation | **Status:** AKTIV | **Seit:** S064
**Problem:** Behauptungen über externes Tool-Verhalten als gesichertes Wissen präsentiert (S061, S063)
**Maßnahme:** Regel in `principles.md` dokumentiert ✓. Selbst-Check vor jeder Tool-Verhaltensbehauptung: „Basiert das auf einem Tool-Call dieser Session?" Falls nein: explizit als unverified kennzeichnen und Verifizierung anbieten. **S085 verbreitert (Rückfall S078/S081/S084):** gilt für jedes Handeln auf angenommenem Verhalten (Empfehlung/Fertig-Erklärung/dokumentierter Befehl), nicht nur Behauptungen – Regel in principles.md verbreitert. **S095 Rückfall:** LL-S086-1 (Kandidaten-Gefahr ohne Verifikation behauptet) + LL-S093-1 (auf „in Datei X definiert"-Doku-Behauptung verlassen, Helper existierte nicht). Bleibt AKTIV – als Urteils-Verhalten schwer poka-yoke-bar. **S107:** Zwei weitere Instanzen (LL-S096-1 Reviewer-/eigene Behauptung ungeprüft weitergereicht; LL-S099-1 Rename-Scope auf unverifizierter Struktur-Annahme) – bestätigt „schwer poka-yoke-bar", bleibt AKTIV. **S114 Rückfall (drei Instanzen in einer Session), mit zwei bisher unbenannten Tarnungen:** (a) **Arithmetik auf zitierten Zahlen** (LL-S114-1) – eine Rechnung auf fremden Angaben fühlt sich wie Verifikation an, weil man selbst etwas getan hat; der Selbst-Check „basiert das auf einem Tool-Call dieser Session?" greift nicht, weil das *Rechnen* einer war. (b) **Vorschrift als Beschreibung der Praxis gelesen** (LL-S114-2) – der Check zielt auf externes Tool-Verhalten, hier kam die Annahme aus einem projekteigenen Dokument, das die Realität bloß vorschreibt. (c) Zusätzlich LL-S114-3: eigenes abgeleitetes Ergebnis ungeprüft berichtet. Alle drei fielen erst durch Rückfragen des Users auf. Beide Tarnungen in `principles.md` ergänzt; bleibt AKTIV.

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
**Maßnahme:** (1) Orchestrator-Vorabanalyse vor E2E-Test auf Spec-Ambiguitäten; (2) Subagent bittet nach RED um Test-Review, Orchestrator friert die freigegebenen Tests als immutable git-Blob-Anker ein (`git hash-object -w`); (3) Per-Assertion-Zuordnung, Full-State-Assertion-Check, Check auf Anpassungen an bestehenden Tests; (4) mechanischer Test-Freigabe-Audit in `qa-check --verify --approved-tests` – zeigt jede Test-Änderung seit Freigabe als Diff (Setup erlaubt, Assertions verboten), immun gegen Subagent-Stagen. Details: `implementing-scenario` SKILL.md **S095:** 3 saubere Full-Stack-Läufe (S83/S90/S91, kein Gold-Plating-Rückfall) – BEWÄHRT-reif, aber wegen KRITISCH-Impact + teils prozeduralem Mechanismus bewusst noch 1 Periode beobachten, dann BEWÄHRT. **S099:** Mechanismus gehärtet – der frühere „Staged-Test-Check" (prozedural, durch Subagent-`git add` umgehbar → OBS-S090-4) durch den Blob-Anker-Audit ersetzt; das schließt das Umgehungs-Loch mechanisch. **S107 (bleibt AKTIV, NICHT hochgestuft):** Der Blob-Anker-Audit war für **Backend** bis S104 faktisch wirkungslos – `qa-check._LAYER_PATHS["backend"]` band den Backend-Testcode nicht (OBS-S102-2, gefixt S104) → das Gate deckte Backend erst ab S104. Valide gate-gedeckte Läufe der Periode: Frontend S100/S101/S103 (3×), Backend nur S105/S106 (2×). Kein Gold-Plating-Rückfall, aber der Backend-Pfad hat noch keine 3 sauberen gate-aktiven Läufe → BEWÄHRT wäre voreilig (LL-S095-2: keine Hochstufung auf nicht-isolierender Evidenz), zumal KRITISCH. BEWÄHRT, sobald Backend ≥3 gate-aktive Läufe ohne Rückfall hat.

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
**Maßnahme:** Prinzip „Vollständige Zerlegung vor Schluss/Empfehlung" in `principles.md` dokumentiert ✓ (Abschnitt „Kommunikation & Argumentation"): Dimensionen/Pfade/Quantoren explizit aufzählen und je prüfen, bevor der Schluss steht. **S107:** LL-S107-2 – CM-BEWÄHRT-Evidenz („6 saubere Läufe") vorgelegt, ohne zu zerlegen, ob das steuernde Gate die ganze Periode aktiv war (Backend-Gate erst ab S104). Bleibt AKTIV.

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
