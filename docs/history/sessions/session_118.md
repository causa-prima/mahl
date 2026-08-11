# Session 118 – 2026-08-12

**Phase:** SKELETON | **Art:** Klärung der drei fälligen offenen Fragen (kein Code)

Geplant war ein OBS-Drain über sieben Einträge. Stattdessen wurden die drei fälligen offenen
Fragen erstmals überhaupt dem User vorgelegt – seit S115 standen sie nur im Agenten-Startkontext
(OBS-S117-2) und davor 32 Sessions lang in einer Datei ohne Lese-Trigger. Alle drei sind geklärt.
Der Drain-Satz blieb unberührt.

---

## E1 – Ablage-Taxonomie ADR / TD / OQ (war OQ-S083-1)

Drei Trennschnitte, jeder für sich eindeutig:

| Schnitt | Trennt |
|---|---|
| **Produkt vs. Prozess** | ADR/TD/OQ (Code + Build-/Test-Kette: `stryker-config.json`, `playwright.config.ts`, `Directory.Build.props`) ↔ OBS/CM/LL (`.claude/**`, `docs/process/`, `docs/kaizen/`) |
| **entschieden vs. offen** | ADR/TD ↔ OQ |
| **terminal vs. terminierend** | ADR ↔ TD |

**Operativer Test:** *„Ist die Sache erledigt – bleibt dann etwas zu erklären übrig, das ohne
diesen Eintrag unverständlich wäre?"* Ja → ADR (wird `Superseded`, bleibt stehen). Nein → TD
(verschwindet ersatzlos).

