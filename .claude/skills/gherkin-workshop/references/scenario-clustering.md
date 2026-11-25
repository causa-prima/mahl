# Szenario-Clustering

Gruppiert die fertigen Szenarien einer User Story in **Implementierungs-Läufe** –
ein Lauf = ein Implementierungs-Durchlauf. Ziel ist nicht „möglichst wenige Läufe",
sondern **möglichst homogene** Läufe.

## Worum es geht

Mehrere Szenarien in einem Durchlauf umzusetzen statt jedes einzeln spart den fixen Overhead,
der pro Durchlauf anfällt. Der Preis ist ein Risiko: je **heterogener** ein Bündel, desto
schwerer fällt es, jede Assertion sauber auf ihr Szenario-Kriterium zurückzuführen – und desto
eher entsteht Code oder ein Test, den kein Kriterium fordert (Gold-Plating).

Der Hebel dagegen ist **Homogenität**, nicht Größe. Ein homogenes Bündel (gleiches Setup,
gleiche Assertion-Form, nur der Input variiert) kollabiert ohnehin zu *einem* parametrisierten
Test – das Mapping ist dann „jede Zeile = eine Input-Partition", trivial zu prüfen, auch bei
vielen Fällen. Ein heterogenes Bündel derselben Größe zwingt dazu, mehrere unabhängige Mappings
gleichzeitig zu halten. Zielfunktion daher: **Homogenität maximieren** – die passende Größe
ergibt sich von selbst.

