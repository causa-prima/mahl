#!/usr/bin/env python3
"""PID-basierter Lock-Guard gegen konkurrierende Stryker-Läufe.

Schützt die `.claude/tmp/stryker_*_out.txt`-Ausgabedateien: zwei parallele Läufe würden
in dieselbe Datei schreiben und sich gegenseitige Reports/Output korrumpieren.

Mechanik: Sidecar-Lockfile (`<tmp>.lock`) enthält die PID des laufenden Prozesses. Beim
Start wird geprüft, ob bereits ein Lock existiert und dessen Prozess noch lebt
(`os.kill(pid, 0)`). Ein verwaister Lock (Prozess tot / nicht parsebar) wird automatisch
übernommen, damit ein Absturz nicht dauerhaft blockiert.
"""
import os
import sys
from pathlib import Path


def _pid_alive(pid: int) -> bool:
    """True, wenn ein Prozess mit dieser PID existiert (Linux-PID des WSL-Python)."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Prozess existiert, gehört aber einem anderen User → lebt.
        return True
    return True


class RunLock:
    """Context-Manager: hält einen PID-Lock auf eine Ausgabedatei.

    Verwendung:
        with RunLock(tmp_file):
            ...  # Stryker-Lauf

    Bricht mit Exit 1 ab, wenn bereits ein lebender Lauf den Lock hält.
    """

    def __init__(self, target: Path):
        self._lock_path = Path(str(target) + ".lock")

    def __enter__(self) -> "RunLock":
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._read_existing_pid()
        if existing is not None and existing != os.getpid() and _pid_alive(existing):
            print(
                f"⛔ Konkurrierender Stryker-Lauf aktiv (PID {existing}, Lock {self._lock_path}).\n"
                f"   Erst beenden lassen – paralleles Schreiben würde Report/Output korrumpieren.\n"
                f"   Verwaister Lock? Datei manuell löschen: {self._lock_path}",
                file=sys.stderr,
            )
            sys.exit(1)
        # Lock übernehmen (eigene PID eintragen; überschreibt verwaisten Lock).
        self._lock_path.write_text(str(os.getpid()), encoding="utf-8")
        return self

    def __exit__(self, *_exc) -> None:
        try:
            # Nur den eigenen Lock entfernen (Race: anderer Lauf hat ggf. übernommen).
            if self._read_existing_pid() == os.getpid():
                self._lock_path.unlink(missing_ok=True)
        except OSError:
            pass

    def _read_existing_pid(self) -> int | None:
        try:
            return int(self._lock_path.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, ValueError):
            return None
