# Observations – Archiv

<!--
Zweck: Aufgelöste Beobachtungen aus docs/kaizen/observations.md. Beim Backlog-Grooming in der Retro
       werden Einträge mit Status UMGESETZT oder VERWORFEN hierher VERSCHOBEN (nicht kopiert), damit
       die Live-observations.md scannbar bleibt.

Format der Einträge: identisch zu observations.md (Eintrag-Format dort im Header / docs/kaizen/process.md).

Speist Jenga NICHT (kein Script liest diese Datei).
-->

> **Quelle:** `docs/kaizen/observations.md`
> **Format-Referenz:** `docs/kaizen/process.md`

---

## OBS-S085-5 – Doku-Links per Anchor statt Sektions-Position
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Doku
- Beobachtung: Links in der Doku verweisen auf Positionen („Sektion 6"), die stale werden; Agenten suchen ineffizient.
- Entscheidung/Maßnahme: Aufgegangen im Prinzip „Single Source of Truth" (grep-barer Anchor / Heading-Text / ID statt „Sektion N"-/Zeilen-Position). → CM (S086, AKTIV).
- Bezug: OBS-S085-15

## OBS-S085-6 – lessons_learned-Format wird in closing-session wiederholt eingelesen
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Das Format wurde regelmäßig per Datei-Einlesen geprüft → Zeit/Token-Verschwendung.
- Entscheidung/Maßnahme: Präzise Ursache (S086): die LL-Datei muss zum Edit ohnehin gelesen werden – die echte Verschwendung war ein *separater* `process.md`-Read für das Format (closing-session Schritt 5 zeigte dorthin). Fix: Format kanonisch im `lessons_learned.md`-Header (+ Mini-Beispiel); `process.md` §Eintrag-Format, closing-session Schritt 5 und das Template referenzieren nur noch den Header (Single Source gegen Drift).
- Bezug: OBS-S085-15

## OBS-S085-9 – index.md-Einträge werden zu lang
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Einträge in `docs/history/sessions/index.md` wurden über die Sessions hinweg immer länger.
- Entscheidung/Maßnahme: Drift per Plot als **Verbosity-Ratchet** belegt (nicht Scope-Wachstum – frühe Sessions leisteten mehr in weniger Zeichen). **A+B:** Soft-Ziel 150 / harter Cap 300 Zeichen (Kurzfassung = ein Satz, *was* sich änderte, kein „warum"); `check-index-length.py` als CLI-Report **und** PreToolUse-Hook (grandfathered: nur neueste/geänderte Zeilen), geteilte Logik in `_index_length.py`; closing-session Schritt 6 gehärtet; S76–S85 gekürzt. Live verifiziert.

## OBS-S085-11 – ID-Retrofit für bestehende lessons_learned-Einträge (deferred Meta-Änderung)
- Quelle: Agent
- Status: UMGESETZT (S085)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Neue LL-Einträge bekommen IDs; ~99 Bestands-Findings haben keine. Nutzen spekulativ.
- Entscheidung/Maßnahme: **A — kein Retrofit**; IDs nur für neue Einträge (gängige Praxis). Entschieden S085.
- Bezug: OBS-S085-10

## OBS-S085-13 – Retro-/Findings-Präsentation pro Punkt strukturieren
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Kommunikation
- Beobachtung: Bei vielen Findings war schwer erkennbar, was Problem/Warum-jetzt/Vorschlag/Alternativen ist; leere Findings-Abschnitte wurden still weggelassen.
- Entscheidung/Maßnahme: **A+B** in `kaizen` SKILL Schritt 5: pro Finding vier Facetten explizit (Problem / Warum jetzt / Vorschlag / Alternativen, auch als Tabellen-Spalten in A); leere Abschnitte nicht still weglassen, sondern kurz nennen (was + warum leer).

## OBS-S085-15 – Referenzieren statt duplizieren; greppbare Anchors/IDs statt Zeilennummern
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Infos teils über mehrere Dateien dupliziert (Drift-Gefahr); Verweise per Position statt grep-barem Marker.
- Entscheidung/Maßnahme: **A** — Prinzip „Single Source of Truth: Information am passendsten Ort, sonst referenzieren" in `principles.md` (Abschnitt „Doku & Referenzen": kontextfrei am passendsten Ort; sonst referenzieren mit grep-barem Anchor; Zeilennummern nur für read-only-Dateien; referenzierte Stelle geändert → referenzierende mitpflegen) + Spiegel-CM (S086, AKTIV).
- Bezug: OBS-S085-5, OBS-S085-6, OBS-S085-9, OBS-S085-16
