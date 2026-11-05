"""Shared helpers für den Prozess-Code: native dotnet/npm-Aufrufe (WSL-native Toolchain)."""
import os
import subprocess
from pathlib import Path


# Wo dieser Code liegt – maßgeblich für jede Repo-Datei und jeden dotnet-/npm-Aufruf. Bewusst
# nicht `CLAUDE_PROJECT_DIR`: In einem git-Worktree zeigte das aufs Hauptrepo.
REPO_ROOT: Path = Path(__file__).resolve().parents[1]


def projekt_verzeichnis() -> Path:
    """Wo Claude Code läuft – danach ist der Ordner der Session-Logs benannt. Ohne Claude Code
    (Werkzeug von Hand gestartet) das Repo selbst."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", REPO_ROOT))


def run_npm(args: list[str], subdir: str = "Client") -> tuple[str, int]:
    """Führt 'npm <args>' nativ in REPO_ROOT/<subdir> aus. Gibt (combined_output, exit_code)."""
    result = subprocess.run(
        ["npm", *args],
        cwd=str(REPO_ROOT / subdir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout, result.returncode


def run_dotnet(args: list[str], cwd: str | None = None) -> tuple[str, int]:
    """Führt 'dotnet <args>' nativ aus (cwd default REPO_ROOT). Gibt (combined_output, exit_code)."""
    result = subprocess.run(
        ["dotnet", *args],
        cwd=cwd or str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout, result.returncode
