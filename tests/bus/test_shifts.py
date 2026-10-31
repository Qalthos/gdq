# Copyright 2026
# SPDX-License-Identifier: MIT
from bus import shifts
from bus.shifts import Omega


def test_shift_basic() -> None:
    shift_name = "Shift"
    shift = Omega(0, shift_name)

    assert str(shift) == shift_name
    assert len(shift) == len(shift_name)


def test_shift_active(monkeypatch) -> None:  # noqa: ANN001
    shift = shifts.SHIFTS[0]

    for hour in range(6, 12):
        monkeypatch.setattr(shifts, "_current_hour", lambda: hour)  # noqa: B023
        assert shift.is_active()

    assert shift.colorize("test") == "\x1b[33;7mtest\x1b[0m"


def test_shift_inactive(monkeypatch) -> None:  # noqa: ANN001
    shift = shifts.SHIFTS[3]

    for hour in range(6, 24):
        monkeypatch.setattr(shifts, "_current_hour", lambda: hour)  # noqa: B023
        assert not shift.is_active()

    assert shift.colorize("test") == "\x1b[35;2mtest\x1b[0m"