**Keine Hybride.** Eine ADR trägt keinen Aufschub; der Aufschub-Teil gehört als eigener TD-Eintrag
abgelegt. Der Test findet im Bestand sofort zwei: **ADR-S083-1** („ToDomain aufgeschoben") und
**ADR-S083-2** („volle Union aufgeschoben") haben nach Behebung keinen terminalen Rest und sind
damit TD. ADR-S083-2 benennt das selbst („Bekannte Konsequenzen (technische Schuld bis zur
Erweiterung)") und hat in TD-S101-1 bereits einen Zwilling, der dort nicht referenziert wird.
Beide werden aus dem Code referenziert (`Server/Endpoints/IngredientsEndpoints.cs:189`, vier
Stellen in `Client/src/hooks/`) – die Kommentare müssen beim Umhängen mit.

**Lifecycle – bewusste Abweichung von der Lehrmeinung.** Der Mainstream kennt kein Löschen von
ADRs (immutable, nur `Superseded`). Hier gilt: Eine ADR, die je gegolten hat, bleibt als
`Superseded` stehen, weil sie Projekthistorie erklärt – auch wenn keine Anwendungsstelle mehr
existiert. Eine ADR, die **nie** angewendet wurde, erklärt nichts und wird gelöscht (Präzedenz
S108: ADR-S000-3). Im Zweifel behalten. Kein `Rejected`-Archiv.

**Ort der Regel:** Aufnahmebedingung je Datei-Header, gemeinsame Übersicht in `CLAUDE.md` –
einziges Dokument mit garantiertem Lese-Trigger und ohnehin Routing-Zentrale. **Nicht** in
`docs/kaizen/process.md`: Die dortige Tabelle „Wann gehört etwas wohin?" ist die Kaizen-Taxonomie
und dort vollständig; mein anfänglicher Befund einer Lücke war ein Fehlschluss. **Keine** eigene
Datei – sie hätte keinen Lese-Trigger (Argument des Users).

## E2 – Domänentyp und Constraint-Typ (war OQ-S083-2, Prinzipienteil)

Fünf Regeln, kanonischer Ort ist `coding-guideline-csharp.md` §2 mit Verweis aus `architecture.md`:

1. **Der Domänentyp ist die Schnittstelle, der Constraint-Typ die Implementierung.** Constraint-Typ
   = Prädikat über einer Repräsentation, wiederverwendbar, `Server/Types/`. Domänentyp = Rolle in
   der Fachsprache, nicht wiederverwendbar, `Server/Domain/`. Der Domänentyp *benutzt* Constraint-
   Typen als Baumaterial; wird seine zulässige Menge aufzählbar (Enum) oder strukturiert (Sum-Type),
   verschwindet der Constraint-Typ ersatzlos. **Ertrag:** Steht der Constraint-Typ in Signaturen,
   ist ein Implementierungsdetail geleckt – der absehbare Wechsel `Unit`: string → Enum wird dann
   zur Breaking Change an jeder Signatur statt zur Änderung in einer Datei.
2. **Rolle ≠ Typ.** `DefaultUnit`, Alternativeinheiten, Rezept- und Einkaufslisten-Einheit sind alle
   `Unit`; die Rolle steckt im Feldnamen. Ausnahme: eine Rolle mit eigener Invariante bekommt einen
   eigenen Typ (`ConversionFactor` ist kein `Unit`).
3. **Verwechslungsschutz ist Nebenprodukt, kein Entwurfsziel.** Nie fragen „brauche ich hier einen
   Typ gegen Vertauschen?", sondern „ist das ein eigenes Fachkonzept?". Zwei Parameter desselben
   Konzepts dürfen denselben Typ haben. Das verhindert die Rutschbahn zu einem Typ pro Parameter.
4. **Abwesenheit ist keine Einschränkung.** Bevor ein Wert einen Sonderfall bekommt (`Guid.Empty`,
   `-1`, `""`), prüfen, ob Optionalität gemeint ist. Optionalität gehört out-of-band (Union/`Option`),
   nie ins Wertband des Domänentyps.
5. **Regeln in den Domänentyp, Meldungen an die Grenze.** `MaxLength` lebt im Typ; die Zuordnung
   Fehlerfall → deutscher Text bleibt an der API-Grenze (ADR-S051-2 unberührt).

Geltungsbereich, am Bestand belegt: Die Regel endet an der DTO-/DbType-Grenze
(`coding-guideline-csharp.md` §57 „in den Geschäftsmodellen", §157–158 Write-/Read-Pfad, §281
zeigt rohe Primitives im DbType; `architecture.md:88/89` – `mahl.Infrastructure` ist `public`,
`mahl.Server` internal, ein Domänentyp kann dort gar nicht auftauchen). Deshalb bleiben `Name` und
`DefaultUnit` im DTO `string`, und der Umbau berührt nur die Domäne.

## E3 – ID-Modellierung (war OQ-S083-2, Umsetzungsteil)

Beschlossen: **Union-Typ** `Known`/`Unknown` als ID, `IngredientId` als eigener Domänentyp darüber
(nach Regel 1 – eigenes Fachkonzept, nicht wegen Verwechslungsschutz). Constraint-Schichtung:
`Guid` (Repräsentation) → `Uuid7` (Prädikat aus ADR-S030-1, subsumiert `Guid.Empty`, `Server/Types/`)
→ `IngredientId` (`Server/Domain/`). Volltext in TD-S118-1.

Die Alternative – zwei Entitätstypen `IngredientValues`/`Ingredient` – wurde nach längerer
Auseinandersetzung verworfen und ist als Ausweichweg dokumentiert. Drei meiner Gegenargumente
haben nicht gehalten: (a) ADR-S083-1/-2 sind Sequenzierungs-, keine Grundsatzentscheidungen und
verbieten keine Verzweigungen; (b) die toten `Unknown`-Arme sind über `SumType.Unreachable<T>()`
abgedeckt, dessen Pattern (ADR-S040-1) und dessen äquivalenter Mutant (ADR-S018-2) längst
entschieden sind – die Kosten sind Schreibarbeit, kein Stryker-Problem; (c) der Vergleich mit
`Guid.Empty` war falsch, weil in-band-Sentinel und out-of-band-Union kategorial verschieden sind.
Dazu ein Argument *für* den Union-Typ, das erst in der Diskussion auftauchte: US-306 verlangt
Schreiben ohne erreichbares Backend (ADR-S000-13, ADR-S112-4) bei serverseitiger ID-Vergabe
(ADR-S030-1) – eine Phase ohne Server-ID ist dokumentiert absehbar.

## E4 – OQ-Grammatik (war OQ-S094-1)

Die Frage selbst ist nicht entschieden, sondern terminiert: Der dokumentierte Wiederaufgreif-Trigger
ist nicht eingetreten, das Alter allein rechtfertigt keine Vorlage. `Fällig: S140` als Backstop
gesetzt. Der tragende Ereignis-Trigger lässt sich noch nicht ausdrücken, weil `Fällig` bei OQ nur
eine Session-Nummer kennt; beschlossen ist, dass das Feld die Anker-Grammatik aus
`.claude/scripts/td_anchors.py` übernimmt (Modul wiederverwenden, nicht kopieren) und die Frage
dann auf `Phase:V1` steht. Zusätzlich soll das `open-questions`-Modul der `session-agenda.py`
(heute `STUB`) die fälligen Fragen im Volltext vorlegen.

---

## Aufgedeckt: Wegwerf-Id in `ToDomain()`

Der schwerste Einzelbefund der Session entstand aus der Frage, welche `IngredientId` eine noch
nicht angelegte Zutat hat. Antwort: keine – aber `IngredientsEndpoints.cs:135` erzeugt trotzdem
eine per `Guid.CreateVersion7()`, weil `Ingredient.Create` eine verlangt. Der Restore-Pfad
dokumentiert das ausdrücklich (`:240`: „die dabei … erzeugte Id … wird nie gelesen"). Ein illegaler
Zustand wird routinemäßig erzeugt und verworfen; der getypte ID-Wrapper ist dabei nicht die Lösung,
sondern das Werkzeug, das ihn sichtbar macht. Festgehalten in TD-S118-1.

## Verworfen

Ein Check „OQ-Eintrag zitiert eine Guideline → verdächtig" wurde erwogen und verworfen: einmaliges
Vorkommen, kein Schaden, und der Bestand von vier OQ-Einträgen ist zu klein, um Treffer gegen
Fehlalarme abzuwägen (User-Entscheid).

## Learnings & Beobachtungen

- **LL-S118-1** – Eine Fehlablage erbt die Wiedervorlage ihres Zielorts, nicht die ihres Inhalts.
- **OBS-S118-1** – TD-Einträge mit `Fällig: jetzt` werden von Hand in `AGENT_MEMORY.md` dupliziert,
  statt dort erzeugt zu werden; aus einer Nachfrage des Users beim Abschluss.
- **OQ-S083-1** und **OQ-S083-2** entfernt (entschieden → TD-S118-1, TD-S118-2 und die
  Verankerungsarbeit aus E1/E2). **OQ-S094-1** bleibt mit Backstop-Termin.
- Mehrere meiner Analysen wurden vom User korrigiert und sind in obiger Form das Ergebnis dieser
  Korrekturen – im Einzelnen: der angebliche Taxonomie-Mangel in `process.md` (E1), die Begründung
  für getypte IDs (Regelbuchstabe statt Nutzen), der Geltungsbereich der Primitive-Obsession-Regel,
  und drei Argumente gegen den Union-Typ (E3).
