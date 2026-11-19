"""Tests für prozesscode/_run_lock.py – PID-Lock-Guard gegen konkurrierende Stryker-Läufe."""
import os
import threading
import time

import pytest

from prozesscode import _run_lock as rl


def test_acquire_and_release(tmp_path):
    # // Given eine Ziel-Datei ohne bestehenden Lock
    target = tmp_path / "stryker_out.txt"
    lock_file = tmp_path / "stryker_out.txt.lock"
    # // When der Lock genommen und wieder freigegeben wird
    with rl.RunLock(target):
        assert lock_file.exists()
        assert lock_file.read_text(encoding="utf-8").strip() == str(os.getpid())
    # // Then ist der Lock nach dem Block entfernt
    assert not lock_file.exists()


def test_live_concurrent_lock_aborts(tmp_path, capsys):
    # // Given ein Lockfile mit einer fremden, garantiert lebenden PID (1 = init)
    target = tmp_path / "stryker_out.txt"
    lock_file = tmp_path / "stryker_out.txt.lock"
    lock_file.write_text("1", encoding="utf-8")
    # // When ein zweiter Lauf den Lock nehmen will, während die PID lebt
    # // Then bricht er mit Exit != 0 ab
    with pytest.raises(SystemExit) as exc:
        with rl.RunLock(target):
            pass
    assert exc.value.code != 0
    # Ohne Angabe ist es ein Stryker-Lauf – die beiden Stryker-Wrapper nennen keine Laufart.
    assert "Konkurrierender Stryker-Lauf aktiv (PID 1," in capsys.readouterr().err


def test_stale_lock_reclaimed(tmp_path):
    # // Given ein Lockfile mit einer toten PID (sehr hohe, nicht vergebene PID)
    target = tmp_path / "stryker_out.txt"
    lock_file = tmp_path / "stryker_out.txt.lock"
    dead_pid = 2_000_000_000  # praktisch nie vergeben
    lock_file.write_text(str(dead_pid), encoding="utf-8")
    # // When ein neuer Lauf startet
    with rl.RunLock(target):
        # // Then übernimmt er den verwaisten Lock (eigene PID eingetragen)
        assert lock_file.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_corrupt_lock_reclaimed(tmp_path):
    # // Given ein Lockfile mit nicht-parsebarem Inhalt
    target = tmp_path / "stryker_out.txt"
    lock_file = tmp_path / "stryker_out.txt.lock"
    lock_file.write_text("not-a-pid", encoding="utf-8")
    # // When / // Then der Lock wird übernommen statt zu blockieren
    with rl.RunLock(target):
        assert lock_file.read_text(encoding="utf-8").strip() == str(os.getpid())


def test_live_lock_not_clobbered_on_abort(tmp_path):
    # // Given ein Lockfile einer lebenden fremden PID (1 = init)
    target = tmp_path / "stryker_out.txt"
    lock_file = tmp_path / "stryker_out.txt.lock"
    lock_file.write_text("1", encoding="utf-8")
    # // When ein konkurrierender Lauf abbricht (atomare O_EXCL-Erzeugung schlägt fehl)
    with pytest.raises(SystemExit):
        with rl.RunLock(target):
            pass
    # // Then bleibt der fremde Lock-Inhalt unangetastet – kein Schreiben vor bestätigtem
    #        Ownership (das TOCTOU-Fenster der read-then-write-Variante ist geschlossen).
    assert lock_file.read_text(encoding="utf-8").strip() == "1"


def test_abbruch_nennt_die_art_des_laufs(tmp_path, capsys):
    # // Given ein Lockfile einer lebenden fremden PID (1 = init) für einen E2E-Lauf
    target = tmp_path / "playwright_run"
    (tmp_path / "playwright_run.lock").write_text("1", encoding="utf-8")
    # // When ein zweiter E2E-Lauf startet
    with pytest.raises(SystemExit) as exc:
        with rl.RunLock(target, "E2E-Lauf"):
            pass
    # // Then nennt der Abbruch den E2E-Lauf, nicht Stryker, mit eigenem Exit-Code
    assert exc.value.code == rl.LOCK_BUSY_EXIT_CODE
    assert "Konkurrierender E2E-Lauf aktiv (PID 1," in capsys.readouterr().err


@pytest.fixture
def schnell_nachsehen(monkeypatch):
    """Ein wartender Lauf sieht sonst nur alle 0,5 s nach – jeder Wartetest kostete das."""
    monkeypatch.setattr(rl, "_PRUEF_ABSTAND", 0.01)


def _fremdlauf_gibt_frei_nach(lock_file, sekunden: float) -> threading.Timer:
    """Ein lebender Fremdlauf (PID 1 = init) hält den Lock und gibt ihn nach `sekunden` frei."""
    lock_file.write_text("1", encoding="utf-8")
    freigabe = threading.Timer(sekunden, lambda: lock_file.unlink())
    freigabe.start()
    return freigabe


