#!/usr/bin/env python3
"""PID-basierter Lock-Guard gegen konkurrierende Stryker- und E2E-Läufe.

Schützt die `.claude/tmp/stryker_*_out.txt`-Ausgabedateien: zwei parallele Läufe würden
in dieselbe Datei schreiben und sich gegenseitige Reports/Output korrumpieren. Bei E2E
bauten zwei Läufe dasselbe Backend und stritten um dessen Port (playwright-test.py).

Mechanik: Sidecar-Lockfile (`<tmp>.lock`) enthält die PID des laufenden Prozesses. Beim
Start wird geprüft, ob bereits ein Lock existiert und dessen Prozess noch lebt
(`os.kill(pid, 0)`). Ein verwaister Lock (Prozess tot / nicht parsebar) wird automatisch
übernommen, damit ein Absturz nicht dauerhaft blockiert.
"""
import os
import sys
import time
from pathlib import Path


# Eigener Exit-Code für „Lock belegt, Lauf gar nicht gestartet". Ein generisches Exit 1 wäre
# für den Aufrufer von einem Score-Gate-Fail (Stryker lief, Score < 100 %) nicht unterscheidbar –
# `qa-check.py` griff deshalb auf den Report eines fremden Laufs zurück und attestierte einen
# Umfang, der nie geprüft wurde (OBS-S108-3 c).
LOCK_BUSY_EXIT_CODE = 99

# Wie oft ein wartender Lauf nachsieht, ob der Lock frei ist – kurz gegenüber der Laufdauer
# (Sekunden), lang genug, um die CPU nicht mit Nachsehen zu belegen.
_PRUEF_ABSTAND = 0.5

_WARTE_MELDUNG = ("⏳ Warte auf laufenden {laufart} (PID {pid}), höchstens {wartezeit} s – "
                  "danach Abbruch mit Exit 99.")
_NACH_WARTEN_MELDUNG = ("   Auch nach {wartezeit} s Warten nicht frei – später erneut versuchen; "
                        "im Review den Befund als offene Prüfung melden.")


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

    Bricht mit LOCK_BUSY_EXIT_CODE ab, wenn ein lebender Lauf den Lock hält – sofort oder nach
    der Wartezeit.
    """

    def __init__(self, target: Path, laufart: str = "Stryker-Lauf", wartezeit: float = 0):
        """`wartezeit` (Sekunden): so lange auf einen lebenden Fremdlauf warten, dann abbrechen.

        Kurze Läufe warten, lange brechen sofort ab: Ohne explizites timeout schiebt der Harness
        einen Bash-Aufruf nach 120 s in den Hintergrund, und ein untätiger benannter Subagent
        erfährt dann nie, dass er fertig ist (OBS-S144-4). Warten lohnt also nur, wenn
        Wartezeit plus eigener Lauf darunter bleiben.
        """
        self._lock_path = Path(str(target) + ".lock")
        self._laufart = laufart
        self._wartezeit = wartezeit

    def __enter__(self) -> "RunLock":
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        frist = time.monotonic() + self._wartezeit
        angekuendigt = False
        while not self._nehmen():
            halter = self._read_existing_pid()
            if time.monotonic() >= frist:
                self._abort(halter)
            if not angekuendigt:
                print(_WARTE_MELDUNG.format(laufart=self._laufart, pid=halter,
                                            wartezeit=f"{self._wartezeit:g}"), file=sys.stderr)
                angekuendigt = True
            time.sleep(_PRUEF_ABSTAND)
        return self

    def _nehmen(self) -> bool:
        """True, wenn der Lock jetzt diesem Prozess gehört; False, wenn ein lebender Fremdlauf
        ihn hält."""
        # Zwei Versuche: erster akquiriert oder trifft auf Bestand; bei verwaistem Lock
        # wird er entfernt und der zweite Versuch akquiriert atomar. Mehr als ein Retry
        # ist nicht nötig – hält beim zweiten Mal ein *lebender* Fremdlauf den Lock,
        # entscheidet der Aufrufer über Warten oder Abbruch (kein Endlos-Loop hier).
        for _ in range(2):
            if self._anlegen():
                return True
            existing = self._read_existing_pid()
            if existing is not None and existing != os.getpid() and _pid_alive(existing):
                return False
            # Verwaister Lock (Prozess tot / nicht parsebar) → entfernen, erneut versuchen.
            try:
                self._lock_path.unlink(missing_ok=True)
            except OSError:
                pass
        # Zweiter Versuch scheiterte ebenfalls (ein Fremdlauf hat den Lock inzwischen belegt).
        return False

    def _anlegen(self) -> bool:
        """Legt die Lock-Datei mit der eigenen PID an – atomar und nur, wenn sie noch fehlt.

        Erst die PID in einen Entwurf, dann per Hardlink an den Lock-Namen: `os.link` scheitert
        wie O_EXCL, wenn der Name existiert, zwei gleichzeitig gestartete Läufe können also nicht
        beide akquirieren. Anders als O_EXCL mit anschließendem write ist die Lock-Datei aber nie
        leer – in diesem Fenster hielt ein zweiter Lauf sie für verwaist, löschte sie und lief
        mit. Mit parallel startenden Auditoren ist das kein theoretischer Fall mehr (S152).
        """
        entwurf = self._lock_path.with_name(f"{self._lock_path.name}.{os.getpid()}")
        entwurf.write_text(str(os.getpid()), encoding="utf-8")
        try:
            os.link(entwurf, self._lock_path)
            return True
        except FileExistsError:
            return False
        finally:
            entwurf.unlink(missing_ok=True)

    def _abort(self, pid: int | None) -> "RunLock":
        print(
            f"⛔ Konkurrierender {self._laufart} aktiv (PID {pid}, Lock {self._lock_path}).\n"
            f"   Erst beenden lassen – paralleles Schreiben würde Report/Output korrumpieren.\n"
            f"   Verwaister Lock? Datei manuell löschen: {self._lock_path}",
            file=sys.stderr,
        )
        if self._wartezeit > 0:
            print(_NACH_WARTEN_MELDUNG.format(wartezeit=f"{self._wartezeit:g}"), file=sys.stderr)
        sys.exit(LOCK_BUSY_EXIT_CODE)

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
