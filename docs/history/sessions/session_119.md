# Session 119 – 2026-08-13/15

**Phase:** SKELETON | **Art:** Verankerung der S118-Beschlüsse E1, E2 und E4 (Prozess/Doku, kein Produktionscode)

Über drei Arbeitstage. Der erste Teil (13./14.) endete blockiert an einer Entscheidung, die dem
User zu spät am Tag vorlag; der zweite (15.) hat sie aufgelöst und die drei Beschlüsse zu Ende
verankert. Beschluss E3 (ID-Modellierung) blieb unberührt – er ist reine Codearbeit.

---

## E1 – Ablage-Taxonomie ADR/TD/OQ: abgeschlossen

- `CLAUDE.md`: Sektion „Ablage: ADR, TD oder offene Frage?" – kanonische Fassung der drei
  Trennschnitte, des operativen Tests, der Hybrid-Regel und des Lifecycles. Plus Navigations-Zeile.
- Aufnahmebedingung in die Header von `adr.md`, `tech-debt.md` und `open-questions.md` (bei OQ
  zusätzlich negativ formuliert). Alle drei verweisen für die Abgrenzung auf `CLAUDE.md`.
  Schlüsselreihenfolge erhoben statt angenommen: In 21 von 21 Dokumenten mit Header-Block steht
  `wann-lesen` zuerst.
- **`check-adr-capture.py`** gebaut und in `dispatch-edit-write.py` registriert: blockt
  Aufschub-Vokabular in einem **neu** erfassten `### ADR-`-Eintrag. Bestandseinträge bleiben
  änderbar, sonst wäre Aufräumen unmöglich. Escape: `adr-ok` (bewusst eintragsweit, nicht
  zeilenweise wie `ref-ok` – Aufschub-Vokabular verteilt sich über den Fließtext).
- **Bestand bereinigt:** ADR-S083-1 → TD-S083-5 (neu), ADR-S083-2 → in TD-S101-1 aufgegangen.
  Beide waren Hybride ohne terminalen Rest. Fünf Code-Referenzen umgehängt
  (`IngredientsEndpoints.cs`, drei Dateien in `Client/src/hooks/`), dazu fünf Doku-Stellen.

**Nebenbefund mit Folge:** Der TD-Header lehrte in Regel 5 das verbotene Muster – „Ausnahme als
ADR dokumentieren (so ADR-S083-2 für TD-S101-1)" beschrieb genau einen Hybrid. Regel 5 sagt jetzt:
Eine dauerhafte Ausnahme per ADR **löst den TD-Eintrag auf**; eine ADR, die einem Eintrag nur
erlaubt zu warten, gibt es nicht. Gleichlautend im Fehlertext von `check-td-capture.py`.

## E2 – Domänentyp und Constraint-Typ: Prinzip verankert, Code offen (TD-S118-2)

`coding-guideline-csharp.md` §2 trägt die **Drei-Ebenen-Regel** (Constraint-Typ / Domänentyp /
Entity, mit Ort und `Create()`-Signatur je Ebene) und die fünf Regeln aus S118 E2. Verweis aus
`architecture.md` §2 gesetzt.

