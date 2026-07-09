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
        # Zwei Versuche: erster akquiriert oder trifft auf Bestand; bei verwaistem Lock
        # wird er entfernt und der zweite Versuch akquiriert atomar. Mehr als ein Retry
        # ist nicht nötig – hält beim zweiten Mal ein *lebender* Fremdlauf den Lock,
        # brechen wir ab (kein Endlos-Loop).
        for _ in range(2):
            try:
                # Atomare Erzeugung (O_EXCL): schlägt fehl, wenn die Datei existiert. Kein
                # TOCTOU-Fenster wie bei read-then-write – zwei quasi-gleichzeitig gestartete
                # Läufe können NICHT beide akquirieren (nur einer gewinnt das exklusive create),
                # womit sie sich nicht mehr dieselbe .stryker-tmp-Sandbox teilen (ENOENT/Contention).
                fd = os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                existing = self._read_existing_pid()
                if existing is not None and existing != os.getpid() and _pid_alive(existing):
                    self._abort(existing)
                # Verwaister Lock (Prozess tot / nicht parsebar) → entfernen, erneut versuchen.
                try:
                    self._lock_path.unlink(missing_ok=True)
                except OSError:
                    pass
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(str(os.getpid()))
            return self
        # Zweiter Versuch scheiterte ebenfalls (ein Fremdlauf hat den Lock inzwischen belegt).
        self._abort(self._read_existing_pid())

    def _abort(self, pid: int | None) -> "RunLock":
        print(
            f"⛔ Konkurrierender Stryker-Lauf aktiv (PID {pid}, Lock {self._lock_path}).\n"
            f"   Erst beenden lassen – paralleles Schreiben würde Report/Output korrumpieren.\n"
            f"   Verwaister Lock? Datei manuell löschen: {self._lock_path}",
            file=sys.stderr,
        )
        sys.exit(1)

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
