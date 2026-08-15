#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): kein Löschen eines TD-/OQ-Eintrags, auf den noch verwiesen wird.

`check-ref-direction.py` verhindert, dass eine **stabile** Datei eine volatile ID referenziert,
und lässt bewusste Einzelfälle über den `ref-ok`-Marker durch. Damit war `ref-ok` bisher ein
**stummes Opt-out**: einmal gesetzt, nie wieder geprüft. Verschwindet der Zieleintrag, dangelt
der Verweis still. Ebenso ungeprüft blieben Referenzen aus Produktionscode – der Datei-Scope
jenes Hooks endet bei `docs/`, `.claude/skills|agents/` und `CLAUDE.md`.

Dieser Hook schließt die Gegenrichtung: Verschwindet beim Edit eine TD-/OQ-ID aus ihrem
Tracker, wird das Repo nach Referenzen darauf durchsucht. Gibt es welche, wird der Edit
blockiert und die Fundstellen aufgelistet – sie gehören zuerst angepasst.

Das spiegelt ein bereits vorhandenes Muster: `.claude/scripts/decisions.py check` prüft
ADR-Referenzen im Code gegen `adr.md`. Für volatile IDs gab es kein Gegenstück.

Scope:
- **Auslöser** sind nur `docs/tech-debt.md` und `docs/open-questions.md`. Andere Dateien
  passieren ungeprüft. (OBS/LL werden archiviert statt gelöscht – ihre IDs bleiben auflösbar.)
- **Durchsucht** wird das Repo inkl. Produktionscode; ausgenommen sind Verzeichnisse, in denen
  ein Verweis historisch korrekt ist und stehen bleiben soll: Session-Logs und Kaizen-Archive.
  Die Tracker-Datei selbst zählt nicht mit – dort wird der Eintrag ja gerade entfernt.
