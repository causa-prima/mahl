# Offene Fragen / geparkte Diskussionen

<!--
wann-lesen: Wenn eines der Themen wieder aufkommt bzw. bevor verwandte Arbeit beginnt
            (z.B. Taxonomie-Frage vor der nächsten ADR-/Suppression-Entscheidung;
            getypte IDs vor ID-naher Domain-Arbeit / US-602).
wann-schreiben: Wenn eine Architektur-/Produkt-Diskussion mit dem User ohne Auflösung
            geparkt wird. Bei Klärung: Eintrag entfernen (Ergebnis ggf. als ADR/Tech-Schuld).

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen.

Eintrag-Format:
  ## OQ-S<NNN>-<n> — <Kurztitel>
  **Frage:** <die offene, mit dem User zu klärende Frage>
  **Hintergrund:** <Auslöser / Kontext / betroffene Artefakte>

  ID: OQ-S<NNN>-<n> – 3-stellige Session (geparkt), laufende Nummer innerhalb der Session.
-->

## OQ-S083-1 — ADR vs. technische Schuld: Taxonomie klären
**Frage:** Wo verläuft die Grenze? User-Sicht: dauerhafte, code-unabhängige Entscheidung = ADR; Doku konkreter Code-Ausnahmen = technische Schuld.
**Hintergrund:** Suppression-ADRs (S000-3/S000-4) pinnen `// Stryker disable`-Kommentare auf **konkrete Code-Zeilen** – und S000-4 beschrieb Code, der diese Session erst (neu) geschrieben wurde; solche code-spezifischen Ausnahmen sind eher Tech-Debt als dauerhafte Architekturentscheidung. Prüfen: ADR-S000-3/S000-4 (und ggf. S083-1/-2) ggf. in einen Tech-Debt-/Suppression-Katalog auslagern; Konsequenzen für die ADR-Konvention.

---

## OQ-S083-2 — Getypte IDs?
**Frage:** `IngredientId` statt rohes `Guid` – gewünscht? Inkonsistenz zu „immer Value Objects" (name/unit gekapselt, Id nicht).
**Hintergrund:** ADR-S030-1 ggf. neu formulieren wenn getypte IDs gewünscht. Merksatz: kanonische Guideline-Beispiele sind Beispiele, kein Dogma.

---

## OQ-S094-1 — Client-seitige Validierung (Instant-Feedback) einführen?
**Frage:** Lohnt eine client-seitige Validierung (Instant-Feedback *vor* dem Speichern) – und wenn ja, drift-frei wie?
**Hintergrund:** Diese Abwägung kam schon mehrfach auf. Die maßgebliche, _front-loaded_ Argumentkette steht stabil in **ADR-S090-1** (Abschnitt „Validierung bleibt server-only / Client-Validierung aufgeschoben", Punkte 1–4) – bitte zuerst dort lesen, damit die Argumente nicht erneut von vorn aufgerollt werden. Kurzfassung: nur **Required** lohnt; Drift ist via backend-getriebener Metadaten lösbar (aber YAGNI); Fokus-aufs-Fehlerfeld bleibt ohnehin custom. **Aktueller Stand:** aufgeschoben aus YAGNI. **Trigger zum Wiederaufgreifen:** ein UX-Szenario fordert explizit Instant-Feedback, oder mehrere große Formulare entstehen parallel (Konsistenzdruck).

---

## OQ-S094-2 — Mobile-Ansicht: welche Szenarien, ab wann?
**Frage:** Welche Mobile-spezifischen Szenarien braucht die App, und ab welcher Phase?
**Hintergrund:** Mobile-First ist NFR (`ux-ui-auditor`, MUI v7), aber `features/` enthält bisher **keine** Mobile-Szenarien. Laut Stories MVP/V1-Scope. Der responsive Reorder-Schutz für Formulare („Felder nicht per CSS umsortieren", weil das die Autofokus-/Fokus-Reihenfolge bricht) ist bereits in UX-Guideline Prinzip 8 verankert. Systematisch beim MVP/V1 angehen – nicht vergessen.
