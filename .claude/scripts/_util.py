"""Shared helpers for .claude/scripts/: Windows-Pfad-Konvertierung + dotnet via cmd.exe."""
import os
import subprocess


def _win_path(linux_path: str) -> str:
    """Konvertiert /mnt/c/Users/... → C:\\Users\\..."""
    path = linux_path.rstrip("/")
    parts = path.split("/")
    # Erwartetes Format: ['', 'mnt', 'X', 'rest', ...]
    if len(parts) >= 3 and parts[0] == "" and parts[1] == "mnt" and len(parts[2]) == 1:
        drive = parts[2].upper() + ":"
        rest = parts[3:]
        return drive + "\\" + "\\".join(rest) if rest else drive + "\\"
    return linux_path  # Fallback: unverändert zurückgeben


def _get_repo_root_win() -> str:
    linux_root = os.environ.get("CLAUDE_PROJECT_DIR", "/mnt/c/Users/kieritz/source/repos/mahl")
    return _win_path(linux_root)


REPO_ROOT_WIN: str = _get_repo_root_win()


def run_dotnet(args: list[str], cwd_win: str | None = None) -> tuple[str, int]:
    """Führt 'dotnet <args>' via cmd.exe aus. Gibt (combined_output, exit_code) zurück."""
    if cwd_win is None:
        cwd_win = REPO_ROOT_WIN
    # Args mit Leerzeichen in Anführungszeichen
    quoted = [f'"{a}"' if " " in a and not a.startswith('"') else a for a in args]
    cmd_inner = f"cd /d {cwd_win} && dotnet {' '.join(quoted)}"
    result = subprocess.run(
        ["cmd.exe", "/c", cmd_inner],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout, result.returncode