- **Zeilen-Ausnahme:** `dangling-ok` in der referenzierenden Zeile (bewusst stehen gelassener
  historischer Verweis, z.B. ein „War bis SNNN als … abgelegt"-Vermerk).

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Der teure Repo-Scan läuft nur, wenn überhaupt eine ID verschwindet.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Tracker, aus denen Einträge ersatzlos verschwinden (im Gegensatz zu OBS/LL: archiviert).
# Der Lookahead schließt eine Fortsetzung der ID aus: ohne ihn läse `TD-S001-1-ALT` als
# `TD-S001-1`, und ein Umbenennen der Überschrift bliebe unbemerkt (in der Gegenprobe
# aufgetreten). `\b` trägt hier nicht – zwischen Ziffer und Bindestrich liegt eine Wortgrenze.
# Beispiel-IDs hier bewusst aus dem nicht vergebenen S001-Raum: eine echte ID im eigenen
# Quelltext ließe diesen Hook über sich selbst stolpern.
WATCHED = {
    "docs/tech-debt.md": re.compile(r"^## (TD-S\d{2,3}-\d+)(?![\w-])", re.M),
    "docs/open-questions.md": re.compile(r"^## (OQ-S\d{2,3}-\d+)(?![\w-])", re.M),
}

# Historische Verweise dürfen dangeln – sie beschreiben einen vergangenen Zustand.
_SKIP_DIRS = {
    ".git", "node_modules", "bin", "obj", "dist", "coverage", "__pycache__",
    ".venv", "TestResults", "StrykerOutput", "playwright-report",
}
_SKIP_PREFIXES = ("docs/history/sessions/", "docs/kaizen/archive/", ".claude/tmp/")

# Nur Textquellen, in denen Referenzen überhaupt vorkommen.
_SCAN_SUFFIXES = {".md", ".cs", ".ts", ".tsx", ".py", ".json", ".feature", ".yml", ".yaml"}

_DANGLING_OK = "dangling-ok"
_MAX_HITS = 40  # Deckel, damit die Fehlermeldung lesbar bleibt


def watched_pattern(file_path: str) -> re.Pattern | None:
    """Das ID-Muster für diesen Tracker – oder None, wenn die Datei keiner ist."""
    posix = Path(file_path).as_posix()
    for name, pattern in WATCHED.items():
        if posix.endswith(name):
            return pattern
    return None


def removed_ids(pre: str, post: str, pattern: re.Pattern) -> list[str]:
    """IDs, die vor dem Edit einen Eintrag hatten und danach nicht mehr."""
    before = pattern.findall(pre)
    after = set(pattern.findall(post))
    return [i for i in before if i not in after]


def _scannable_files() -> list[Path]:
    """Alle Textdateien des Repos außer den bewusst ausgenommenen Bereichen."""
    files = []
    for path in _REPO_ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in _SCAN_SUFFIXES:
            continue
        rel = path.relative_to(_REPO_ROOT)
        # Nur Segmente **innerhalb** des Repos prüfen. Über `path.parts` liefen auch die
        # Verzeichnisse oberhalb der Repo-Wurzel mit – ein Checkout unter `/…/dist/…` oder
        # `/home/coverage-user/…` hätte den Scan stumm auf null Dateien gesetzt, und der Hook
        # meldete Vollständigkeit, ohne je gesucht zu haben.
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if rel.as_posix().startswith(_SKIP_PREFIXES):
            continue
        files.append(path)
    return files


def find_references(ids: list[str], exclude: Path) -> list[tuple[str, int, str]]:
    """(Datei, Zeilennummer, ID) für jede verbliebene Referenz auf eine entfernte ID."""
    if not ids:
        return []
    wanted = re.compile(r"\b(" + "|".join(re.escape(i) for i in ids) + r")\b")
    try:
        exclude_resolved = exclude.resolve()
    except OSError:
        exclude_resolved = exclude

    hits: list[tuple[str, int, str]] = []
    for path in _scannable_files():
        if path.resolve() == exclude_resolved:
            continue  # der Tracker selbst – dort wird gerade gelöscht
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not wanted.search(text):
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _DANGLING_OK in line:
                continue
            for match in wanted.finditer(line):
                hits.append((rel, lineno, match.group(1)))
    return hits


def read_file_text(file_path: str) -> str:
    """Aktueller Datei-Inhalt; "" wenn die Datei (noch) nicht existiert."""
    path = Path(file_path)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def compute_post_content(tool: str, tool_input: dict, pre: str) -> str | None:
    """Simuliert den Datei-Inhalt nach Anwendung des Edits/Writes."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if old and old in pre:
            count = -1 if tool_input.get("replace_all") else 1
            return pre.replace(old, new, count)
        return pre  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
    return None


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not file_path:
        return None

    pattern = watched_pattern(file_path)
    if pattern is None:
        return None

    pre = read_file_text(file_path)
    post = compute_post_content(tool, tool_input, pre)
    if post is None:
        return None

    gone = removed_ids(pre, post, pattern)
    hits = find_references(gone, Path(file_path))
    if not hits:
        return None

    shown = hits[:_MAX_HITS]
    lines = "\n".join(f"  - {f}:{n} → {i}" for f, n, i in shown)
    more = f"\n  … und {len(hits) - len(shown)} weitere" if len(hits) > len(shown) else ""
    removed = ", ".join(sorted(set(i for _, _, i in hits)))
    return (
        f"❌ Dangling-Referenzen (Poka-Yoke): {removed} soll verschwinden, es wird aber noch "
        "darauf verwiesen:\n"
        f"{lines}{more}\n"
        "  Volatile IDs (TD-/OQ-) verschwinden beim Erledigen – ein verbliebener Verweis zeigt "
        "danach ins Leere und ist von außen nicht mehr auflösbar.\n"
        "  Pass zuerst die Fundstellen an: nötige Information dort inlinen, auf ein stabiles "
        "Artefakt (ADR/Guideline) umhängen, oder den Verweis entfernen. Danach den Eintrag "
        "löschen.\n"
        "  Bewusst historischer Verweis („War bis SNNN als … abgelegt“) → `dangling-ok` in die "
        "betreffende Zeile."
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    try:
        reason = check(data)
        if reason:
            print(reason, file=sys.stderr)
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-dangling-refs: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
