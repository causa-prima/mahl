"""Zugriff auf die Claude-Code-Session-Logs: Sessions finden, ihre Art bestimmen, Reads zählen.

Die Logs liegen unter `~/.claude/projects/<kodiertes-cwd>/`: je Session ein Hauptlog
`<id>.jsonl` und – falls Subagenten liefen – `<id>/subagents/agent-*.jsonl`. Ein Log ist
zeilenweise JSON; ein Record trägt u.a. die Tool-Calls (`tool_use`) und deren Ergebnisse
(`tool_result`).

**Warum die Session-Art zählt:** Die Vorgänger-Messung (S109, Wegwerf-Script) scannte
ausschließlich Sessions mit `subagents/`-Verzeichnis. Das ist faktisch ein Filter auf
implementing-scenario-Sessions – Drain-, Retro- und Tooling-Sessions blieben unsichtbar,
obwohl gerade sie die kaizen-Dokumente lesen. Jede Aussage über „das Read-Volumen" war damit
stillschweigend eine Aussage über nur eine Session-Art. Dieses Modul klassifiziert stattdessen
und lässt die Auswertung je Art getrennt ausweisen.

Klassifikation: primär über das Feld `attributionSkill`, das Claude Code je Record mitschreibt
(zum Bau-Zeitpunkt in 38 von 48 Logs vorhanden – ältere Sessions kennen es nicht). Für den Rest
greift die manuell gepflegte Mapping-Datei `.claude/session-types.json`; sie hat Vorrang, weil
sie kuratiert ist.
"""
import json
import re
from collections import Counter
from pathlib import Path

from _util import REPO_ROOT

PROJECTS_DIR = Path.home() / ".claude" / "projects"
MAPPING_FILE = REPO_ROOT / ".claude" / "session-types.json"

# Welcher Skill steht für welche Art von Arbeit?
SKILL_TO_TYPE = {
    "implementing-scenario": "implementierung",
    "write-code": "implementierung",
    "review-code": "implementierung",  # läuft als Schritt 5 innerhalb von implementing-scenario
    # Szenario-Entwurf ist eigene Arbeit mit eigenem Leseprofil (Stories, Feature-Dateien –
    # kein Testcode) und gehört deshalb nicht zu „implementierung".
    "gherkin-workshop": "workshop",
    "draining-observations": "drain",
    "kaizen": "retro",
    "review-workflow": "tooling",
    "review-docs": "tooling",
    "skill-creator": "tooling",
    "update-config": "tooling",
    "schedule": "tooling",
}

# Skills, die eine Session begleiten, statt sie zu prägen – sie dürfen die Art nicht bestimmen,
# solange irgendein prägender Skill lief. `closing-session` läuft in fast jeder Session.
BEGLEIT_SKILLS = frozenset({"closing-session", "recall-session", "session-recall", "grill-me"})

UNBEKANNT = "unbekannt"
SONSTIGES = "sonstiges"


def project_log_dir(repo_root: Path = REPO_ROOT) -> Path:
    """Log-Verzeichnis dieses Repos (Claude Code kodiert das cwd, `/` → `-`)."""
    return PROJECTS_DIR / str(repo_root).replace("/", "-")


def load_mapping(path: Path = MAPPING_FILE) -> dict[str, str]:
    """Manuell gepflegte Session-ID (oder ID-Präfix) → Art. Fehlt die Datei, ist sie leer.

    Schlüssel mit führendem `_` sind Kommentare (JSON kennt keine) und werden übersprungen.
    """
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {key: value for key, value in raw.items() if not key.startswith("_")}


def mapped_type(session_id: str, mapping: dict[str, str]) -> str | None:
    """Manuelle Zuordnung für diese Session – exakt oder über einen ID-Präfix."""
    if session_id in mapping:
        return mapping[session_id]
    return next((art for key, art in mapping.items() if session_id.startswith(key)), None)


