"""Gemeinsames Lesen und Bewerten von Stryker-JSON-Reports.

Genutzt von `stryker-summary.py` (Ausgabe + Gate) und `qa-check.py` (Übergabe-Hash + Gate).
Die Score-Formel stand vorher in beiden Dateien wörtlich doppelt – ein Duplikat, das
auseinanderdriften kann, obwohl beide dieselbe Zahl als Gate benutzen (OBS-S108-3).

Standard-Mutation-Score (mutation-testing-elements, identisch zum HTML-Report):

    detected   = Killed + Timeout
    undetected = Survived + NoCoverage
    score      = detected / (detected + undetected)

Ignored / CompileError / RuntimeError zählen NICHT in den Nenner (eigene Buckets).
NoCoverage ist undetected: nicht ausgeführter Code senkt den Score – ein NoCoverage-Mutant
ist strenger genommen schlimmer als ein Survivor (nicht mal ausgeführt).
"""
from collections import Counter


# Erklärtext für den Null-Mutanten-Fall – an beiden Aufrufstellen identisch.
# Stryker selbst fängt diesen Fall NICHT ab: StrykerJS meldet dann „Final mutation score of NaN
# is greater than or equal to break threshold 100" und endet mit Exit 0.
NO_MUTANTS_HINT = (
    "0 valide Mutanten im Report – dieser Lauf belegt NICHTS.\n"
    "   Ein Score wird hier bewusst nicht ausgewiesen: „nichts gemessen“ ist kein „alles getötet“.\n"
    "   (Stryker selbst lässt diesen Fall durch – es rechnet einen NaN-Score gegen das Threshold.)\n"
    "   Übliche Ursachen: --mutate zeigt auf einen Pfad, den Stryker als Excluded wertet\n"
    "   (Backend: projekt-relativ, z.B. `Endpoints/Foo.cs` statt `Server/Endpoints/Foo.cs`),\n"
    "   ein Glob ohne Treffer, ein Scope, den die Config komplett ausschließt, oder eine Zieldatei,\n"
    "   deren Mutanten alle am Checker scheitern (CompileError) – sie trägt dann nichts zum Score bei."
)


def compute_metrics(files: dict) -> dict:
    """Wertet den `files`-Block eines Stryker-JSON-Reports aus.

    `score` ist None, wenn der Lauf keinen einzigen validen Mutanten enthält – dieser Fall
    hat keinen definierten Score und darf nicht als 100 % durchgehen (OBS-S108-3).
    `mutated_files` zählt nur Dateien mit mindestens einem validen Mutanten und beschreibt
    damit den tatsächlichen *Umfang* des Laufs (nicht nur sein Ergebnis).
    """
    counts: Counter = Counter()
    mutated_files = 0
    for file_data in files.values():
        file_valid = 0
        for m in file_data.get("mutants", []):
            status = m.get("status")
            counts[status] += 1
            if status in ("Killed", "Timeout", "Survived", "NoCoverage"):
                file_valid += 1
        if file_valid > 0:
            mutated_files += 1
    detected = counts["Killed"] + counts["Timeout"]
    undetected = counts["Survived"] + counts["NoCoverage"]
    total_valid = detected + undetected
    return {
        "counts": counts,
        "detected": detected,
        "undetected": undetected,
        "total_valid": total_valid,
        "mutated_files": mutated_files,
        "score": (detected / total_valid * 100) if total_valid > 0 else None,
    }


def has_no_mutants(metrics: dict) -> bool:
    """True, wenn der Lauf keinen einzigen validen Mutanten enthält (Aussagekraft = null)."""
    return metrics["total_valid"] == 0


def format_status_breakdown(metrics: dict) -> str:
    """Alle vorkommenden Mutanten-Status mit Anzahl – zeigt, WARUM ein Lauf leer blieb.

    Ohne das bliebe offen, ob gar keine Mutanten erzeugt wurden (falscher Pfad/Glob) oder ob
    sie alle in einem Nicht-Bewertungs-Bucket landeten (Ignored, CompileError).
    """
    counts = metrics["counts"]
    if not counts:
        return "   Status-Verteilung: keine Mutanten im Report."
    breakdown = ", ".join(f"{status}: {n}" for status, n in sorted(counts.items()))
    return f"   Status-Verteilung: {breakdown}"


def format_score(metrics: dict) -> str:
    """Score als Anzeige-String; ohne valide Mutanten explizit `n/a` statt einer Scheinzahl."""
    if has_no_mutants(metrics):
        return "n/a (0 valide Mutanten)"
    return f"{metrics['score']:.1f}%"


def format_scope(metrics: dict) -> str:
    """Umfangs-Zeile: WAS der Lauf abgedeckt hat (nicht nur, wie gut).

    Der Übergabe-Hash bindet den Report-*Inhalt*, nicht seinen Umfang – der Umfang muss
    darum sichtbar sein, damit ein zu eng gelaufener Report auffällt (OBS-S108-3).
    """
    return f"Umfang: {metrics['mutated_files']} Datei(en)  |  {metrics['total_valid']} valide Mutanten"


def gate_code(metrics: dict) -> int:
    """Das mechanische Mutation-Gate: 0 nur bei echten 100 % über mindestens einen Mutanten."""
    if has_no_mutants(metrics):
        return 1
    return 0 if metrics["undetected"] == 0 else 1


def short_path(full_path: str) -> str:
    """Kürzt einen Report-Pfad auf den projekt-relativen Teil."""
    normalized = full_path.replace("\\", "/")
    for anchor in ("Server/", "Server.Tests/", "src/"):
        if anchor in normalized:
            return normalized[normalized.index(anchor):]
    return normalized.split("/")[-1]


def collect_undetected(files: dict) -> tuple[dict[str, list], dict[str, list]]:
    """Sammelt Survivors und NoCoverage-Mutanten je Datei (Kurzpfad)."""
    survivors: dict[str, list] = {}
    nocoverage: dict[str, list] = {}
    for path, file_data in files.items():
        for m in file_data.get("mutants", []):
            status = m.get("status")
            if status == "Survived":
                survivors.setdefault(short_path(path), []).append(m)
            elif status == "NoCoverage":
                nocoverage.setdefault(short_path(path), []).append(m)
    return survivors, nocoverage


def format_mutant_group(by_file: dict[str, list]) -> list[str]:
    """Formatiert eine Mutanten-Gruppe (Datei → Zeile/Mutator/Ersetzung) als Ausgabezeilen."""
    lines: list[str] = []
    for file, mutants in sorted(by_file.items()):
        lines.append(f"  {file} ({len(mutants)})")
        for m in sorted(mutants, key=lambda x: x["location"]["start"]["line"]):
            lines.append(f"    Zeile {m['location']['start']['line']:>4}  {m['mutatorName']}")
            lines.append(f"           → {m.get('replacement', '?')}")
        lines.append("")
    return lines