**Entschieden: ADR-S119-1 – Variante A.** Eine parametrisierte Einschränkung („max. N Zeichen")
wird Teil des Typs (`Bounded<NonEmpty<TrimmedString>, Max30>`), nicht ein `const` im Domänentyp.
Der Agent hatte B empfohlen (null neue Typen, Fehlerunterscheidung am Ort der Prüfung); der User
entschied A, weil ein Typ ein Mechanismus ist und eine opt-in-Prüfzeile Disziplin – und bei einem
**neuen** Domänentyp existiert das Szenario noch nicht, das die vergessene Zeile fangen würde.
Beide Varianten stehen unten im Volltext.

**Aus der Diskussion mitgenommen:** Regel 2 trug ein kaputtes Beispiel („`ConversionFactor` ist
kein `Unit`" – war nie eine Rolle *von* `Unit`); ersetzt durch `Amount`/`ConversionFactor` über
demselben `float > 0`-Constraint, mit dem Verhalten unter Operationen als Test
(`Amount × ConversionFactor = Amount` sinnvoll, `Amount + ConversionFactor` Unsinn). Regel 2 trägt
jetzt die stärkere Begründung (mehrere Typen fürs selbe Konzept verteilen dessen Regeln auf mehrere
**Änderungsorte**) statt „die Rolle steckt im Feldnamen".

**Kanonisches Beispiel korrigiert** – es widersprach §2 und §68 derselben Datei (`Create(Guid id, …)`)
und ist jetzt auf Domänentypen umgestellt. Dabei aus User-Einwänden zusätzlich behoben: der Write-Pfad
fehlte vollständig (nur der fail-fast-Read-Pfad war gezeigt, wer danach baut, verletzt ADR-S090-1);
`MapError` ist bei wechselndem Fehlertyp nicht inferierbar, das Beispiel war nie kompilierbar;
Zeile 209 verlangte `Domain.Create(dto)` gegen die eigene Dependency Rule. Der Read-Pfad sammelt
jetzt ebenfalls – Empfänger ist das Log bzw. der 500-Detailtext (ADR-S083-1/-S039-3), wer eine
korrupte Zeile repariert, braucht alle kaputten Felder auf einmal.

**ADR-S119-2 – `Collect` als Applicative-Kombinator, ein Overload je Arity.** Der Bestand behilft
sich mit `ErrorOrEmpty()` + `MapError(_ => errors)`: Der Fehler wird aus dem `OneOf` ausgepackt
(verkapptes `.AsT1`) und der Fehlerkanal am Ende durch parallel berechneten Zustand ersetzt – beides
gegen `csharp-rop.md`. `Bind` kann strukturell nicht sammeln. Verworfen: Currying + ein einzelnes
`Apply` (eine Signatur statt N, verlagert die Boilerplate aber an jeden Aufrufort),
LINQ-Query-Syntax (`SelectMany` ist monadisch, kann kein Applicative sein), Tupel-Akkumulation
(verschachtelt zu `((a,b),c)`, C# erlaubt keine Dekonstruktion in Lambda-Parameterlisten),
`params`-Arrays (verlieren die Typen).

## E4 – OQ-Anker-Grammatik: abgeschlossen

- `open_questions.py` liest `**Fällig:**` über `td_anchors.py` – **wiederverwendet, nicht kopiert**.
  Vorher kannte es nur `S<NNN>`; `Phase:V1` oder ein Vertipper fielen still auf die Alters-Regel
  zurück. Zwei bewusste Abweichungen von der TD-Auswertung: `jetzt` erzeugt hier einen Grund (OQ hat
  keinen zweiten Kanal über AGENT_MEMORY), und ohne das Feld greift die Alters-Regel (bei TD ist es
  Pflicht).
- Das `open-questions`-Modul der `session-agenda.py` war `STUB` und damit wirkungslos – es erschien
  nur als Einzeiler im Nachrang-Bereich und setzte voraus, dass jemand die Datei aufschlägt. Jetzt
  `ZUSTAND` mit **Fragetext und Fälligkeitsgrund** im Startkontext. Nicht der ganze Eintragskörper:
  der trägt Herleitung und Recherche und würde den Start dominieren.
- **`check-oq-capture.py`** gebaut (User-Einwand: ein Vertipper gehört zur Schreibzeit gemeldet,
  nicht erst beim nächsten Session-Start). Kernlogik ist `td_anchors.validiere`. Regel: Feld fehlt →
  in Ordnung; Feld gesetzt → muss tragen, denn ein gesetzter Anker unterdrückt die Alters-Regel.
- Bestandseinträge nachgezogen: OQ-S094-1 auf `Phase:V1, S140` (so in S118 beschlossen),
  OQ-S119-2 auf `US-602, S128`.

## Weitere Mechanik

- **`check-dangling-refs.py`** (User-Wunsch): blockt das Löschen eines TD-/OQ-Eintrags, solange im
  Repo noch auf die ID verwiesen wird, und listet die Fundstellen auf. Schließt die Lücke, dass
  `ref-ok` ein stummes Opt-out war – einmal gesetzt, nie wieder geprüft (Bestandsfall: zwei
  ADR-Stellen verweisen mit `ref-ok` auf TD-S089-1). Spiegelt `decisions.py check`, das dasselbe
  für die stabile Richtung tut. Escape: `dangling-ok`.
- **`checks/primitives.py`** umgebaut: Der Parameter-Check war nur ein Hinweis und feuerte bei
  *jeder* Datei; der Property-Check griff in `Server/Domain/` gar nicht, weil er nur `{ get; }`
  matchte und Domain-Typen durchweg `=>` nutzen. Jetzt blockierend für **Entities**, unterschieden
  an der `Value`-Property. Der Auftrag lautete „rohes Guid/string/int in `Server/Domain/` blocken" –
  das hätte `IngredientName.Create(string)` mitblockiert, also genau die beschlossene Sollform;
  umgesetzt wurde die Absicht, nicht der Buchstabe.
- **Lesekonvention für Code-Beispiele** in `coding-guideline-general.md` verankert: Ein Beispiel
  zeigt eine Regel, nicht den Bestand und keinen Bauauftrag. Es kann Typen nennen, die es (noch)
  nicht gibt; eine 1:1-Umsetzung kann gegen KISS und die Szenario-Pflicht verstoßen; und es kann
  überholt sein – dann gilt die Regel. Ersetzt den Plan, „Phantom-Typen" aus der Doku zu tilgen:
  Namen zu streichen hätte nur diesen Fall behoben, während jedes künftige Beispiel dasselbe
  Problem neu erzeugt.

## Review (drei Auditoren über das Gesamt-Delta)

Fünf ❌, alle bestätigt und behoben. Die zwei schwersten:

- **`primitives.py` sperrte `IngredientValidationError.cs` vollständig** – verifiziert, nicht
  geglaubt. Sum-Types (ADR-S018-1) sind eine dritte Kategorie, die die Drei-Ebenen-Regel nicht
  abbildet: Ihre Payload-Subtypen führen Primitives bewusst. Jetzt ausgenommen.
- **`check-adr-capture.py` ohne `re.IGNORECASE`** – „Aufgeschoben wird die Migration." passierte den
  Hook. Deutsche Entscheidungsprosa schreibt satzinitial groß; die eigene Gegenprobe hatte
  kleingeschrieben getestet und das nicht erwischt.

Zwei Findings abgelehnt und begründet: die `CHECKS`-Liste auf Listenvergleich umzustellen
(Reihenfolge ist kosmetisch – stattdessen den irreführenden Docstring korrigiert), und `zunächst`
als Aufschub-Marker zu behalten (erzählt meist Vorgeschichte – die Bauform jedes
„Verworfen:"-Abschnitts; stand auch nie in CLAUDE.mds Katalog).

Aus dem Review geparkt statt gebaut: OBS-S119-2 (Boilerplate über inzwischen sechs Hooks; dazu
Beispiel-IDs im Tooling, die beim Erledigen von TD-S089-1 Rauschen erzeugen werden) und OQ-S119-4
(die TS-Guideline schreibt `ValidationError = { message: string }` vor – Gegenteil von Regel 5;
nicht automatisch falsch, weil das Frontend laut ADR-S112-4 nicht validiert).

## Learnings & Beobachtungen

- **OBS-S119-1** – Der Deny-Text von `check-bash-permission.py` lenkt in Einmalscripte, statt die
  Werkzeugfrage zu stellen.
- **OBS-S119-2** – Boilerplate über sechs PreToolUse-Hooks; Beispiel-IDs im Tooling kollidieren mit
  dem neuen Dangling-Check.
- **OQ-S119-4** neu, **OQ-S119-1** entfernt (entschieden → ADR-S119-1/-2 und TD-S118-2).
- Keine LL-Einträge – kein konkreter schlechter Ausgang, den die Review-Findings nicht bereits als
  behobene Mechanik-Lücken tragen (User-Entscheid beim Abschluss).

---

## Volltext zur Constraint-Parametrisierung (entschieden als ADR-S119-1): die beiden Varianten

Beispiel in beiden Fällen: `name` max. 30, `defaultUnit` max. 20 (ADR-S051-3), mit der von
ADR-S051-2 geforderten Unterscheidung `NameEmpty` ≠ `NameTooLong`.

### Variante A – parametrisierte Einschränkung im Typ (**gewählt**)

```csharp
// ─── Server/Types/StringConstraints.cs ──────────────────────────────────────
internal enum StringViolation { Empty, TooLong }

internal interface IStringConstraint<TSelf> where TSelf : IStringConstraint<TSelf>
{
    static abstract OneOf<TSelf, StringViolation> Create(string input);
    string Value { get; }
}

internal interface IMaxLength { static abstract int Value { get; } }

// ADR-S051-1: trimmen vor der Validierung, getrimmten Wert speichern
internal readonly record struct TrimmedString : IStringConstraint<TrimmedString>
{
    private readonly string _value;
    // Stryker disable once NullCoalescing,String : default(T) guard (ADR-S041-9)
    public string Value => _value ?? throw new InvalidOperationException("Uninitialized");
    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public TrimmedString() => throw new InvalidOperationException("Uninitialized");
    private TrimmedString(string value) => _value = value;

    public static OneOf<TrimmedString, StringViolation> Create(string input) =>
        new TrimmedString(input?.Trim() ?? "");
}

internal readonly record struct NonEmpty<TInner> : IStringConstraint<NonEmpty<TInner>>
    where TInner : IStringConstraint<TInner>
{
    private readonly TInner _inner;
    public string Value => _inner.Value;                       // wirft transitiv
    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public NonEmpty() => throw new InvalidOperationException("Uninitialized");
    private NonEmpty(TInner inner) => _inner = inner;

    public static OneOf<NonEmpty<TInner>, StringViolation> Create(string input) =>
        TInner.Create(input).Bind<TInner, NonEmpty<TInner>, StringViolation>(inner =>
            inner.Value.Length == 0
                ? (OneOf<NonEmpty<TInner>, StringViolation>) StringViolation.Empty
                : new NonEmpty<TInner>(inner));
}

internal readonly record struct Bounded<TInner, TMax> : IStringConstraint<Bounded<TInner, TMax>>
    where TInner : IStringConstraint<TInner> where TMax : IMaxLength
{
    private readonly TInner _inner;
    public string Value => _inner.Value;
    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public Bounded() => throw new InvalidOperationException("Uninitialized");
    private Bounded(TInner inner) => _inner = inner;

    public static OneOf<Bounded<TInner, TMax>, StringViolation> Create(string input) =>
        TInner.Create(input).Bind<TInner, Bounded<TInner, TMax>, StringViolation>(inner =>
            inner.Value.Length > TMax.Value
                ? (OneOf<Bounded<TInner, TMax>, StringViolation>) StringViolation.TooLong
                : new Bounded<TInner, TMax>(inner));
}

internal readonly struct Max30 : IMaxLength { public static int Value => 30; }
internal readonly struct Max20 : IMaxLength { public static int Value => 20; }
```

```csharp
// ─── Server/Domain/IngredientName.cs ────────────────────────────────────────
internal readonly record struct IngredientName
{
    private readonly Bounded<NonEmpty<TrimmedString>, Max30> _value;   // Grenze steht im Typ
    public string Value => _value.Value;

    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public IngredientName() => throw new InvalidOperationException("Uninitialized");
    private IngredientName(Bounded<NonEmpty<TrimmedString>, Max30> value) => _value = value;

    public static OneOf<IngredientName, IngredientValidationError> Create(string input) =>
        Bounded<NonEmpty<TrimmedString>, Max30>.Create(input)
            .MapError(v => v switch
            {
                StringViolation.Empty   => IngredientValidationError.NameEmpty,
                StringViolation.TooLong => IngredientValidationError.NameTooLong,
                _ => SumType.Unreachable<IngredientValidationError>(),   // enum-Default-Arm
            })
            .Map(v => new IngredientName(v));
}
// Unit analog mit Bounded<NonEmpty<TrimmedString>, Max20>
```

### Variante B – Trägertyp + `const` im Domänentyp (verworfen)

```csharp
// ─── Server/Types/NonEmptyTrimmedString.cs ──────────────────────────────────
// unverändert wie im Bestand – keine neue Datei
```

```csharp
// ─── Server/Domain/IngredientName.cs ────────────────────────────────────────
internal readonly record struct IngredientName
{
    // ADR-S051-3: max. 30 Zeichen, nach Trimming gemessen.
    private const int MaxLength = 30;

    private readonly NonEmptyTrimmedString _value;
    public string Value => _value.Value;                       // wirft transitiv

    // Stryker disable once Statement,String : parameterless ctor (ADR-S041-9)
    public IngredientName() => throw new InvalidOperationException("Uninitialized");
    private IngredientName(NonEmptyTrimmedString value) => _value = value;

    public static OneOf<IngredientName, IngredientValidationError> Create(string input) =>
        NonEmptyTrimmedString.Create(input)
            .MapError<NonEmptyTrimmedString, Error, IngredientValidationError>(
                _ => IngredientValidationError.NameEmpty)
            .Bind<NonEmptyTrimmedString, IngredientName, IngredientValidationError>(v =>
                v.Value.Length > MaxLength
                    ? (OneOf<IngredientName, IngredientValidationError>) IngredientValidationError.NameTooLong
                    : new IngredientName(v));
}
// Unit analog mit MaxLength = 20
```

### Vergleich

| | A (gewählt) | B (verworfen) |
|---|---|---|
| Neue Typen | 5 (`TrimmedString`, `NonEmpty<T>`, `Bounded<T,TMax>`, `Max30`, `Max20`) + Enum | **0** |
| Suppressions | 6 (Träger) + 1 je Domänentyp + 1 Enum-Default-Arm | 2 (bestehend) + 1 je Domänentyp |
| `MaxLength` vergessbar? | **nein** – der Feldtyp deklariert sie | ja – eine Zeile in `Create()` |
| Grenzwert 30→40 | Marker umbenennen (Grenzwert = Typidentität) oder Marker je Feld (O(F)) | ein Token |
| Dritte Property mit max 30 | 0 neue Typen | 0 neue Typen |
| Erstes Feld mit max 25 | +1 Marker | 0 |
| „Welche Regel riss?" | Violation durch alle Generics reichen, am Domänentyp auffalten | direkt am Ort der Prüfung |
| Abstand zum Bestand | Neuentwurf | `ValidateField` wandert aus dem Endpoint in den Domänentyp |

Die Zahlen sind **gerechnet, nicht gemessen**: „2 Suppressions je `readonly record struct`"
stammt aus dem Guideline-Beispiel §3, nicht aus einem Stryker-Lauf.

## Verworfene Zwischenentwürfe (nicht erneut aufrollen)

- **`StringRule` als fluent Prädikat-Pipeline** (`For(x).NonEmpty().MaxLength(30).Build()`).
  Erlaubt alle Achsen-Kombinationen durch Weglassen, scheitert aber an der **Vergessbarkeit**:
  jeder Schritt ist opt-in, ein vergessenes `.NonEmpty()` erlaubt still leere Werte, und bei einem
  neuen Domänentyp gibt es noch kein Szenario, das es fängt.
- **`For(string? input) => new(input ?? "", …)`** – bildet Abwesenheit auf Leerheit ab, ein
  In-band-Sentinel und damit eine Verletzung von E2 Regel 4. Abwesenheit gehört an die
  DTO-Grenze (dort als TD-S090-3 erfasst), nicht in die Prüfkette.
- **`CheckedString` als neutraler Träger** allein für den `default(T)`-Guard – spart über vier
  Felder nur 8→6 Suppressions. Zu dünn für einen eigenen Typ und ein eigenes Konzept.
- **NRT als Ersatz für den `default(T)`-Guard** – funktioniert nicht: `default(T)` bei structs
  null-initialisiert auch ein als non-nullable deklariertes Feld, ohne Compiler-Warnung.

## Recherche-Ergebnisse

- **Zwei Schulen.** *Refined Types* (Haskell/Scala `refined`, Rust `nutype`) komponieren Prädikate
  typseitig. *DDD/Constrained Types* (Wlaschin, *Domain Modeling Made Functional*; Khorikov) machen
  einen Typ je Domänenkonzept und teilen nur Validierungs**funktionen**.
- **Wlaschin komponiert nicht.** `createString fieldName ctor maxLen str` prüft null/empty **und**
  maxLen fest verdrahtet; „leer erlaubt" ist eine zweite Funktion (`createStringOption`). Zwei
  fixe Bündel, keine freie Kombination.
- **C# hat keine const generics.** Nur Draft (`dotnet/csharplang#7508`, seit 2023, MVP vorhanden,
  für keine Version eingeplant). C# 15 enthält sie nicht. Deshalb braucht Variante A je Grenzwert
  einen Marker-Typ. Bemerkenswert: Rust *hat* const generics, und `nutype` nutzt trotzdem
  Proc-Macro-Codegen statt typseitiger Komposition – das Ergonomieproblem ist keine C#-Schwäche.
- **C# 15 / .NET 11** bringt `union`, `closed`-Hierarchien, Collection-Expression-Argumente,
  Extension-Indexer, labeled `break`/`continue`, Memory-Safety. GA November 2026. Relevanz für
  `SumType.cs` und E3: siehe OQ-S119-3.