# Dateien, die `closing-session` am Ende nahezu JEDER Session anfasst. Sie sagen nichts über
# die geleistete Arbeit und müssen vor der Klassifikation weg – sonst gilt jede Session als
# Drain (wegen `observations.md`) oder als Retro (wegen `lessons_learned.md`).
RAUSCH_DATEIEN = (
    "docs/kaizen/observations.md",
    "docs/kaizen/lessons_learned.md",
    "docs/history/sessions/",
    "docs/AGENT_MEMORY.md",
    "docs/tech-debt.md",
    "docs/open-questions.md",
)

# Fallback-Heuristik für Sessions ohne prägenden Skill (praktisch nur die Logs von vor
# Einführung des `attributionSkill`-Feldes). Angewandt auf die um das Rauschen bereinigten
# Edits – erst dadurch sind die Archiv-Dateien brauchbare Marker, denn die schreibt allein
# der Drain bzw. die Retro. Reihenfolge ist bedeutsam.
# Gebaute Artefakte zuerst: Wer Produktionscode oder Werkzeug angefasst hat, hat daran
# gearbeitet – auch wenn nebenher OBS archiviert wurden. Die Archiv-Marker greifen erst
# danach, sonst gilt jede Tooling-Session als Drain, die zwischendurch aufgeräumt hat.
EDIT_MARKER = (
    ("Client/", "implementierung"),
    ("Server", "implementierung"),
    ("features/", "implementierung"),
    (".claude/", "tooling"),
    ("docs/kaizen/archive/observations_archive", "drain"),
    ("docs/kaizen/archive/lessons_learned", "retro"),
    ("docs/", "doku"),
)


def ohne_rauschen(paths: set[str]) -> set[str]:
    """Editierte Dateien ohne die, die jede Session ohnehin anfasst."""
    return {p for p in paths if not any(marker in p for marker in RAUSCH_DATEIEN)}


def type_from_edits(paths: set[str]) -> str | None:
    """Art aus den editierten Dateien erraten – schwächer als ein Skill-Signal, aber besser
    als „unbekannt". Wird in der Ausgabe als Herkunft `heuristik` ausgewiesen.

    Blieb nach dem Abzug des Rauschens nichts übrig, hat die Session ausschließlich die
    Abschluss-Dateien gepflegt – das ist selbst die Aussage (`abschluss`).
    """
    charakteristisch = ohne_rauschen(paths)
    if not charakteristisch:
        return "abschluss" if paths else None
    return next(
        (art for marker, art in EDIT_MARKER if any(marker in p for p in charakteristisch)),
        None,
    )


def session_type(
    session_id: str,
    skills: Counter,
    mapping: dict[str, str],
    edits: set[str] | None = None,
) -> tuple[str, str]:
    """(Art, Herkunft der Zuordnung). Absteigende Verlässlichkeit: mapping → skill → heuristik.

    Die manuelle Zuordnung schlägt alles, weil sie kuratiert ist.
    """
    manual = mapped_type(session_id, mapping)
    if manual:
        return manual, "mapping"

    praegend = Counter({s: n for s, n in skills.items() if s not in BEGLEIT_SKILLS})
    if praegend:
        art = SKILL_TO_TYPE.get(praegend.most_common(1)[0][0])
        if art:
            return art, "skill"

    geraten = type_from_edits(edits or set())
    return (geraten, "heuristik") if geraten else (UNBEKANNT, "-")


AREA_PREFIXES = (
    ("docs/guidelines", "docs/guidelines (Pflichtlektüre)"),
    ("docs/process", "docs/process (Pflichtlektüre)"),
    ("docs/kaizen", "docs/kaizen"),
    ("docs/history", "docs/history (ADR/Sessions)"),
    ("docs/reference", "docs/reference"),
    ("docs/stories", "docs/stories"),
    ("docs/", "docs/ (sonstige)"),
    (".claude/skills", ".claude/skills"),
    (".claude/agents", ".claude/agents"),
    (".claude/scripts", ".claude/scripts"),
    (".claude/hooks", ".claude/hooks"),
    (".claude/", ".claude/ (sonstige)"),
    ("Server", "Server/ (Backend-Code)"),
    ("Client", "Client/ (Frontend-Code)"),
    ("features", "features/ (Gherkin)"),
)


def categorize(path: str) -> str:
    """Pfad → Auswertungs-Bereich (erste passende Regel gewinnt, Reihenfolge ist bedeutsam)."""
    p = path.replace("\\", "/")
    return next((label for prefix, label in AREA_PREFIXES if prefix in p), "sonstiges")


