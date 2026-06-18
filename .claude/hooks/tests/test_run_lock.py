"""Tests für .claude/scripts/_run_lock.py – PID-Lock-Guard gegen konkurrierende Stryker-Läufe."""
import importlib.util
import os

import pytest

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "_run_lock.py")


def _load():
    spec = importlib.util.spec_from_file_location("run_lock", _PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rl = _load()


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


def test_live_concurrent_lock_aborts(tmp_path):
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
