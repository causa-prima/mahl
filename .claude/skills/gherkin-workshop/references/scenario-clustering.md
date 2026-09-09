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
### Datei-Direktiven: Phase und Kanten für die ganze Datei

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

## Beispiel

`scenario-clustering-example.html` (in diesem Ordner) – interaktive Visualisierung des
Algorithmus an US-904 (31 Szenarien → 11 Läufe, Schritte durchklickbar).
