# Session 120 – 2026-08-17/18

**Phase:** SKELETON | **Art:** Codearbeit – Beschluss E3 aus S118 umgesetzt (TD-S118-1 und TD-S118-2)

Die Session löste zuerst die letzte offene Entscheidung am Fehlermodell (OQ-S119-2 → ADR-S120-1)
und setzte danach beide TD-Einträge in einem Durchlauf um. Die Reihenfolge war erzwungen: Ein
zwischen Zutat, Rezept und Einkaufsliste geteiltes `Unit` kann keinen entitätsspezifischen
`IngredientValidationError` liefern – ohne die Antwort wäre `Unit` zweimal gebaut worden.

Ablauf über den Skill `implementing-scenario`, mit einer benannten Abweichung: Es gab keinen
Gherkin-Lauf. Das ATDD-Gate (Schritt 0.1) wurde durch die fordernden Quellen ersetzt – TD-S118-1/-2,
ADR-S119-1/-2, ADR-S120-1. Die Umsetzung lief in einem Backend-Implementer statt schichtweise,
weil kein Frontend-Verhalten betroffen war; die Reviewer blieben eigene Subagenten.

---

## A – OQ-S119-2 entschieden: ein Fehlertyp je Domänentyp (ADR-S120-1)

Drei Varianten wurden dem User mit je einem mehrfeldrigen Codebeispiel vorgelegt. Gewählt: **V2**
– jeder Domänentyp liefert seinen eigenen, **feldagnostischen** Fehlertyp
(`IngredientName.Create` → `OneOf<IngredientName, IngredientNameError>`), der Feldbezug entsteht
erst an der API-Grenze, die statisch weiß, welches Feld sie gerade validiert.

Ausschlaggebend war die Begründung des Users: V1 (Constraint-Violation direkt durchreichen) zwingt
den Aufrufer, die Interna der Domänentypen zu kennen; V3 (Fehler am Entity-Typ) scheitert daran,
dass Frontend-Daten nicht immer über ein Domänen-Objekt laufen.

**Folge für den Bestand:** `Server/Domain/IngredientValidationError.cs` ist gelöscht – der erste
Sum-Type des Repos (S091) verliert seine vier Feld×Prüfung-Fälle an die Domänentypen. Übrig bliebe
allein `NameDuplicate`, ein Fehler, den kein Domänentyp erzeugen kann, weil er die Datenbank
braucht; er entsteht im Endpoint direkt als `FieldError`.

## B – TD-S118-2: Domänentypen für Name und Einheit

Neu in `Server/Types/`:

- **`StringConstraints.cs`** – der Baukasten aus ADR-S119-1: `StringViolation` (`Empty`,
  `TooLong`), `IStringConstraint<TSelf>` (CRTP mit `static abstract Create`), `IMaxLength`,
  `Bounded<TInner, TMax>` und die Marker `Max30`/`Max20` als `readonly struct`. Bewusst **eine**
  Datei – die Typen sind nur gemeinsam les- und änderbar.
- **`Uuid7.cs`** – nur `New()`, kein validierendes `Create`: Es gibt keine ungültige UUIDv7, die
  Kontrolle liegt vollständig beim Erzeuger.

Neu in `Server/Domain/`: `IngredientName.cs` und `Unit.cs`, jeweils mit ihrem Fehler-Enum in
derselben Datei. `Ingredient.Create` nimmt jetzt `(IngredientId, IngredientName, Unit)` und ist
mit ungültigen Werten nicht mehr aufrufbar.

**`OneOfExtensions.Collect` (Arity 2)** ersetzt die ausgepackte Fehlersammlung im Endpoint. Das
ist der applikative statt des monadischen Weg: Beide Felder werden ausgewertet, auch wenn das
erste schon fehlschlägt – Voraussetzung dafür, dass ein 422 weiterhin beide Feldfehler trägt
(ADR-S090-1).

