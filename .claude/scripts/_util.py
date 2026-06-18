"""Shared helpers for .claude/scripts/: native dotnet/npm-Aufrufe (WSL-native Toolchain)."""
import os
import subprocess
from pathlib import Path


REPO_ROOT: Path = Path(
    os.environ.get("CLAUDE_PROJECT_DIR", str(Path(__file__).resolve().parents[2]))
)


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