def relative_path(path: str) -> str:
    """Repo-relativer Pfad, damit gleiche Dateien über Sessions hinweg zusammenfallen."""
    return path.split("/repos/mahl/")[-1]


def block_text(block) -> str:
    """Textinhalt eines Content-Blocks – Tool-Ergebnisse sind mal String, mal verschachtelt."""
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return ""
    if block.get("type") == "text":
        return block.get("text") or ""
    if block.get("type") == "tool_result":
        content = block.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(block_text(c) for c in content)
    return ""


# Claude Code lagert Tool-Ausgaben über ~60 KB in `<session>/tool-results/<id>.txt` aus und
# hinterlässt im Log nur eine 2-KB-Vorschau mit Pfad. Wer die Vorschau misst, untercountet
# ausgerechnet die größten Ausgaben – und damit die Dateien, um die es bei OBS-S109-1 geht.
# Die S109-Vorgänger-Messung hatte diesen Fehler.
_PERSISTED_RE = re.compile(r"Full output saved to:\s*(\S+)")


def effective_size(text: str) -> int:
    """Zeichenzahl einer Tool-Ausgabe – bei ausgelagerten Ausgaben die der Zieldatei.

    Ist die Zieldatei verschwunden, bleibt es bei der Vorschau (dann untercountet die
    Messung, aber sie erfindet nichts).
    """
    match = _PERSISTED_RE.search(text)
    if not match:
        return len(text)
    target = Path(match.group(1))
    return target.stat().st_size if target.exists() else len(text)


def _content_blocks(record: dict):
    return (record.get("message") or {}).get("content") or []


def load_records(path: Path) -> list[dict]:
    """Alle parsbaren Records eines Logs (defekte Zeilen werden übersprungen)."""
    records = []
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def skills_in(records: list[dict]) -> Counter:
    """Wie oft welcher Skill in diesem Log als aktiv vermerkt ist."""
    return Counter(skill for rec in records if (skill := rec.get("attributionSkill")))


def edited_paths(records: list[dict]) -> set[str]:
    """Dateien, die in diesem Kontext je editiert/geschrieben wurden."""
    return {
        fp
        for rec in records
        for block in _content_blocks(rec)
        if isinstance(block, dict)
        and block.get("type") == "tool_use"
        and block.get("name") in ("Edit", "Write", "NotebookEdit")
        and (fp := (block.get("input") or {}).get("file_path"))
    }


def read_events(records: list[dict]) -> list[tuple[str, int, bool]]:
    """(Dateipfad, Zeichen der Read-Ausgabe, gezielt?) je `Read`-Aufruf, in Log-Reihenfolge.

    Die Größe steckt im `tool_result`, der Pfad im zugehörigen `tool_use` – beide werden
    über die Tool-Use-ID verbunden. „Gezielt" heißt: mit `offset` oder `limit` gelesen,
    also bewusst nur ein Ausschnitt statt der ganzen Datei.
    """
    id_to_read: dict[str, tuple[str, bool]] = {
        block["id"]: (
            (block.get("input") or {}).get("file_path", "?"),
            bool((block.get("input") or {}).get("offset") or (block.get("input") or {}).get("limit")),
        )
        for rec in records
        for block in _content_blocks(rec)
        if isinstance(block, dict)
        and block.get("type") == "tool_use"
        and block.get("name") == "Read"
        and block.get("id")
    }
    return [
        (entry[0], effective_size(block_text(block)), entry[1])
        for rec in records
        for block in _content_blocks(rec)
        if isinstance(block, dict)
        and block.get("type") == "tool_result"
        and (entry := id_to_read.get(block.get("tool_use_id"))) is not None
    ]


def session_logs(log_dir: Path) -> list[tuple[str, Path, list[Path]]]:
    """(Session-ID, Hauptlog, Subagent-Logs) je Session, nach ID sortiert."""
    return [
        (main.stem, main, sorted((log_dir / main.stem / "subagents").glob("*.jsonl")))
        for main in sorted(log_dir.glob("*.jsonl"))
    ]
