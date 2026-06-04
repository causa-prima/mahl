"""Shared helpers for .claude/scripts/: Windows-Pfad-Konvertierung + dotnet via cmd.exe."""
import os
import subprocess
import sys


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


def _query_dotnet_processes() -> list[tuple[str, str]]:
    """Gibt laufende dotnet.exe-Prozesse als (pid, commandline) zurück.

    Nutzt PowerShell Get-CimInstance (WMIC-Ersatz, kein WMIC ab Windows 11 25H2).
    Gibt leere Liste zurück wenn powershell.exe nicht verfügbar ist (pure Linux).
    """
    import json as _json
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \\\"name='dotnet.exe'\\\" "
        "| Select-Object ProcessId,CommandLine "
        "| ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=15,
        )
        raw = result.stdout.strip()
        if not raw or raw.lower() in ("null", ""):
            return []
        data = _json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        return [
            (str(entry.get("ProcessId", "")), entry.get("CommandLine") or "")
            for entry in data
            if entry.get("ProcessId")
        ]
    except (FileNotFoundError, subprocess.TimeoutExpired, _json.JSONDecodeError):
        return []


def check_dotnet_dll_lock() -> None:
    """Prüft ob dotnet-Prozesse aus dem mahl-Projekt laufen (DLL-Lock-Risiko).

    Identifiziert Prozesse anhand des Projektpfads in der CommandLine.
    Setzt voraus dass dotnet run mit --project <vollpfad> aufgerufen wird.
    Wird auf reinem Linux ohne powershell.exe stillschweigend übersprungen.
    """
    all_procs = _query_dotnet_processes()
    repo_root = REPO_ROOT_WIN.lower()
    mahl_procs = [(pid, cmd) for pid, cmd in all_procs if repo_root in cmd.lower()]

    if not mahl_procs:
        return

    print(
        "⚠️  dotnet-Prozesse aus diesem Projekt laufen bereits (DLL-Lock-Risiko).\n"
        "   Build und Stryker schlagen mit MSB3027/MSB3021 fehl.",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    for pid, cmd in mahl_procs:
        short_cmd = cmd if len(cmd) <= 100 else cmd[:97] + "..."
        print(f"   PID {pid}: {short_cmd or '(kein Kommando-Argument)'}", file=sys.stderr)
    print(file=sys.stderr)
    label = "Prozess beenden" if len(mahl_procs) == 1 else "Prozesse beenden"
    print(f"   {label}:", file=sys.stderr)
    for pid, _ in mahl_procs:
        print(f'     cmd.exe /c "taskkill /f /pid {pid}"', file=sys.stderr)
    sys.exit(1)


def run_npm(args: list[str], subdir: str = "Client") -> tuple[str, int]:
    """Führt 'npm <args>' via cmd.exe aus. Gibt (combined_output, exit_code) zurück."""
    cwd_win = REPO_ROOT_WIN + "\\" + subdir
    quoted = [f'"{a}"' if " " in a and not a.startswith('"') else a for a in args]
    cmd_inner = f"cd /d {cwd_win} && npm {' '.join(quoted)}"
    result = subprocess.run(
        ["cmd.exe", "/c", cmd_inner],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout, result.returncode


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