**Bewusste Abwägung:** Homogenität geht vor Durchsatz. Wo der Algorithmus ein einzelnes
Szenario isoliert, bleibt es ein eigener Lauf (siehe [Hinweis „Singletons"](#CLU-singletons)).

<a id="CLU-algorithmus"></a>
## Algorithmus

Eingabe: alle Szenarien der Story. Ein resultierender Cluster = ein Lauf. Die Schritte in
Reihenfolge anwenden. Sie zerfallen in zwei Gruppen: die **Split-Schritte** zerteilen die
Szenario-Menge (Capability, Ergebnisklasse, Validierung, Schicht), die **Ordnungs-Schritte**
ordnen und flaggen das fertige Ergebnis (Zustands-Abhängigkeiten, Erstmaligkeiten).

1. <a id="CLU-capability"></a>**Nach Capability gruppieren** (aus dem `When` / der Hauptaktion): Lesen/Liste, Anlegen,
   Ändern, Löschen – plus story-spezifische Operationen (z.B. Reaktivierung). Jede Capability
   ist zunächst ein eigener Cluster.

2. <a id="CLU-ergebnisklasse"></a>**Mutations-Capabilities** (Anlegen/Ändern/Löschen) nach **Ergebnisklasse** trennen:
   - **Validierung** – das `Then` behauptet einen *abgelehnten oder grenzwertigen* Input
     (Fehlermeldung **und** Zustand unverändert).
   - **Success/Verhalten** – das `Then` behauptet eine *erfolgreiche* Mutation oder reines
     Dialog-/UI-Verhalten.

3. <a id="CLU-validierung-split"></a>**Validierung** weiter splitten – zuerst nach **Form**, dann nach **Feld**:
   - *stateless* (kein Seed, reine Input-Prüfung) vs. *state-driven* (Seed nötig,
     Eindeutigkeit/Konflikt) – unterschiedliches Setup, unterschiedliche Invariante.
   - innerhalb *stateless* nach **Eingabefeld** (Name, Einheit, …).
   - Der **valide Grenzwert** einer Feldregel („genau N akzeptiert") gehört in die Familie
     dieses Feldes – als Boundary-Paar mit dem Reject-Fall, nicht zu Success.

4. <a id="CLU-schicht-split"></a>**Success/Verhalten** nach **Schicht** splitten:
   - *frontend-only* – kein HTTP-Call / keine Persistenz-Assertion (Dialog öffnen/schließen/
     zurücksetzen, Fokus, Pflichtfeld-Markierung, Pending-Disabled).
   - *full-stack* – behauptet persistierten Zustand / Liste nach realer Mutation.

5. <a id="CLU-zustands-abhaengigkeiten"></a>**Zustands-Abhängigkeiten auflösen** – kein weiterer Split, nur Reihenfolge und Zuordnung:
   Notiere je Cluster, welche Lebenszyklus-Zustände seine `Given` **voraussetzen** (Reader) und
   welche seine `Then` **herstellen** (Writer). Prüffrage je Cluster: *Lässt sich sein `Given` mit
   dem, was bis zu diesem Lauf gebaut ist, über die Oberfläche herstellen?* Lautet die Antwort
   nein, hängt der Cluster an einem Zustand, den bis dahin kein Lauf schreibt.
   Regel: **Der Writer-Cluster eines Zustands liegt vor jedem Reader-Cluster desselben Zustands.**
   Bei Verletzung drei Auswege, in dieser Reihenfolge prüfen:
   - **Umordnen** – wenn die Abhängigkeit nur in eine Richtung läuft.
   - **Szenario verschieben** – wenn Reader und Writer sich **gegenseitig** voraussetzen (Zyklus;
     keine Reihenfolge erfüllt dann beide Seiten). Das lesende Szenario gehört in den Lauf, der
     den Zustand schreibt: Es beschreibt die Wirkung *dieser Mutation*, nicht die Grundfunktion
     des lesenden Endpoints.
   - **Zusammenlegen** – wenn beide Cluster ohnehin dieselbe Mutation umkreisen.
   Ohne diesen Schritt entsteht ein Lauf, dessen E2E-Arrangement keinen Weg über die Oberfläche
   hat – er erzwingt dann einen Test-only-Endpoint oder das Vorziehen eines späteren Laufs.

   **Die gefundene Abhängigkeit wird aufgeschrieben, nicht nur eingeordnet.** Die Run-Nummer
   allein trägt sie nicht: Sie ordnet nur innerhalb einer Datei, und sie sagt nicht, *warum*
   diese Reihenfolge gilt. Jede Kante, die über die Datei hinausreicht oder die nicht schon
   durch aufsteigende Nummern erfüllt ist, gehört als `· braucht:<ref>` an den Run-Tag (bzw. als
   `# @braucht:` in den Header, wenn sie für die ganze Datei gilt). `next_run.py` legt einen
   Lauf erst vor, wenn seine Vorgänger erledigt sind – eine nicht notierte Kante hat diese
   Wirkung nicht, sondern verlässt sich darauf, dass jemand die Nummern in der richtigen
   Reihenfolge vergeben hat.

   **Neben Zuständen hängen Läufe auch an Regeln.** Prüffrage je Cluster, zusätzlich zur
   `Given`-Frage oben: *Setzt ein `When` oder `Then` eine Regel aus einer Querschnitts-Feature-Datei
   voraus (`@CROSS-…`, `@NFR-…`), deren Lauf noch offen ist?* Dann bekommt der Lauf die Kante auf
   diesen Lauf – auch wenn nur eine Beispielzeile die Regel berührt. Beispiel: Ein Grenzwert-Szenario
   gibt einen Titel mit doppeltem Leerzeichen ein und erwartet ihn mit einfachem gespeichert; das
   geht nur mit `CROSS-text/run-1` (Leerraum zusammenfassen). Fehlt die Kante, legt `next_run.py`
   den Lauf zu früh als fällig vor.

6. <a id="CLU-erstmaligkeiten"></a>**Erstmaligkeiten flaggen** – vor der Implementierung, nicht während:
   Prüfe je Lauf in der festgelegten Reihenfolge: *Was tut dieser Lauf, das noch kein Lauf zuvor
   getan hat?* Führt er den ersten Vertreter einer Klasse ein (erster mutierender
   Single-Resource-Endpoint, erste zweite Seite, erste Liste mit Pagination …), zieht das eine
   **Querschnitts-Policy** nach – Optimistic Concurrency via ETag/If-Match, Navigations-Struktur,
   Ähnliches –, die die feature-orientierte Clusterung nicht abbildet. Benenne sie beim Lauf und
   kläre sie **vor** dessen Implementierung; sonst kommt sie als PLANUNG-Eskalation des
   Schicht-Subagenten mitten im Lauf hoch und erzwingt eine Scope-Diskussion im laufenden
   Betrieb. Bewusst als offene Frage formuliert statt als feste Klassenliste – eine solche Liste
   wäre nie vollständig.

<a id="CLU-hinweise"></a>
## Hinweise

- **Nach dem [Schicht-Split](#CLU-schicht-split) nicht weiter splitten.** Nicht nach einzelner Assertion-Form zerschneiden – das
  erzeugt Mikro-Cluster ohne Mehrwert. (Die Ordnungs-Schritte – [Zustands-Abhängigkeiten](#CLU-zustands-abhaengigkeiten) und [Erstmaligkeiten](#CLU-erstmaligkeiten) – splitten nicht, sie ordnen und flaggen.)
- <a id="CLU-singletons"></a>**Singletons bleiben eigene Läufe.** Ergibt der Algorithmus einen Cluster mit nur einem
  Szenario, ihn *nicht* in einen unähnlichen Cluster zwingen, nur um einen Lauf zu sparen –
  das schleppte genau die Heterogenität ein, die wir vermeiden. Ein Singleton ist gewollt,
  kein Versehen. (Tritt natürlich auf, wenn die Story von einer Form nur ein Exemplar hat.)
- **Kein Größen-Deckel.** Ein homogener Cluster mit vielen Fällen ist *ein* parametrisierter
  Batch und braucht keinen Split. Fühlt sich ein Cluster „zu groß" an, wurde eine der Achsen
  der Split-Schritte übersprungen – diese anwenden, statt willkürlich zu trennen.
- **Reihenfolge der Läufe:** zuerst der Full-stack-Success-Cluster der zentralen Mutation
  (er baut den Endpoint), darauf dessen Validierungs-Cluster; übrige Capabilities danach. Die
  Reihenfolge ist im Übrigen weich – hart sind zwei Bedingungen: Validierung setzt auf dem
  Endpoint des Success-Laufs auf, und die Bedingung aus [Zustands-Abhängigkeiten auflösen](#CLU-zustands-abhaengigkeiten) (Writer vor Reader).
- Der einzige Urteilspunkt unter den Split-Schritten ist die [Capability-Gruppierung](#CLU-capability) (welche Aktion = welche Capability). Den Rest
  bestimmt die Form; die Ordnungs-Schritte kommen danach auf das fertige Clustering.

<a id="CLU-output"></a>
## Output: Lauf-Kommentar-Tags

Jedes Szenario erhält einen **Kommentar-Tag** direkt oberhalb seiner `@US-NNN-…`-Tag-Zeile
(über etwaigen Erklär-Kommentaren – so bleibt der `@`-Tag adjazent zum `Scenario:`):

```gherkin
  # @run-1 · Anlegen·Success · Full-Stack
  @US-904-happy-path
  Scenario: Zutat anlegen
```

Format: `# @run-<N> · <Cluster-Label> · <Schicht>[ · Singleton][ · Phase:<P>][ · braucht:<refs>]`

- **Frontend-only** / **Full-Stack** – die Schicht des Laufs: *Frontend-only* braucht keinen
  Backend-Subagenten (reines UI-/Dialog-Verhalten), *Full-Stack* berührt Frontend und Backend.
- **Singleton** – ein Lauf mit nur einem Szenario; wird ergänzt, damit klar ist, dass der
  einzelne Eintrag Absicht ist (siehe [Hinweise](#CLU-hinweise)).
- **Phase:`<P>`** – eine von `SKELETON`, `MVP`, `V1`. Bestimmt, ab wann der Lauf überhaupt
  fällig ist. Weglassen, wenn die Datei-Direktive `# @phase:` (siehe unten) schon die richtige
  Phase setzt; angeben, wenn dieser Lauf davon abweicht (z.B. eine Story, deren Bearbeiten-Läufe
  erst im MVP kommen). Ein Lauf **ohne** Phase – weder hier noch per Direktive – wird nie fällig;
  `next_run.py --check` blockt das.
- **braucht:`<refs>`** – kommaseparierte Vorgänger-Läufe, die vor diesem gebaut sein müssen:
  `run-8` innerhalb derselben Datei, `US-904/run-8` datei-übergreifend (Präfix = Top-Level-Tag
  der Zieldatei ohne `@`). Ersetzt die Datei-Direktive `# @braucht:`, ergänzt sie nicht.
- Bewusst ein **Kommentar**, kein echter Gherkin-`@tag`: der Bauplan soll die Spec nicht
  verunreinigen und keine Test-Runner-Tags belegen.
- Greppbar via `# @run-`. `<N>` = Lauf-Nummer = Implementierungs-Reihenfolge **innerhalb einer
  Datei**. Über Dateigrenzen hinweg ordnet sie nichts – dafür sind `braucht:`-Kanten da.

<a id="CLU-datei-direktiven"></a>
### Datei-Direktiven: Phase, Kanten und Stufen für die ganze Datei

Im Feature-Header – vor `Background:`/dem ersten `Scenario:` – stehen zwei Direktiven, die als
Default für **alle** Läufe der Datei gelten:

```gherkin
@NFR-resilience
Feature: Querschnittliche Fehlerbehandlung

  # @phase: MVP
  # @braucht: US-904/run-1,US-904/run-7
```

Sie sind der einzige Weg für Dateien **ohne** Run-Tags (querschnittliche Features nach
ADR-S103-1): Deren Szenarien bilden je einen Einzel-Lauf und hätten sonst nirgends eine Phase
anzuschreiben. Unterhalb des Headers sind sie ein Verstoß – dort sähen sie lokal aus und wirkten
global.

Muss ein Lauf einer **anderen** Datei auf eine Querschnittsdatei warten, bekommt diese
Lauf-Kommentare: Eine `braucht:`-Kante kann nur auf einen Lauf mit Nummer zeigen, nicht auf einen
Einzel-Lauf ohne Run-Tag. Beispiel: `US-602/run-13` braucht `CROSS-navigation/run-1`, weil es die
Navigationsleiste bedient.

Eine dritte Direktive gilt nur für Story-Dateien (`@US-NNN`): `# @stufen: SKELETON, MVP` nennt
die Stufen der Story, deren Akzeptanzkriterien der Workshop **vollständig** spezifiziert hat. Die
Stufen einer Story sind die Köpfe ihrer Akzeptanzkriterien-Blöcke in `docs/stories/`
(`**Akzeptanzkriterien (MVP – …):**`; ohne Klammer die Phase der Story). Jede erreichte Stufe,
die nicht genannt ist, meldet `next_run.py` als „ohne Workshop" – sonst wären spätere Stufen einer
Story mit Feature-Datei unsichtbar. Fehlt die Direktive, gilt die Stufe aus `# @phase:`.
Teilweise spezifizierte Stufen werden nicht genannt; `next_run.py --check` blockt Stufen, die die
Story gar nicht hat.

<a id="CLU-kopf-regeln"></a>
### Kopf-Regeln ohne Szenario: Absicherung und Lauf

Was der Kopf der Feature-Datei über Verhalten festlegt, ohne dass ein Szenario es trägt – eine
Regel, ein Querschnittsvertrag, eine bekannte Grenze, eine Invariante für den ADR-Check –, bekommt
als letzte Zeile einen Vermerk, wie es abgesichert wird und in welchem Lauf:

```gherkin
  #   - Findet der Server beim Übernehmen keine Vormerkung, wird die Einkaufsliste leer.
  #     → Integrationstest · run-2
```

Format: `→ <Absicherung> · run-<N>[, run-<M>]`

- **Absicherung** – `Komponententest` oder `Integrationstest` (Kategorie „Vertrag aus dem
  Feature-Kopf" in ADR-S106-3), oder `keine (unbestimmt erlaubt)` ohne Lauf, wenn das Verhalten
  bewusst offen bleibt. Der Vermerk `keine` hält fest, dass das entschieden ist und nicht vergessen.
- **Lauf** – der Lauf, der den Code baut, den die Aussage betrifft; bei einem Vertrag über mehrere
  Seiten jeder dieser Läufe.
- Deckt ein Szenario nur einen Teil eines Spiegelstrichs, wird der Rest ein eigener Spiegelstrich.
  Keinen Vermerk tragen Aussagen, die ein Szenario trägt oder die aus einem folgen (etwa eine
  bekannte Grenze als Folge einer Regel), die Liste der Übergangsregeln, Punkte für spätere
  Workshops und Hinweise für die Step-Implementierung.

Wirkung: `check-atdd-gate.py` gibt im Lauf-Modus nach den Szenarien die Kopf-Regeln des Laufs
aus, mit ihrer Überschrift. So stehen sie im Architektur-Check und im Auftrag an die
Schicht-Subagenten wie ein Szenario. Gelesen wird jede Laufnummer hinter dem letzten Pfeil der
Aussage, auch über einen Zeilenumbruch. Nicht erscheint eine Aussage ohne Vermerk, mit einem
Vermerk ohne Lauf (zwischen Workshop und Clustering) oder mit Formfehler (`->`, `run2`) – und
ein Vermerk auf einen Lauf ohne Szenario, weil das Gate dort schon vorher anhält. Auf diese
Fälle prüft nichts: Den Vermerk nach dem Clustering einmal mit der Gate-Ausgabe abgleichen.

## Beispiel

`scenario-clustering-example.html` (in diesem Ordner) – interaktive Visualisierung des
Algorithmus an US-904 (31 Szenarien → 11 Läufe, Schritte durchklickbar).