**Nicht killbarer Mutant – Träger-Liste geändert.** ADR-S119-1 sah zwei orthogonale Träger vor
(`TrimmedString` normalisierend, `NonEmpty<TInner>` prädizierend). Beim Umbau zeigte sich, dass
diese Trennung einen nicht killbaren Mutanten erzeugt: Ein rein normalisierender Träger muss im
JSON-`null`-Fall einen *Wert* liefern (`""`), und `""` aus `null` ist von `""` aus `""` nicht
unterscheidbar. Umgesetzt wurde deshalb der ungetrennte `NonEmptyTrimmedString`, in dem die
Leer-Entscheidung im selben Schritt fällt und einen **Fehler** liefern kann, dessen Entfernung
über HTTP sofort beobachtbar ist. Eine Suppression schied aus – der Zweig ist erreichbar, das
wäre eine Testlücke gewesen, keine Unerreichbarkeit (ADR-S041-9 greift nicht). ADR-S119-1 trägt
die geänderte Träger-Liste, die Mutanten-Begründung und den additiven Erweiterungspfad; der
User hat den Verzicht auf die Trennung mit KISS begründet und zugleich benannt, wann sie fällig
wird – beim ersten Feld, das getrimmt werden muss, aber leer sein darf.

## C – TD-S118-1: getypte `IngredientId`

`Server/Domain/IngredientId.cs` als `readonly record struct` über `Uuid7`, zwölf Zeilen. Der
ursprünglich in TD-S118-1 vorgesehene Sum-Type entfiel: Ein Sum-Type mit genau einem Fall trägt
nichts, und die Id hat keinen Fehlerfall (siehe `Uuid7` oben). `ToDomain()` erzeugt keine
ungelesene Wegwerf-Id mehr.

## D – Umbenennung `DefaultUnit` → `BaseUnit`

Vom User angestoßen, nachdem ein Review-Finding die Bezeichnung anzweifelte: Das Glossar führt den
Begriff als **Basiseinheit (Base Unit)**, der Code hieß seit dem Skeleton `DefaultUnit`. Konsistent
durchgezogen über Domäne, DTOs, DB-Typ, Endpoint, JSON-Feldname, Frontend (10 Stellen), E2E-Tests
und die betroffenen ADR-Volltexte (ADR-S068-1, ADR-S090-1, ADR-S108-2, ADR-S111-1/-3). Das UI-Label
bleibt „Einheit" – so schreibt es das Glossar ausdrücklich vor, solange es keine Umrechnung gibt.
Ausgeführt von einem frischen Implementer statt vom bisherigen (Cache-Miss wäre teurer gewesen).

## E – Migration neu generiert, Hand-SQL gerettet

Die Schema-Änderung erzwang eine Neugenerierung von `InitialCreate`
(`20260721191200` → `20260817125333`). Der funktionale Unique-Index auf `LOWER(name)` lebt dort
als handgeschriebener SQL-Block – EF Core kann ihn nicht ableiten und hätte ihn beim Neugenerieren
ersatzlos verloren. Er wurde zeichengleich übertragen. Der Vorfall hinterließ zwei Spuren: einen
Warnhinweis in `dev-workflow.md` (der Prozess ist Drop+Recreate, nicht Migrations-Kette – siehe
LL-S120-3) und **TD-S120-3**, das die Fehlerquelle beseitigen statt dokumentieren will.

## F – Suppressions-Politik: `.editorconfig` aufgeräumt und begrenzt

Der User stellte die von mir vorgenommenen `.editorconfig`-Änderungen infrage. Die Prüfung ergab,
dass ich inkonsistent gehandelt hatte: Die Fehler-Enums hatte ich in eigene Dateien gezwungen,
während ich `StringConstraints.cs` eine Datei-Suppression zugestand. Revidiert – die Enums wanderten
zurück in ihre Domänen-Dateien mit einer **Zeilen**-Suppression (`MA0048`), `StringConstraints.cs`
behielt die Datei-Suppression mit Begründung. Entscheidungsregel des Users: Datei-Suppression nur,
wenn sie eine Eigenschaft der ganzen Datei ist; wandert das Konstrukt ohnehin zurück in seine
Klasse, ist die Zeilen-Suppression vorzuziehen.

Mitgenommen: der tote `CA2225`-Block und der `S3060`-Block für die gelöschte
`IngredientValidationError.cs`; `CA1000` neu begründet. Die weitergehende Frage, wann eine
Suppression überhaupt in die `.editorconfig` gehört, hat der User bewusst vertagt – erfasst als
**TD-S120-5** (Regelwerk fehlt) und **TD-S120-2** (Aufräumen des Bestands), wechselseitig verankert.

## G – Review-Loop

Auditoren nach `review-code` über das gesamte Delta, mehrere Runden bis 0 ❌. Bemerkenswerte
Befunde:

