# Offene Fragen / geparkte Diskussionen

<!--
wann-lesen: Wird vom Drain-Vorschlag am Session-Start vorgelegt, sobald ein `Fällig`-Termin
            erreicht oder ein Eintrag überaltert ist (`obs-drain.py`, Sektion „Offene
            Fragen"). Zusätzlich weiterhin, wenn eines der Themen aufkommt bzw. bevor
            verwandte Arbeit beginnt (z.B. Taxonomie-Frage vor der nächsten ADR-/
            Suppression-Entscheidung; getypte IDs vor ID-naher Domain-Arbeit / US-602).
wann-schreiben: Wenn eine Architektur-/Produkt-Diskussion mit dem User ohne Auflösung
            geparkt wird. Bei Klärung: Eintrag entfernen (Ergebnis ggf. als ADR/Tech-Schuld).

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen.

Eintrag-Format:
  ## OQ-S<NNN>-<n> — <Kurztitel>
  **Frage:** <die offene, mit dem User zu klärende Frage>
  **Fällig:** S<NNN>          (optional – wann soll die Frage vorgelegt werden?)
  **Hintergrund:** <Auslöser / Kontext / betroffene Artefakte>

  ID: OQ-S<NNN>-<n> – 3-stellige Session (geparkt), laufende Nummer innerhalb der Session.

  `Fällig` ist optional und steuert die Vorlage: Ist ein Termin gesetzt, erscheint die Frage
  genau dann (und vorher nicht – ein Termin unterdrückt die Alters-Regel, sonst wäre er
  wirkungslos). Ohne Termin gilt eine Frage nach ~10 Sessions als überaltert und wird
  vorgelegt. Ein Termin lohnt, wenn die Frage an ein Ereignis gebunden ist („vor US-602");
  ohne Termin genügt das Alter.
-->

## OQ-S094-1 — Client-seitige Validierung (Instant-Feedback) einführen?
**Frage:** Lohnt eine client-seitige Validierung (Instant-Feedback *vor* dem Speichern) – und wenn ja, drift-frei wie?
**Fällig:** S140 – reiner Backstop. Der tragende Trigger ist das Ereignis (siehe „Trigger zum Wiederaufgreifen" unten), nicht das Alter; ausdrücken lässt er sich hier noch nicht, weil `Fällig` bei OQ bisher nur eine Session-Nummer kennt. Sobald dieses Feld die Anker-Grammatik aus `.claude/scripts/td_anchors.py` übernimmt, wird daraus `Phase:V1`.
**Hintergrund:** Diese Abwägung kam schon mehrfach auf. Die maßgebliche, _front-loaded_ Argumentkette steht stabil in **ADR-S090-1** (Abschnitt „Validierung bleibt server-only / Client-Validierung aufgeschoben", Punkte 1–4) – bitte zuerst dort lesen, damit die Argumente nicht erneut von vorn aufgerollt werden. Kurzfassung: nur **Required** lohnt; Drift ist via backend-getriebener Metadaten lösbar (aber YAGNI); Fokus-aufs-Fehlerfeld bleibt ohnehin custom. **Aktueller Stand:** aufgeschoben aus YAGNI. **Trigger zum Wiederaufgreifen:** ein UX-Szenario fordert explizit Instant-Feedback, oder mehrere große Formulare entstehen parallel (Konsistenzdruck).

---

## OQ-S094-2 — Mobile-Ansicht: welche Szenarien, ab wann?
**Frage:** Welche Mobile-spezifischen Szenarien braucht die App, und ab welcher Phase?
**Hintergrund:** Mobile-First ist NFR (`ux-ui-auditor`, MUI v7), aber `features/` enthält bisher **keine** Mobile-Szenarien. Laut Stories MVP/V1-Scope. Der responsive Reorder-Schutz für Formulare („Felder nicht per CSS umsortieren", weil das die Autofokus-/Fokus-Reihenfolge bricht) ist bereits in UX-Guideline Prinzip 8 verankert. Systematisch beim MVP/V1 angehen – nicht vergessen.
