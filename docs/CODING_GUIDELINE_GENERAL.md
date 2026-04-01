# Allgemeine Coding-Guideline (sprachunabhängig)

<!--
wann-lesen: Vor jedem Schreiben von Produktionscode (C# oder TypeScript) – Pflichtlektüre, kurz
kritische-regeln:
  - KISS: Keine Abstraktion für hypothetische Zukunft
  - Nur Begriffe aus GLOSSARY.md für Domänenkonzepte
  - Max. ~20 Zeilen pro Methode/Funktion
  - Kein toter Code (auskommentiert, ungenutzte Importe)
-->

## Inhalt

| Abschnitt | Inhalt | Wann lesen |
|-----------|--------|------------|
| KISS | Einfachste Lösung wählen, keine vorzeitigen Abstraktionen | Immer – vor jedem Feature |
| Naming | Glossar-Begriffe, selbsterklärende Namen, Kommentare = Warum | Immer – beim Benennen von Typen/Methoden |
| Komplexität & Refactoring | Max. ~20 Zeilen/Methode, max. 3 Verschachtelungsebenen, kein toter Code | Bei Umstrukturierung oder wachsenden Methoden |
| Übergreifende Paradigmen | Tabelle: Immutability, Value Objects, ROP, Pure Functions – C# vs. TypeScript | Als Orientierung vor dem Lesen der sprachspezifischen Guideline |
---

Diese Grundprinzipien gelten für **alle** Sprachen im Projekt (C# und TypeScript/React).
Sprachspezifische Umsetzungen: `docs/CODING_GUIDELINE_CSHARP.md` · `docs/CODING_GUIDELINE_TYPESCRIPT.md`

---

## KISS – Keep It Simple

Wähle immer die einfachste Lösung, die den Anforderungen genügt.

- Keine Abstraktionen für hypothetische Zukunft.
- Keine Überabstraktion, die mehr als eine Aufgabe vereinheitlichen soll.
- Drei ähnliche Code-Stellen sind besser als eine voreilige Abstraktion.
- Wenn eine Lösung erklärt werden muss, weil sie clever ist: Vereinfachen.
- Die richtige Menge Komplexität ist das Minimum, das für die aktuelle Aufgabe nötig ist.

---

## Naming

- Verwende ausschließlich Begriffe aus `docs/GLOSSARY.md` für Domänenkonzepte.
- Variablen-, Methoden- und Typnamen sollen selbsterklärend sein – kein Name, der einen erklärenden Kommentar benötigt.
- Kommentare beschreiben das **Warum**, nicht das **Was**. Code erklärt das Was.

---

## Komplexität & Refactoring

- Eine Methode / Funktion hat maximal ~20 Zeilen. Größer → Refactoring-Kandidat.
- Verschachtelung tiefer als 3 Ebenen → Pattern Matching oder Extraktion erwägen.
- Duplikate oder Copy-Paste-Code → gemeinsamen Helper extrahieren.
- Kein toter Code (auskommentierter Code, ungenutzte Variablen/Importe).

---

## Abhängigkeiten

Externe Pakete (npm, NuGet) nur hinzufügen wenn sie in `docs/DEPENDENCIES.md` gelistet sind. Vor jeder Erweiterung der Allowlist: User konsultieren (5-Punkte-Begründung laut `DEPENDENCIES.md`). Hooks erzwingen diese Regel automatisch.

---

## Übergreifende Paradigmen

Diese Prinzipien gelten für den gesamten Produktionscode. Die sprachspezifischen Guidelines beschreiben die konkrete Umsetzung:

| Prinzip | C# | TypeScript |
|---|---|---|
| Immutability | `readonly record struct`, `init;` | `readonly`, `as const`, Spreading |
| Keine Primitive Obsession | Value Objects (`NonEmptyTrimmedString` etc.) | Branded Types |
| Make Illegal States Unrepresentable | Private Konstruktoren + `Create()` Factory | Discriminated Unions |
| Railway-Oriented Programming | `OneOf<T, Error<string>>` + `.Match()` | `neverthrow` `Result<T, E>` + `.match()` |
| Pure Functions | Extension Methods, keine Seiteneffekte | `src/domain/`, `src/services/` |

