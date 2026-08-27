# Session 125 – 2026-08-27/28

**Phase:** SKELETON
**Schwerpunkt:** OBS-Drain – gezielter Doku-Zugriff (`doc.py`) gebaut, vier Einträge behandelt.
Dabei entschieden, dass die Session-Historie in die Commit-Nachricht zieht: **Dies ist die
letzte Datei dieser Art.**

## Umgesetzt: gezielter Abschnittsabruf (OBS-S114-2)

Ausgangslage, neu gemessen: `docs/guidelines` und `docs/process` machen zusammen **20,4 %** des
Read-Volumens aus (61 Sessions), bei Ø ~11.900 Zeichen je Read und nur **6 % gezielten**
Zugriffen. Gegenbeleg im selben Datensatz: `docs/history` liegt bei **72 % gezielt** – dort gab
es mit `decisions.py` schon einen Abrufweg. Der Median eines Abschnitts liegt bei 952 Zeichen.

**`doc.py`** (neu, mit `test_doc.py`): `get <ANKER>` liefert einen Abschnitt, `toc <datei>` die
Abschnittsliste mit Anker und Größe, `audit` sichtet den Bestand. Der Anker-Index kommt aus
`anchors.py` (Import, keine Kopie); eigenes Script, weil die Zielgruppe eine andere ist –
Retrieval für arbeitende Subagenten statt Integritätsprüfung für Autor und Hook.

**Scope-Regel** (User-Entscheid): Überschriften-Anker reichen bis zur nächsten gleichrangigen
oder höherrangigen Überschrift, Unterabschnitte gehören dazu; Absatz-Anker liefern nur ihren
zusammenhängenden Block. Die Alternativen (bis zur nächsten Überschrift beliebiger Ebene / bis
zum nächsten Anker) sparen im Median nur ~200 Zeichen und erkaufen das durch stilles
Abschneiden. Die Block-Regel wurde an allen 35 Absatz-Ankern des Bestands validiert.

**Doku-Umbau:** 7 Stellen, an denen fette Absatz-Leads faktisch als Abschnitte dienten, wurden
zu echten Überschriften (`coding-guideline-csharp.md`, `review-workflow`, `gherkin-workshop`,
`implementing-scenario`). Bestand danach: 344 Anker gesichtet, 0 mit zurückgelassenem Text.

**Absicherung:** `doc.py audit` als Pflichtschritt in `review-docs`; Prinzip „Ein Anker ist eine
Abrufeinheit" in `principles.md`; Navigationszeile in `CLAUDE.md`.

**Wirksamkeit:** Die Implementer-Agenten nennen `doc.py` konkret (zwei Zeilen, Verweis auf
`--help` statt Erklärungskopie); die Skills bleiben projektneutral und verweisen nur auf die
`CLAUDE.md`-Navigation – ein Skill soll portabel bleiben (User-Entscheid). Neue Sektion
„Gezielt lesen statt Volldatei" in der SessionStart-Injektion (`check-bash-permission.py --list`),
die auch `decisions.py` und `test-inventory.py` erstmals sichtbar macht. **Bewusst nicht
umgestellt:** die Review-Auditoren – sie haben kein Bash, und gezieltes Abrufen setzt voraus,
dass man weiß, wonach man sucht; ein Reviewer weiß das per Definition nicht (begründet in
`review-code`). Die Wirkung selbst ist unbewiesen: OBS-S114-2 steht auf Wiedervorlage mit dem
Kriterium, erst nach mindestens drei Implementierungs-Sessions nachzumessen.

**Nebenbefund, behoben:** `workflow-auditor.md` trug einen toten Auftrag – der Agent sollte
`decisions.py` ausführen, hat aber kein Bash.

## Entschieden: die Session-Historie zieht in den Commit (OBS-S121-3)

Messungen: 106 von 121 Session-Dateien wurden nie per `Read` geöffnet (87 %). Alle 16
Lesezugriffe wurden einzeln nachgesehen und in vier Zwecke zerlegt – Herleitung (~6), Übergabe
zwischen Sessions (2), Detail-Erinnerung (~4, einer davon nachweislich erfolglos), Meta ohne
Inhaltsnutzen (~4). 69 % aller Lesezugriffe waren reines Format-Abschauen. Der Index wurde
98-mal gelesen, aber ausschließlich als Meta-Quelle (Nummer, Zeilenformat, Lückencheck) – kein
inhaltlicher Zugriff belegt.

Entscheidend war der Hinweis des Users, dass die **Commit-Nachricht** dieselbe Aufgabe bereits
erfüllt: Ihr Body trägt Problem, Entscheidung, Werkzeuge und Tracker-IDs – mehr als die
Session-Datei –, und es ist praktisch ein Commit je Session. Zwei Fassungen wären eine Kopie.
Der Einwand, die Commit-Konvention sei nicht erzwungen, fiel: Für die Datei-Konvention gilt
dasselbe (kein Hook, nur ein Schritt in `closing-session`), belegt durch die Lücke bei
`session_104`.