- **CQ-1** deckte auf, dass `IngredientId` als Sum-Type überdimensioniert war → Abschnitt C.
- **FC-9** deckte eine echte Beobachtungslücke auf: Ob die Längengrenze vor oder nach dem Trimmen
  greift, war durch kein Szenario festgenagelt. Zwei neue Gherkin-Szenarien (Name/Einheit an der
  Grenze mit umgebenden Leerzeichen) plus die passenden E2E-Tests schließen sie. Der Weg dorthin
  ging über zwei Fehlschläge, die beide in `lessons_learned.md` stehen (LL-S120-1, LL-S120-4).
- **T3** war der Auslöser der Umbenennung aus Abschnitt D.
- **T4** war ein False Positive **meines** Prompts: ADR-S106-3 fehlte in der Auditor-Liste,
  woraufhin der Auditor 12 legitime, US-Tag-lose Infra-Tests meldete. Folge: LL-S120-2 und eine
  neue Regel im Skill `review-code` – ADR-Volltexte in den Prompt (die Auditoren haben kein Bash)
  **plus** ein Auftrag zur eigenen Grep-Gegenprobe in `adr.md`.

Ein früher vorgeschlagenes Löschen der TD-Einträge wies der User zurück, solange die Arbeit nicht
fertig war; TD-S118-1/-2 sind erst nach der Verifikation entfernt worden.

## H – Verifikation

| Ebene | Ergebnis |
|---|---|
| Backend | 53/53 Tests, Stryker 100 % (83 valide Mutanten, 0 Survivors) |
| Frontend | 40/40 Tests, Stryker 100 % |
| E2E | 41/41 Tests |

Alle Test-Freigabe-Audits meldeten „unverändert seit Freigabe". Der E2E-Lauf war zunächst blockiert,
weil Postgres nicht lief und `docker compose` mangels Compose-Plugin nicht startbar war – der User
hat die Datenbank selbst hochgefahren. Er ist der einzige Beleg dafür, dass die parallel umgebauten
Schichten zusammenpassen (Frontend sendet `baseUnit`, Backend erwartet `baseUnit`).

## I – Doku, Guidelines, Tracker

- **`coding-guideline-csharp.md` §2:** Regel 5 ergänzt; das Beispiel auf `IngredientNameError` /
  `Bounded<NonEmptyTrimmedString, Max30>` umgestellt; der offene Punkt am Fehlertyp ist mit
  ADR-S120-1 aufgelöst; der „Sollform"-Absatz auf einen reinen Lesekonventions-Verweis gekürzt.
- **`docs/open-questions.md`:** OQ-S119-2 entfernt, OQ-S119-4 von `S132` auf `jetzt` umgehängt
  (der tragende Trigger ist mit ADR-S120-1 gefallen), TD-Verweis in OQ-S119-3 aufgelöst.
- **`docs/tech-debt.md`:** TD-S118-1/-2 entfernt; TD-S090-3 um zwei Testlücken erweitert;
  TD-S120-1 bis -5 neu.
- **`dev-workflow.md`/`tdd-process.md`:** jscpd-Befehl korrigiert, Migrations-Warnhinweis ergänzt.
- **`session-agenda.py`:** Kommentar-Referenz auf OQ-S119-2 aufgelöst (die Frage existiert nicht mehr).

## J – Learnings und Beobachtungen

- **LL-S120-1** – 100 % Mutation Score als Beleg für eine gepinnte Trim-Eigenschaft gelesen;
  Wiederholung von LL-S092-1, zu dem nie eine Countermeasure entstand.
- **LL-S120-2** – Auditor-Prompt verlangte eine Gegenprobe per Bash, obwohl die Auditoren kein
  Bash-Tool haben.
- **LL-S120-3** – Mein Auftrag an den Implementer widersprach `dev-workflow.md`; nur sein
  Widerspruch verhinderte den Schaden.
- **LL-S120-4** – Eine Gegenprobe vorgeschlagen, die die beiden Varianten mathematisch gar nicht
  unterscheiden kann.
- **OBS-S120-1** *(User)* – Offene Fragen sind der einzige Tracker ohne Pflege-Werkzeug.
- **OBS-S120-2** *(User)* – Fünf Eintrags-Tracker, drei verschiedene Pflege-Strategien.
- **OBS-S120-3** – Der `qa-check`-Übergabe-Hash erzwingt einen zweiten Stryker-Volllauf nach
  jedem Aufräumen.
- **OBS-S120-4** – Für Textersetzung über mehrere Dateien gibt es kein Werkzeug.

Volltext jeweils in `docs/kaizen/lessons_learned.md` bzw. `docs/kaizen/observations.md`.