def test_wartet_bis_der_fremde_lauf_endet(tmp_path, capsys, schnell_nachsehen):
    # // Given ein Lock, den ein fremder Lauf hält und nach kurzer Zeit freigibt
    target = tmp_path / "dotnet_test_run"
    lock_file = tmp_path / "dotnet_test_run.lock"
    freigabe = _fremdlauf_gibt_frei_nach(lock_file, 0.2)
    # // When ein zweiter Lauf mit Wartezeit startet
    with rl.RunLock(target, "Backend-Testlauf", wartezeit=5):
        # // Then übernimmt er den Lock, statt abzubrechen, und hat das Warten angekündigt
        assert lock_file.read_text(encoding="utf-8").strip() == str(os.getpid())
    freigabe.join()
    assert "Warte auf laufenden Backend-Testlauf (PID 1), höchstens 5 s" in capsys.readouterr().err


def test_bricht_nach_ablauf_der_wartezeit_ab_und_nennt_den_ausweg(tmp_path, capsys, schnell_nachsehen):
    # // Given ein Lock, den ein fremder, lebender Lauf dauerhaft hält
    target = tmp_path / "dotnet_test_run"
    (tmp_path / "dotnet_test_run.lock").write_text("1", encoding="utf-8")
    beginn = time.monotonic()
    # // When ein zweiter Lauf mit kurzer Wartezeit startet
    with pytest.raises(SystemExit) as exc:
        with rl.RunLock(target, "Backend-Testlauf", wartezeit=0.3):
            pass
    # // Then wartet er die Frist ab, bricht mit dem Belegt-Code ab und sagt, dass er gewartet hat
    assert time.monotonic() - beginn >= 0.3
    assert exc.value.code == rl.LOCK_BUSY_EXIT_CODE
    fehler = capsys.readouterr().err
    assert "Konkurrierender Backend-Testlauf aktiv (PID 1," in fehler
    assert "Auch nach 0.3 s Warten nicht frei – später erneut versuchen" in fehler


def test_kuendigt_das_warten_nur_einmal_an(tmp_path, capsys, schnell_nachsehen):
    # // Given ein Fremdlauf, der den Lock über viele Nachseh-Runden hält
    target = tmp_path / "dotnet_test_run"
    freigabe = _fremdlauf_gibt_frei_nach(tmp_path / "dotnet_test_run.lock", 0.2)
    # // When ein zweiter Lauf wartet, bis der Lock frei ist
    with rl.RunLock(target, "Backend-Testlauf", wartezeit=5):
        pass
    freigabe.join()
    # // Then steht die Warteansage genau einmal in der Ausgabe
    assert capsys.readouterr().err.count("Warte auf laufenden") == 1


def test_ohne_wartezeit_bricht_er_sofort_und_ohne_warteansage_ab(tmp_path, capsys):
    # // Given ein Lock, den ein fremder, lebender Lauf hält
    target = tmp_path / "playwright_run"
    (tmp_path / "playwright_run.lock").write_text("1", encoding="utf-8")
    # // When ein Lauf ohne Wartezeit startet (E2E, Stryker)
    with pytest.raises(SystemExit):
        with rl.RunLock(target, "E2E-Lauf"):
            pass
    # // Then kündigt er weder Warten an, noch behauptet er, gewartet zu haben
    fehler = capsys.readouterr().err
    assert "Warte" not in fehler
    assert "Auch nach" not in fehler


def test_hinterlaesst_neben_dem_lock_keine_weitere_datei(tmp_path):
    # // Given ein leeres Verzeichnis
    target = tmp_path / "dotnet_test_run"
    # // When ein Lauf den Lock nimmt
    with rl.RunLock(target):
        # // Then liegt dort nur die Lock-Datei – der Entwurf mit der PID ist wieder weg
        assert [p.name for p in tmp_path.iterdir()] == ["dotnet_test_run.lock"]
    assert list(tmp_path.iterdir()) == []


def test_ein_abgewiesener_lauf_hinterlaesst_keinen_entwurf(tmp_path):
    # // Given ein Lock, den ein fremder, lebender Lauf hält
    target = tmp_path / "dotnet_test_run"
    (tmp_path / "dotnet_test_run.lock").write_text("1", encoding="utf-8")
    # // When ein zweiter Lauf abgewiesen wird
    with pytest.raises(SystemExit):
        with rl.RunLock(target):
            pass
    # // Then bleibt nur der fremde Lock zurück
    assert [p.name for p in tmp_path.iterdir()] == ["dotnet_test_run.lock"]