Die vollständige Ablage-Aufteilung, die Folgearbeiten (u.a. `current_session()` von den Dateien
auf `git log` umstellen – daran hängt jede Tracker-ID) und die drei umzuziehenden Verweise
stehen im Eintrag. Status: Wiedervorlage S126, dort als erster Punkt des Drains.

## Behandelte Einträge

- **OBS-S114-1** – `VERWORFEN`. Recherche zu Markdown-/Git-basierten Memory-Systemen geführt;
  kein Fit, u.a. weil `mdq` Abschnitte über generierte Positions-IDs adressiert – genau die
  Ordinale, die S124 abgeschafft hat. Kein CM (User-Entscheid).
- **OBS-S114-2** – `IN BEOBACHTUNG bis S130`, siehe oben.
- **OBS-S124-1** – `VERWORFEN`. Kein Defekt: Dass Prioritäten hinter dem Drain warten, ist die
  designte Rangfolge, und `Fällig: jetzt` steuert die Vorlage, statt Überfälligkeit zu
  behaupten. Inline-Maßnahme: Stub-Wortlaut des `priorities`-Moduls und die Doppeldefinition
  von `jetzt` im `AGENT_MEMORY`-Header bereinigt.
- **OBS-S121-3** – `IN BEOBACHTUNG bis S126`, siehe oben.

Backlog: 17 → 13 drainbar.

## Review

Drei Auditoren über `doc.py`, Tests und Doku-Umbau. **0 Blocker, aber vier echte Fehler** – alle
an den Nahtstellen zwischen Regeln, alle still: Ein Absatz-Anker schluckte den nächsten Anker
ohne Leerzeile; die dokumentierte Inline-Schreibweise `<a id="X"></a>## Titel` wurde beim
Vorwärts-Scan nie als Überschrift erkannt; ein eingerückter Code-Block nach einer Leerzeile
beendete den Block; und `--nur-vorspann` zusammen mit `--zeilen` meldete nur eine der zwei
Kürzungen – eine stille Kürzung in genau der Funktion, die sie verhindern soll. Dazu 12
Verbesserungen umgesetzt. Ein Finding wurde begründet zurückgewiesen (`_einrueckung` misst
korrekt roh – der Docstring war falsch, nicht der Code).

## Korrekturen am eigenen Vorgehen

Vier Rückfragen des Users deckten Fehler auf, die das Ergebnis verändert haben: eine als
„30 Session-Starts" ausgegebene Zahl waren 11 Sessions (Vorkommen statt Sessions gezählt);
„toter Mechanismus" war überzogen für ein Modul, das hinter bewusster Priorisierung
zurücksteht; ein Ausschlusskriterium wurde nur an der neuen Option geprüft, nicht am Status
quo; und bei `index.md` wurde „wird gelesen" mit „wird gebraucht" verwechselt. Details in
LL-S125-1 bis -4.

**Vorschlag für die Retro:** LL-S125-3 (Ausschlusskriterium auch am Status quo prüfen) wäre ein
Kandidat für `principles.md`. Ein Entwurf wurde geschrieben und vom User verworfen – zu lang
und zu fallbezogen für ein Dokument, das bei jedem Session-Start injiziert wird; außerdem
erzwingt ein MITTEL-Learning keine direkte Behandlung. Wenn, dann in knapper Form.

## Learnings & Beobachtungen

- **LL-S125-1** (HOCH) – Zähleinheit stillschweigend getauscht; CM-Bezug `neu`.
- **LL-S125-2** – Fertig gemeldet nach einer Gegenprobe, die nur bereits getestete Stellen traf.
- **LL-S125-3** – Ausschlusskriterium nur an der neuen Option geprüft.
- **LL-S125-4** – Backticks im Bash-Argument zerstörten einen Tracker-Eintrag.
- **OBS-S125-1** – Tracker-Einträge werden im Drain per ID genannt, ohne dass der User ihren
  Inhalt kennt.
- **OBS-S125-2** – Tracker-Scripte können Erfassungsfehler nicht korrigieren (`set` kennt kein
  `--vorprägung`, `--beobachtung` erweitert statt zu ersetzen).
- **OBS-S125-3** – Für `.claude/scripts` gibt es kein Mutation-Testing.
- **OBS-S125-4** – Review-Auditoren können ihre Findings nicht verifizieren, weil ihnen Bash fehlt.

Volltexte: `docs/kaizen/lessons_learned.md`, `docs/kaizen/observations.md`.

## Zum Schluss

121 Dateien, 486 KB, über rund neunzig Sessions geschrieben. 106 davon hat nie jemand geöffnet;
von den 15 gelesenen wurden zwei Drittel der Zugriffe nur getätigt, um die Form der nächsten
Datei abzuschauen. Der Wert lag fast immer woanders: in der ADR, im Docstring des Werkzeugs, im
OBS-Archiv – oder in der Commit-Nachricht, die daneben still dasselbe erzählte, nur besser.

Ein Format, das seinen eigenen Nutzen nicht belegen kann, verschwindet. Dass diese Reihe damit
endet, ist kein Verlust, sondern das Ergebnis genau der Messung, für die sie da war.
