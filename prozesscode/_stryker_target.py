"""Auflösung und Validierung des `--mutate`-Arguments der Stryker-Wrapper.

Hintergrund: Stryker wertet `--mutate`-Muster **projekt-relativ** aus (Backend zu `Server/`,
Frontend zu `Client/`) – nicht repo-root-relativ, wie es praktisch jedes andere Script hier tut.
Ein Muster mit falscher Basis wird nicht als Fehler gemeldet, sondern führt zu einem Lauf über
null Dateien, der als „100 %" endet. Dasselbe passiert bei einem Glob ohne Treffer. Beide Fälle
werden hier VOR dem Lauf abgefangen, mit einem konkreten Korrekturvorschlag statt eines stillen
Leerlaufs (OBS-S103-1, OBS-S106-3, OBS-S108-3).
"""
import sys
from pathlib import Path


def _strip_range(pattern: str) -> str:
    """Trennt die StrykerJS-Mutation-Range ab (`datei.ts:1:3-1:5` → `datei.ts`).

    Die Range hängt hinten am Dateinamen; der Pfad selbst enthält nie ':'.
    """
    return pattern.partition(":")[0]


def _matches(base: Path, pattern: str) -> bool:
    try:
        return any(base.glob(pattern))
    except (ValueError, IndexError, NotImplementedError):
        # Ungültiges Glob-Muster (z.B. Reste einer zerlegten Brace-Expansion, leeres Muster)
        # oder ein absoluter Pfad, den `Path.glob` gar nicht annimmt.
        return False


def resolve_mutate(raw: str, project_dir: Path, repo_root: Path) -> list[str]:
    """Zerlegt das `--mutate`-Argument in Einzelmuster und prüft, dass jedes real trifft.

    Bricht mit Exit 2 ab, sobald ein Muster keine Datei trifft – lieber gar kein Lauf als ein
    Lauf, der nichts mutiert und trotzdem grün aussieht. Gibt die bereinigten Muster zurück.
    """
    if "{" in raw or "}" in raw:
        _fail(
            f"Brace-Glob nicht unterstützt: {raw!r}\n"
            f"   Stryker zerlegt die Liste am Komma – aus `src/{{a.ts,b.ts}}` werden die beiden\n"
            f"   ungültigen Muster `src/{{a.ts` und `b.ts}}`, die nichts treffen.\n"
            f"   Stattdessen als Kommaliste vollständiger Pfade schreiben: `src/a.ts,src/b.ts`"
        )

    patterns = [p.strip() for p in raw.split(",") if p.strip()]
    if not patterns:
        _fail(f"--mutate ist leer: {raw!r}")

    for pattern in patterns:
        if pattern.startswith("!"):
            continue  # Ausschlussmuster dürfen ins Leere zeigen.
        bare = _strip_range(pattern)
        if _matches(project_dir, bare):
            continue

        hint = _correction_hint(bare, project_dir, repo_root)
        _fail(
            f"--mutate-Muster trifft keine Datei: {pattern!r}\n"
            f"   Basis ist {project_dir.name}/ (Stryker wertet die Muster projekt-relativ aus,\n"
            f"   NICHT repo-root-relativ wie die meisten anderen Scripts hier).{hint}"
        )

    return patterns


def _correction_hint(bare: str, project_dir: Path, repo_root: Path) -> str:
    """Baut den „meintest du"-Hinweis, wenn das Muster nur die falsche Basis hat."""
    if not _matches(repo_root, bare):
        return ""
    try:
        hit = next(iter(repo_root.glob(bare)))
        corrected = hit.relative_to(project_dir)
    except (StopIteration, ValueError):
        return ""
    return f"\n   Meintest du `{corrected}`? (Das Muster trifft repo-root-relativ, projekt-relativ nicht.)"


def _fail(message: str) -> None:
    print(f"⛔ {message}", file=sys.stderr)
    sys.exit(2)
