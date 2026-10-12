"""Tests for the GOD_NODE schedule and restart logic (no subprocesses spawned)."""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from orchestrator import god_node
from orchestrator.god_node import WraithOrchestrator


def at(hour: int) -> datetime.datetime:
    return datetime.datetime(2026, 10, 13, hour, 30)


def test_default_night_window_is_local_2_to_8(monkeypatch):
    monkeypatch.delenv("WRAITH_NIGHT_START", raising=False)
    monkeypatch.delenv("WRAITH_NIGHT_END", raising=False)
    o = WraithOrchestrator()
    assert [h for h in range(24) if o.is_night_mode(at(h))] == [2, 3, 4, 5, 6, 7]


def test_uses_local_clock_not_utc(monkeypatch):
    monkeypatch.delenv("WRAITH_NIGHT_START", raising=False)
    monkeypatch.delenv("WRAITH_NIGHT_END", raising=False)

    class FakeDT(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            # 03:00 local; in UTC+8 that would be 19:00 UTC (day mode if UTC were used)
            return cls(2026, 10, 13, 3, 0) if tz is None else cls(2026, 10, 12, 19, 0, tzinfo=tz)

    monkeypatch.setattr(god_node.datetime, "datetime", FakeDT)
    assert WraithOrchestrator().is_night_mode() is True


def test_window_crossing_midnight(monkeypatch):
    monkeypatch.setenv("WRAITH_NIGHT_START", "22")
    monkeypatch.setenv("WRAITH_NIGHT_END", "6")
    o = WraithOrchestrator()
    assert o.is_night_mode(at(23)) and o.is_night_mode(at(0)) and o.is_night_mode(at(5))
    assert not o.is_night_mode(at(6)) and not o.is_night_mode(at(12))


def test_invalid_env_falls_back_to_defaults(monkeypatch):
    monkeypatch.setenv("WRAITH_NIGHT_START", "nope")
    monkeypatch.setenv("WRAITH_NIGHT_END", "99")
    o = WraithOrchestrator()
    assert (o.night_start, o.night_end) == (2, 8)


class _Done:
    pid = 1

    def __init__(self, code):
        self.code = code

    def poll(self):
        return self.code


def test_clean_exit_marks_job_done_and_is_not_restarted():
    o = WraithOrchestrator()
    o.current_mode = "NIGHT"
    o.active_process = _Done(0)
    assert o.check_process_health() is False
    assert o.mode_job_done is True
    assert o.active_process is None


def test_crash_is_not_marked_done():
    o = WraithOrchestrator()
    o.current_mode = "DAY"
    o.active_process = _Done(1)
    assert o.check_process_health() is False
    assert o.mode_job_done is False
