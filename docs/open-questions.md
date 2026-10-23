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
            seitige, also wie gearbeitet wird (`prozesscode/`, `.claude/**`, `docs/process/`, `docs/kaizen/`) –
            das läuft über `docs/kaizen/observations.md`; (c) eine Aufgabe, der nur die
            Priorisierung fehlt (das ist `docs/AGENT_MEMORY.md`).
            Abgrenzung ADR/TD/OQ kanonisch: [„Ablage: in welchen Tracker gehört dieser
            Eintrag?"](../AGENTS.md#CLA-ablage)

Sortierung: nach ID (Session) aufsteigend – neue Einträge unten anfügen.

Eintrag-Format:
  ## OQ-S<NNN>-<n> — <Kurztitel>
  **Frage:** <die offene, mit dem User zu klärende Frage>
  **Fällig:** <Anker>[, <Anker>…] – <Prosa>   (Pflicht – wann vorlegen?)
  **Hintergrund:** <Auslöser / Kontext / betroffene Artefakte>
  **Aufschubgrund:** User | Recherche – <warum nicht sofort geklärt>   (Pflicht für neue
            Einträge seit S133, meist `User`: gefragt, Antwort bewusst vertagt. Bedeutung der
            Werte: `prozesscode/eintrag_felder.py`)

  ID: OQ-S<NNN>-<n> – 3-stellige Session (geparkt), laufende Nummer innerhalb der Session.

  `Fällig` ist **Pflicht** und steuert die Vorlage (`check-oq-capture.py` erzwingt es). Ohne
  Termin fiele der Eintrag auf die Alters-Regel zurück – dann ist eine seit Dutzenden Sessions
  treibende Frage von einer frisch gestellten nicht mehr unterscheidbar. Es nutzt dieselbe Anker-Grammatik wie
  `docs/tech-debt.md` – kanonisch in `prozesscode/td_anchors.py`, von `open_questions.py`
  wiederverwendet (nicht kopiert). Der Kopf vor dem Gedankenstrich ist maschinenlesbar:

      jetzt              sofort vorlegen
      Phase:V1           Phasenwechsel (auch MVP/V2)
      S140               Spätestens-Termin (Session-Nummer)
      Szenario:„…"       ein Gherkin-Szenario aus features/ (Titel exakt) – erscheint, sobald
                         sein Lauf der nächste ist, unter „Nächster Lauf" als „Teil dieses Laufs"
      US-602             eine Story – nur solange sie noch keine Szenarien hat
      TD-S089-1          ein Tech-Debt-Eintrag – tritt ein, wenn jener behoben ist

  Mehrere Anker mit Komma. Alles Erklärende gehört **hinter** den Gedankenstrich.

  Ist ein Anker gesetzt, erscheint die Frage genau dann (und vorher nicht – ein Anker
  unterdrückt die Alters-Regel, sonst wäre er wirkungslos). **Ohne** das Feld gilt eine Frage
  nach ~10 Sessions als überaltert und wird vorgelegt.

  Mechanisch geprüft an beiden Enden: `prozesscode/hooks/check-oq-capture.py` blockt zur
  Schreibzeit ein gesetztes Feld, das nicht trägt (Vertipper, kein terminierter Anker);
  `open_questions.py` meldet zur Lesezeit einen dennoch unauswertbaren Anker, statt ihn zu
  verschlucken. Vorher fiel beides still auf die Alters-Regel zurück und blieb unbemerkt.

  Anders als bei Tech-Debt erzeugt `jetzt` hier einen Vorlage-Grund: TD-Einträge mit `jetzt`
  stehen zusätzlich in `AGENT_MEMORY.md` und kämen sonst doppelt, offene Fragen haben diesen
  zweiten Kanal nicht.
-->

## OQ-S094-1 — Client-seitige Validierung (Instant-Feedback) einführen?
**Frage:** Lohnt eine client-seitige Validierung (Instant-Feedback *vor* dem Speichern) – und wenn ja, drift-frei wie?
**Fällig:** Phase:V1 – der tragende Trigger ist das Ereignis (siehe „Trigger zum Wiederaufgreifen" unten). Das Rezeptformular ist zwar ein zweites großes Formular, seine Spec legt aber „Alle Meldungen kommen vom Server" fest – der Konsistenzdruck-Trigger greift damit nicht.
**Hintergrund:** Diese Abwägung kam schon mehrfach auf. Die maßgebliche, _front-loaded_ Argumentkette steht stabil in **ADR-S090-1** (Abschnitt „Validierung bleibt server-only / Client-Validierung aufgeschoben", alle Punkte dieses Abschnitts) – bitte zuerst dort lesen, damit die Argumente nicht erneut von vorn aufgerollt werden. Kurzfassung: nur **Required** lohnt; Drift ist via backend-getriebener Metadaten lösbar (aber YAGNI); Fokus-aufs-Fehlerfeld bleibt ohnehin custom. **Aktueller Stand:** aufgeschoben aus YAGNI. **Trigger zum Wiederaufgreifen:** ein UX-Szenario fordert explizit Instant-Feedback, oder mehrere große Formulare entstehen parallel (Konsistenzdruck).

---

## OQ-S094-2 — Mobile-Ansicht: welche Szenarien, ab wann?
**Frage:** Welche Mobile-spezifischen Szenarien braucht die App, und ab welcher Phase?
**Fällig:** Phase:MVP – User-Entscheid S122 auf die zweite Hälfte der Frage („ab wann"): Beim Phasenwechsel SKELETON→MVP läuft ein `gherkin-workshop`, der die Mobile-Szenarien für die dann bestehenden Seiten systematisch entdeckt. Bis dahin trägt die UX-Guideline (Formular-/Dialog-Baseline, Reorder-Schutz) die Mobile-Anforderung allein.
**Hintergrund:** Mobile-First ist NFR (`ux-ui-auditor`, MUI v7), aber `features/` enthält bisher **keine** Mobile-Szenarien. Laut Stories MVP/V1-Scope. Der responsive Reorder-Schutz für Formulare („Felder nicht per CSS umsortieren", weil das die Autofokus-/Fokus-Reihenfolge bricht) ist bereits in UX-Guideline der Formular-/Dialog-Baseline verankert. Systematisch beim MVP/V1 angehen – nicht vergessen.

---

## OQ-S119-3 — Native C#-Union-Types statt `SumType.cs`, sobald .NET 11 verfügbar ist?
**Frage:** Werden die handgerollten Sum-Types (`Server/Types/SumType.cs`, ADR-S040-1) auf native `union`-Typen umgestellt, sobald das Projekt auf .NET 11 / C# 15 steht?
**Fällig:** S150 – verschoben in S130. Die Richtung steht (User-Tendenz deutlich zu den nativen Union-Types); offen ist allein die Verfügbarkeit. Tragender Trigger bleibt der Wechsel auf .NET 11 (GA November 2026 angekündigt), S150 ist nur der Backstop dahinter (~3,3 Tage/Session zum Zeitpunkt der Schätzung). Bei Wiedervorlage sind die beiden Haken unten zu prüfen – Boxing der Struct-Unions und der tatsächliche Spec-Umfang zum GA-Zeitpunkt.

**Hintergrund:** Recherchiert in S119. C# 15 führt `union` als nominale Deklaration ein (`public union Pet(Cat, Dog, Bird);`) mit compiler-erzwungener Exhaustivität in `switch`, dazu den `closed`-Modifier für geschlossene Hierarchien. Verfügbar ab .NET 11 Preview 2, GA für November 2026 angekündigt.

**Warum relevant:** `IngredientId` ist als Union `Known`/`Unknown` über `SumType.cs` gebaut (in S118 entschieden, in S120 umgesetzt – verworfen wurde die Alternative „zwei Entitätstypen `IngredientValues`/`Ingredient`", weil US-306 Schreiben ohne erreichbares Backend verlangt (ADR-S000-13, ADR-S112-4), die ID aber serverseitig vergeben wird (ADR-S030-1): eine Phase ohne Server-ID ist dokumentiert absehbar); nativ entfielen die `SumType.Unreachable<T>()`-Arme samt Stryker-Suppression (ADR-S018-2) – genau das Bedenken, das bei der ID-Modellierung diskutiert wurde.

**Zwei Haken, die 2026 gegen ein Warten auf .NET 11 sprachen** – sie sind weiterhin die Prüfpunkte, an denen die Umstellung zu messen ist:
1. Unions sind Structs mit einem `object? Value` – **Value Types boxen bei jeder Zuweisung.** Die Domänentypen des Projekts sind `readonly record struct` ausdrücklich, um Heap-Allokation zu vermeiden (Typen-Tabelle in [Immutability](guidelines/coding-guideline-csharp.md#CGC-immutability)).
2. Das Projekt steht auf `net10.0`; `LangVersion=latest` liefert auf dem .NET-10-SDK C# 14, nicht 15. In Preview 5 fehlen laut Doku noch Teile der Spec (`ClosedAttribute` shippt die Runtime noch nicht).

---

## OQ-S119-4 — Gilt „Regeln in den Typ, Meldungen an die Grenze" auch im Frontend?
**Frage:** Wird der Frontend-Fehlertyp `ValidationError = { readonly message: string }` auf Fehler**fälle** statt Meldungstexte umgestellt – oder gilt die Regel bewusst nur backend-seitig?
**Fällig:** Phase:V1 – User-Entscheid S122: gekoppelt an **OQ-S094-1** (client-seitige Validierung) und darum auf dessen Anker gesetzt, damit beide zusammen entschieden werden. Begründung: Solange das Frontend keine Regeln prüft (ADR-S112-4), entstehen dort keine Fehler**fälle** – die Frage nach deren Typform hat bis dahin keinen Gegenstand.

**Hintergrund:** Aufgekommen im S119-Review beim Verankern von „Domänentyp und Constraint-Typ". [Domain Modeling](reference/architecture.md#ARC-domain-modeling) erklärt das Domain-Modeling-Kapitel ausdrücklich für „C# und TypeScript gleichermaßen" gültig und verweist für die Ausformulierung auf die sprachspezifischen Guidelines. Die dort in den [die Regeln dazu](guidelines/coding-guideline-csharp.md#CGC-domaenentyp-regeln) verankerte Regel **„Meldungen an die Grenze"** lautet: „Ein Domänentyp gibt einen Fehler**fall** zurück, nie einen Meldungstext" (ADR-S051-2: die Zuordnung Fall → deutscher Text lebt an der API-Grenze). `coding-guideline-typescript.md` schreibt aber das Gegenteil vor: `ValidationError` trägt ein `message: string` als einziges Feld.

**Nicht automatisch ein Fehler.** ADR-S112-4 hält fest, dass Domänenregeln das **Backend** durchsetzt und Frontend-Brands rein nominal sind – die Factory validiert nicht. Wo nichts validiert wird, entstehen kaum Fehlerfälle, und ein Meldungstext, der vom Server kommt und nur durchgereicht wird, ist an dieser Stelle womöglich das Richtige. Genau das ist zu entscheiden statt anzunehmen.

**Befund S122, am Bestand geprüft (spart die Recherche beim Wiederaufgreifen):** `ValidationError` existiert im Client-**Code** nicht. `Client/src/types/` enthält allein `apiError.ts`; `grep -rn "ValidationError" Client/src` liefert null Treffer. Der Typ lebt ausschließlich in `coding-guideline-typescript.md` (Fehlertyp-Absatz in [Branded Types](guidelines/coding-guideline-typescript.md#CGT-branded-types) sowie das `neverthrow`-Beispiel in [Railway-Oriented Programming](guidelines/coding-guideline-typescript.md#CGT-rop)). Real verwendet wird `ApiError` (`Client/src/types/apiError.ts`) – bereits eine kind-getaggte Union (`FieldErrors` | `Unexpected`), also schon in der dort verlangten Form. Es ist heute folglich **nichts umzustellen**; zu entscheiden ist, ob die Guideline einen Typ für einen Fall vorschreiben soll, den ADR-S112-4 ausschließt.

**Aktueller Stand:** In [Domain Modeling](reference/architecture.md#ARC-domain-modeling) ist vermerkt, dass die Regeln für C# ausformuliert sind und die TypeScript-Seite nicht nachgezogen ist – die Doku behauptet also keine Parität mehr, die es nicht gibt. Mit der Entscheidung hier ist dieser Vermerk aufzulösen.

---

## OQ-S135-1 — Umrechnung zwischen Einheiten: welche Stufen, wo gepflegt, wann angewendet?
**Frage:** Welche Umrechnungen braucht mahl, und wann werden sie angewendet? Innerhalb einer Größenart (g↔kg, ml↔l, EL=15 ml, TL=5 ml) allgemein und exakt; über Größenarten hinweg (Stück↔g, Dose↔g, Löffel↔g) nur je Zutat – überhaupt nötig? Auf der Einkaufsliste bleiben gemischte Einheiten laut User eher nebeneinander stehen („200 g + 10“). Und: Welche Rolle behält die Basiseinheit einer Zutat, wenn jede Rezeptzeile ihre eigene Einheit speichert (Ziel der Summierung? Vorgabe beim Parsen?) – und was folgt dann aus dem Ändern der Basiseinheit?
**Fällig:** Phase:MVP – im gherkin-workshop der US-904-MVP-Stufe (Bearbeiten), gemeinsam mit US-902 (Umrechnungsfaktoren) und den Einkaufslisten-Stories; vorher gibt es weder Bearbeiten einer Zutat noch Summierung.
**Hintergrund:** Aus dem US-602-Workshop. Jede Rezeptzeile speichert Menge UND Einheit (ADR-S020-1) – das Ändern der Basiseinheit einer Zutat lässt Rezeptmengen also unberührt. Analyse der Rezeptsammlung des Users (1086 Zutatenzeilen): dieselbe Zutat erscheint oft in mehreren Größenarten (Tomaten als g/Dose/Stück, Sahne als ml/g/EL, Zwiebeln als Stück/g). Ein allgemeiner Standard über Größenarten hinweg (z. B. 1 TL = 7 g) liegt je Zutat bis Faktor 2 daneben. User zu Umrechnung beim Summieren: „In Bring! mache ich das mal so und mal so, aber vermutlich häufiger 200 g + 10.“
**Aufschubgrund:** User – im US-602-Workshop auf den US-904-MVP-Workshop gelegt (dort entsteht das Bearbeiten der Zutat).

---

## OQ-S135-2 — Zutatenzeile zerlegen: unscharfe und mehrdeutige Zuordnung
**Frage:** Wie ordnet der Parser die Teile einer Freitext-Zutatenzeile zu, wenn kein exakter Treffer existiert? Teilfragen des Users: Was, wenn mehrere Kandidaten gleich gut passen? Was, wenn zwei Teile der Eingabe beide als Zutat (oder beide als Zusatz) erkannt werden? Ergänzend: feste Regeln je Zutat ("2 Knoblauchzehen" → 2 Zehen Knoblauch), allgemeine Zusatz-Regeln über Zutaten hinweg ("gemahlene/gemahlenes X" → "X, gemahlen"), Lernen aus Korrekturen des Users (Alias speichern).
**Fällig:** Phase:MVP – im Workshop der MVP-Stufe der Zutateneingabe (Plural, Kurzformen, Zusatz, Tippfehler-Toleranz); der SKELETON arbeitet mit harten Regeln (exakter Name, Einheit weggelassen oder = Basiseinheit).
**Hintergrund:** Aus der Durchsicht der US-602-Szenarien: Entscheidung für Freitext je Zutatenzeile, vom Backend in Menge, Einheit, Zutat und Zusatz zerlegt (Vorbild Chefkoch). Vorschlag des Users: Kandidaten unter bekannten Zutaten und Zusätzen nach geringster Distanz (Levenshtein o. ä.) suchen, höchster Score gewinnt. Ein Test bei Chefkoch zeigte, dass dort "2 Knoblauchzehen"/"2 Zehen Knoblauch" und "Tomaten, stückig"/"stückige Tomaten" je auf verschiedene Zutaten fallen. Chefkoch ist Referenz, keine Vorgabe – Zielgruppe hier: zwei Nutzer. Nach V1 zusätzlich: "Salz und Pfeffer" beim "und" in zwei Zeilen aufteilen (offen dabei: "1 TL Salz und Pfeffer" – gilt die Menge für beide?). Testbestand: die DokuWiki-Rezeptsammlung des Users (~/rezepte, 114 Rezepte, 1086 Zutatenzeilen, u. a. Spannen, "etwas", "oder"-Alternativen, Tippfehler wie "Kreukümmel"/"Zirone", Einheit im Namen wie "Knoblauchzehen") – laut User keine eigene Story, sondern Test für den Parser bzw. einmaliger Übernahme-Auftrag an einen Agenten. Abgrenzung Zusatz: Produkt-Modifizierer vs. Zubereitungshinweis (Glossar, US-904 MVP).
**Aufschubgrund:** User – Parser-Komfort ist laut User frühestens MVP; der SKELETON arbeitet mit harten Regeln.

---

## OQ-S135-3 — Zeitmodell: Arbeitszeit und Wartezeiten statt Gesamtzeit
**Frage:** Wie bildet mahl die Zeit eines Rezepts ab? Entschieden: gemessen wird nur die Zeit, in der man arbeitet; Wartezeiten (Backen, Garen ohne Aufsicht, Gehen) werden von Hand erfasst, nicht eingerechnet, aber daneben angezeigt. Offen: (a) Begriffe – Vorschlag „Arbeitszeit“ und „Wartezeiten“ statt „Gesamtzeit“; (b) Wartezeiten MITTEN im Rezept (Teig geht 1 h, dann weiter): Vorschlag – ein Schritt mit Typ „Warten“ und Dauer (US-617) hält die Messung an, solange er der aktuelle Schritt ist; arbeitet man parallel weiter, ist man im nächsten Schritt und die Uhr läuft; (c) wie US-610 (Gesamtzeit, MVP), US-611 (vier Zeitkomponenten, V2), US-617 (Aktivitätsart je Schritt, V2) und US-108 (Zeit-Budget mit „aktiver Arbeitszeit“, V2) dazu umgeschnitten werden; (d) Zeitstempel je Schrittwechsel mitspeichern? Die Anhalte-Logik aus (b) braucht sie ohnehin, und Rohdaten lassen sich später nicht nachholen – angezeigt würde trotzdem nur die Summe.
**Fällig:** Phase:MVP – im gherkin-workshop von US-610 (Gesamtzeit); dort entsteht das erste Zeitfeld.
**Hintergrund:** Aus der Bestandsanalyse der Rezeptsammlung des Users: 62 von 114 Rezepten notieren die Zeit schon als „Arbeit + Warten“ (z. B. „15 + 60 + 10 Minuten“). 18 Rezepte haben parallele Schritte („In der Zwischenzeit …“) – deshalb misst US-517 nicht je Schritt, sondern je Kochvorgang. User: Wartezeiten am Ende werden nicht gemessen, weil niemand dafür die App öffnet; das Ende braucht einen gut sichtbaren „Kochen abschließen“-Knopf; starke Abweichung vom Median soll sofort eine Warnung mit Aktionen auslösen (in US-517 übernommen).
**Aufschubgrund:** Umfang – betrifft fünf Stories über MVP bis PARKING; die Klärung gehört in den Workshop des ersten Zeitfelds (US-610), nicht in die Durchsicht von US-602.

---

## OQ-S135-4 — Testtiefe für Code, der sicher ersetzt wird
**Frage:** Braucht Code einer Übergangsregel (Ablösung fest eingeplant, gherkin-workshop „Tiefe je Regel"), der mit seiner Nachfolgelösung wieder entfällt, die volle Coverage-Schwelle und volle Mutationstests – oder gilt für ihn eine Ausnahme, und wenn ja, wie wird sie markiert und wann endet sie?
**Fällig:** Szenario:„Zutat nicht gefunden oder Einheit falsch", Phase:MVP – Lauf 11 von US-602 ist der letzte Lauf zum Zerleger der Zutatenzeilen (Übergangsregel, abgelöst durch US-607); erst dann gibt es echte Zahlen zum Testaufwand.
**Hintergrund:** Aus der Auswertung des neuen Workshop-Schritts „Tiefe je Regel" an US-602. Der User fragte, ob „temporärer Code keine Coverage braucht"; Gegenfrage war, wie sicher die typischsten Fälle dann korrekt umgesetzt werden. Zu erheben in den Läufen 7, 10 und 11 von US-602: Wie viele Tests (Unit, Integration, Mutanten) entstehen für den Zerleger, und wie viele davon entfallen mit US-607? Die Spezifikation selbst wurde bereits verschlankt (SKELETON 63 → 46 Szenarien).
**Aufschubgrund:** User – im Workshop vereinbart, nach dem Ausprobieren mit echten Zahlen zu entscheiden

---

## OQ-S137-1 — Log-Ziel in Produktion: Wo landen Logs, sodass sie ein Redeploy überstehen?
**Frage:** Wohin gehen die Backend-Logs in Produktion, damit sich Probleme im Nachhinein nachvollziehen lassen – auch über Neustarts und Redeploys hinweg? Optionen: (a) Docker-Log-Treiber, der außerhalb des Containers persistiert (z.B. journald), (b) Log-Sammler (z.B. Seq, Loki, Elasticsearch) – dann lohnt strukturiertes Logging (Serilog, JSON), (c) Datei durch die Anwendung – widerspräche der Observability-Anforderung in docs/process/nfr.md (stdout, Persistenz durch die Laufzeitumgebung). Hängt an der Hosting-Entscheidung.
**Fällig:** Phase:V1 – erst mit dem Produktivbetrieb müssen Logs Redeploys überstehen; vorher reicht stdout in der Entwicklung
**Hintergrund:** S137: Serilog (AspNetCore, Sinks.Console, Sinks.File) war referenziert, aber nie angeschlossen, und wurde vom User entfernt. ADR-S054-7 schließt Serilog aus dem MVP-Scope aus. Die Observability-Anforderung (docs/process/nfr.md, Abschnitt Observability) legt stdout als Ausgabeziel fest und überlässt Persistenz der Laufzeitumgebung. Falle (aus Docker-Wissen, nicht verifiziert): Der Standard-Log-Treiber json-file hält Logs pro Container; sie verschwinden, wenn der Container beim Redeploy neu erzeugt wird – also gerade nach dem Update, das ein Problem verursacht haben könnte. Der User will in V1 nachvollziehen können, was Probleme verursacht hat.
**Aufschubgrund:** User – der User hat entschieden, die Frage mit V1 zu klären

---

## OQ-S141-1 — Rückmeldung bei Server- oder Netzwerkfehler beim Speichern eines Rezepts
**Frage:** Was sieht der Nutzer, wenn POST /api/recipes mit 5xx antwortet oder das Netz fehlt – Meldung wo und mit welchem Text, bleiben die Eingaben erhalten, gibt es einen Weg zum erneuten Versuch?
**Fällig:** Phase:MVP – mit dem globalen Exception-Handler aus ADR-S112-1 liefert der Server dann ProblemDetails, auf die das Frontend reagieren muss
**Hintergrund:** Security- und Korrektheits-Review US-602 run-2: createRecipe (Client/src/services/recipesApi.ts) wertet den Status nicht aus. Die Läufe run-8 bis run-12 bauen nur die 422-Pfade (FieldErrors); für 5xx/Netzwerkfehler gibt es in features/recipes.feature kein Szenario. Die technische Meldung aus toUnexpectedError darf laut docs/process/nfr.md (Reliability) nicht ungefiltert angezeigt werden.
**Aufschubgrund:** User – in der Abschluss-Triage von US-602 run-2 als offene Frage mit Phase MVP entschieden
