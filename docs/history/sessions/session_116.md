# Session 116 – 2026-08-10

**Phase:** SKELETON | **Art:** Kaizen-Retro (Periode S107–115)

---

## Kaizen-Retro

Ausgelöst durch den Jenga-Trigger (Score ≤ 0). Periode S107–115: 9 Sessions, 22 Findings.

### Noise-Review & Kalibrierung (Schritt 0)

- **1 Noise-Eintrag gelöscht:** LL-S098-2 (Provider-spezifische API in `Program.Main`) – die Regel ist eine nachschlagbare Coding-Tatsache und steht wörtlich in `coding-guideline-csharp.md`, Filter-Frage 3 also Nein. Stand seit S098 im Archiv, vom S107-Noise-Review übersehen.
- **2 Impacts hochgestuft** (MITTEL → HOCH): LL-S113-3 (Gate-Suite ohne Gate) und LL-S110-1 (vakuöse Hauptassertion) – beide sind False-Green-Fälle. LL-S111-3 und LL-S113-2 blieben nach Diskussion bei MITTEL.
- **3 Phantom-Kontext-Tags korrigiert:** `[Subagenten]` → `[Agent-Prompt]` (LL-S108-1), 2× `[Kaizen]` → `[Skill-Nutzung]` (LL-S102-1, LL-S099-1, beide im Archiv). Tags außerhalb der `process.md`-Liste können mit nichts clustern und fallen aus der Musteranalyse.
- **1 falsche Ursachendiagnose korrigiert:** LL-S111-2 führte das Liegenbleiben von TD-S108-4 auf den TD-Abgleich in Schritt 6 zurück; tatsächlich deckt Schritt 0 Punkt 5 den Fall ab und wurde nicht ausgeführt → Rückfall, keine Abdeckungslücke.

### Maßnahmen

- **CM-S116-1 neu** + Prinzip „Die Gegenprobe" in `principles.md`: Das dominante Muster der Periode (8 Instanzen), von der Tripel-Clusterung in zwei getrennte Kandidaten zerrissen. Details: `docs/kaizen/countermeasures.md`.
- **CM-S078-2 reaktiviert** (VERWORFEN → OFFEN): 8 HOCH-Findings bei 2 neuen CMs; der in der Verwerf-Begründung von S095 benannte Fall ist eingetreten. Ausgestaltung bewusst in den Drain (OBS-S116-5), nicht in AGENT_MEMORY.
- **2× BEWÄHRT:** CM-S102-2 (Ref-Direction-Hook – 3 `ref-ok`-Marker im Gesamtbestand, alle begründet; feuerte in dieser Session real) und CM-S107-1 (OBS-Erfassungs-Hook – live seit 2026-07-23, >15 Erfassungen ohne Rückfall).
- **6 CMs mit Rückfall-/Erweiterungs-Nachträgen:** CM-S047-1, CM-S056-1, CM-S064-1, CM-S086-1, CM-S095-2, CM-S102-3, CM-S107-2. CM-S070-1 blieb trotz erfülltem Lauf-Kriterium AKTIV (Review-Fix-Pfad ungedeckt).
- **CM-S083-3 entschieden:** kein Soft-Cap für AGENT_MEMORY. Die Ansammlung ist mechanisch erzwungen – 3 TD-Einträge mit `Fällig: jetzt`, die `check-td-capture.py` an einen AGENT_MEMORY-Eintrag koppelt. Der reale Defekt ist der Detailgrad → OBS-S116-2.

### Belege aus harten Datenquellen

Erstmals wurde für CM-S056-1 die primäre Datenquelle ausgewertet statt auf Selbstbericht vertraut (`process.md`, BEWÄHRT-Kriterium): 94 echte Denies in 9 Sessions. Die direkten `npx vitest`/`npm run lint`-Aufrufe stammen laut Subagent-Logs praktisch immer vom Frontend-Schicht-Subagenten (5 in dieser Periode, Muster zurück bis S90) – kein einziges lessons_learned berichtete davon. Ursache lag in den Agenten-Definitionen, nicht im Hook.

## Änderungen an Skills, Agenten und Prozess

- `backend-layer-implementer` / `frontend-layer-implementer`: Test-Wrapper (`dotnet-test.py`, `vitest-run.py`) am RED-Schritt verankert; die `npm --prefix`-Form korrigiert (die bisherige Angabe lief aus dem Repo-Root nicht).
- `implementing-scenario`: Szenario-Frage vor jedem Fix-Auftrag im Review-Loop; dritte Signal-Klasse „gar kein Signal" beim Warten auf Subagenten.
- `process.md` Regel 1 differenziert nach definiert/undefiniert (AGENT_MEMORY vs. Drain) – die Regel stammte aus der Zeit vor dem kontinuierlichen Drain und kannte nur einen Ablageort; zwei tote Schritt-Verweise in derselben Sektion korrigiert.
- `kaizen`-Skill: Archivierungs-Schritt nutzt kleinste/größte Session-Nummer statt erstem/letztem Header (die Datei ist in Erfassungs-, nicht Session-Reihenfolge sortiert); Schritt 6 folgt der neuen Regel-1-Weiche.

## Bugfix

`jenga_score.py` zählte den Beispiel-Eintrag aus dem HTML-Kommentar des Datei-Headers als echtes Finding → jede Periode startete bei 90 statt 100. Behoben via TDD (Kommentare vor dem Parsen strippen), Gegenprobe an der archivierten Periode: 22 geparst = 22 per `grep`. 495 Tooling-Tests grün.

## Learnings & Beobachtungen

- LL-S115-2 (in der archivierten Periode): Erledigtes bleibt in Zustandsdokumenten stehen, weil nur die präventive Regelhälfte einen Auslöser hat.
- LL-S116-1: Tests prüften den Regex-Baustein, nie die Funktion, die ihn anwendet.
- LL-S116-2: Aus der gerenderten Session-Start-Injektion auf den Dateiinhalt geschlossen.
- OBS-S116-1 bis -5 neu erfasst (Backlog 16 → 21, überfüllt); OBS-S111-4 um vier Denies aus dieser Session erweitert.

Volltext: `docs/kaizen/lessons_learned.md`, `docs/kaizen/archive/session_107_to_115.md`, `python3 .claude/scripts/obs.py get <ID>`.
