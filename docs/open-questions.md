# Offene Fragen / geparkte Diskussionen

<!--
wann-lesen: Wird vom Drain-Vorschlag am Session-Start vorgelegt, sobald ein `Fällig`-Termin
            erreicht oder ein Eintrag überaltert ist (`obs-drain.py`, Sektion „Offene
            Fragen"). Zusätzlich weiterhin, wenn eines der Themen aufkommt bzw. bevor
            verwandte Arbeit beginnt (z.B. Taxonomie-Frage vor der nächsten ADR-/
            Suppression-Entscheidung; getypte IDs vor ID-naher Domain-Arbeit / US-602).
wann-schreiben: Wenn eine Architektur-/Produkt-Diskussion mit dem User ohne Auflösung
            geparkt wird. Bei Klärung: Eintrag entfernen (Ergebnis ggf. als ADR/Tech-Schuld).
aufnahmebedingung: Hier steht eine **noch nicht entschiedene** Frage am Produkt (Code +
            Build-/Test-Kette), deren Antwort mit dem User zu klären ist. Mit der Entscheidung
            verlässt der Eintrag diese Datei: bleibt nach Erledigung etwas zu erklären übrig →
            `docs/history/adr.md`, sonst → `docs/tech-debt.md`.
            NICHT hierher gehört: (a) alles bereits **Entschiedene** – auch wenn die Umsetzung
            noch aussteht (das ist `docs/tech-debt.md`, nicht „offen"); (b) alles **Prozess**-
            seitige, also wie gearbeitet wird (`.claude/**`, `docs/process/`, `docs/kaizen/`) –
            das läuft über `docs/kaizen/observations.md`; (c) eine Aufgabe, der nur die
            Priorisierung fehlt (das ist `docs/AGENT_MEMORY.md`).
            Abgrenzung ADR/TD/OQ kanonisch: `CLAUDE.md`, Sektion „Ablage: ADR, TD oder
            offene Frage?"

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen.

Eintrag-Format:
  ## OQ-S<NNN>-<n> — <Kurztitel>
  **Frage:** <die offene, mit dem User zu klärende Frage>
  **Fällig:** <Anker>[, <Anker>…] – <Prosa>   (optional – wann vorlegen?)
  **Hintergrund:** <Auslöser / Kontext / betroffene Artefakte>

  ID: OQ-S<NNN>-<n> – 3-stellige Session (geparkt), laufende Nummer innerhalb der Session.

  `Fällig` ist **optional** und steuert die Vorlage. Es nutzt dieselbe Anker-Grammatik wie
  `docs/tech-debt.md` – kanonisch in `.claude/scripts/td_anchors.py`, von `open_questions.py`
  wiederverwendet (nicht kopiert). Der Kopf vor dem Gedankenstrich ist maschinenlesbar:

      jetzt              sofort vorlegen
      Phase:V1           Phasenwechsel (auch MVP/V2)
      S140               Spätestens-Termin (Session-Nummer)
      Szenario:„…"       ein Gherkin-Szenario aus features/ (Titel exakt)
      US-602             eine Story – nur solange sie noch keine Szenarien hat
      TD-S089-1          ein Tech-Debt-Eintrag – tritt ein, wenn jener behoben ist

  Mehrere Anker mit Komma. Alles Erklärende gehört **hinter** den Gedankenstrich.

  Ist ein Anker gesetzt, erscheint die Frage genau dann (und vorher nicht – ein Anker
  unterdrückt die Alters-Regel, sonst wäre er wirkungslos). **Ohne** das Feld gilt eine Frage
  nach ~10 Sessions als überaltert und wird vorgelegt.

  Mechanisch geprüft an beiden Enden: `.claude/hooks/check-oq-capture.py` blockt zur
  Schreibzeit ein gesetztes Feld, das nicht trägt (Vertipper, kein terminierter Anker);
  `open_questions.py` meldet zur Lesezeit einen dennoch unauswertbaren Anker, statt ihn zu
  verschlucken. Vorher fiel beides still auf die Alters-Regel zurück und blieb unbemerkt.

  Anders als bei Tech-Debt erzeugt `jetzt` hier einen Vorlage-Grund: TD-Einträge mit `jetzt`
  stehen zusätzlich in `AGENT_MEMORY.md` und kämen sonst doppelt, offene Fragen haben diesen
  zweiten Kanal nicht.
-->

## OQ-S094-1 — Client-seitige Validierung (Instant-Feedback) einführen?
**Frage:** Lohnt eine client-seitige Validierung (Instant-Feedback *vor* dem Speichern) – und wenn ja, drift-frei wie?
**Fällig:** Phase:V1, S140 – der tragende Trigger ist das Ereignis (siehe „Trigger zum Wiederaufgreifen" unten), nicht das Alter; `Phase:V1` drückt ihn aus, `S140` bleibt als Backstop stehen, falls die Phase sich verschiebt.
**Hintergrund:** Diese Abwägung kam schon mehrfach auf. Die maßgebliche, _front-loaded_ Argumentkette steht stabil in **ADR-S090-1** (Abschnitt „Validierung bleibt server-only / Client-Validierung aufgeschoben", Punkte 1–4) – bitte zuerst dort lesen, damit die Argumente nicht erneut von vorn aufgerollt werden. Kurzfassung: nur **Required** lohnt; Drift ist via backend-getriebener Metadaten lösbar (aber YAGNI); Fokus-aufs-Fehlerfeld bleibt ohnehin custom. **Aktueller Stand:** aufgeschoben aus YAGNI. **Trigger zum Wiederaufgreifen:** ein UX-Szenario fordert explizit Instant-Feedback, oder mehrere große Formulare entstehen parallel (Konsistenzdruck).

---

## OQ-S094-2 — Mobile-Ansicht: welche Szenarien, ab wann?
**Frage:** Welche Mobile-spezifischen Szenarien braucht die App, und ab welcher Phase?
**Hintergrund:** Mobile-First ist NFR (`ux-ui-auditor`, MUI v7), aber `features/` enthält bisher **keine** Mobile-Szenarien. Laut Stories MVP/V1-Scope. Der responsive Reorder-Schutz für Formulare („Felder nicht per CSS umsortieren", weil das die Autofokus-/Fokus-Reihenfolge bricht) ist bereits in UX-Guideline Prinzip 8 verankert. Systematisch beim MVP/V1 angehen – nicht vergessen.

---

## OQ-S119-3 — Native C#-Union-Types statt `SumType.cs`, sobald .NET 11 verfügbar ist?
**Frage:** Werden die handgerollten Sum-Types (`Server/Types/SumType.cs`, ADR-S040-1) auf native `union`-Typen umgestellt, sobald das Projekt auf .NET 11 / C# 15 steht?
**Fällig:** S130 – reiner Backstop. Der tragende Trigger ist der **Wechsel auf .NET 11**; ein Anker dafür existiert im Vokabular nicht (weder Phase noch Szenario treffen es).

**Hintergrund:** Recherchiert in S119. C# 15 führt `union` als nominale Deklaration ein (`public union Pet(Cat, Dog, Bird);`) mit compiler-erzwungener Exhaustivität in `switch`, dazu den `closed`-Modifier für geschlossene Hierarchien. Verfügbar ab .NET 11 Preview 2, GA für November 2026 angekündigt.

**Warum relevant:** `IngredientId` ist als Union `Known`/`Unknown` über `SumType.cs` gebaut (S120, Herleitung in `session_118.md` E3); nativ entfielen die `SumType.Unreachable<T>()`-Arme samt Stryker-Suppression (ADR-S018-2) – genau das Bedenken, das in E3 diskutiert wurde.

**Zwei Haken, die 2026 gegen ein Warten auf .NET 11 sprachen** – sie sind weiterhin die Prüfpunkte, an denen die Umstellung zu messen ist:
1. Unions sind Structs mit einem `object? Value` – **Value Types boxen bei jeder Zuweisung.** Die Domänentypen des Projekts sind `readonly record struct` ausdrücklich, um Heap-Allokation zu vermeiden (`coding-guideline-csharp.md` §1-Tabelle).
2. Das Projekt steht auf `net10.0`; `LangVersion=latest` liefert auf dem .NET-10-SDK C# 14, nicht 15. In Preview 5 fehlen laut Doku noch Teile der Spec (`ClosedAttribute` shippt die Runtime noch nicht).

---

## OQ-S119-4 — Gilt „Regeln in den Typ, Meldungen an die Grenze" auch im Frontend?
**Frage:** Wird der Frontend-Fehlertyp `ValidationError = { readonly message: string }` auf Fehler**fälle** statt Meldungstexte umgestellt – oder gilt die Regel bewusst nur backend-seitig?
**Fällig:** jetzt – der tragende Trigger, die Entscheidung über das **Backend**-Fehlermodell, ist mit **ADR-S120-1** gefallen (ein Fehlertyp je Domänentyp, feldagnostisch, Feldbezug an der Grenze). Damit steht das Vorbild fest, an dem sich diese Frage messen lässt. Der frühere Backstop `S132` begründete sich damit, der tragende Anker sei nicht ausdrückbar – das traf schon damals nicht mehr zu (`open_questions.py` verwendet seit S119 `td_anchors.py`).

**Hintergrund:** Aufgekommen im S119-Review beim Verankern von E2. `docs/reference/architecture.md` §2 erklärt das Domain-Modeling-Kapitel ausdrücklich für „C# und TypeScript gleichermaßen" gültig und verweist für die Ausformulierung auf die sprachspezifischen Guidelines. Die dort in §2 verankerte **Regel 5** lautet: „Ein Domänentyp gibt einen Fehler**fall** zurück, nie einen Meldungstext" (ADR-S051-2: die Zuordnung Fall → deutscher Text lebt an der API-Grenze). `coding-guideline-typescript.md` schreibt aber das Gegenteil vor: `ValidationError` trägt ein `message: string` als einziges Feld.

**Nicht automatisch ein Fehler.** ADR-S112-4 hält fest, dass Domänenregeln das **Backend** durchsetzt und Frontend-Brands rein nominal sind – die Factory validiert nicht. Wo nichts validiert wird, entstehen kaum Fehlerfälle, und ein Meldungstext, der vom Server kommt und nur durchgereicht wird, ist an dieser Stelle womöglich das Richtige. Genau das ist zu entscheiden statt anzunehmen.

**Aktueller Stand:** In `architecture.md` §2 ist vermerkt, dass die Regeln für C# ausformuliert sind und die TypeScript-Seite nicht nachgezogen ist – die Doku behauptet also keine Parität mehr, die es nicht gibt. Mit der Entscheidung hier ist dieser Vermerk aufzulösen.
