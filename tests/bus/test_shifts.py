# Copyright 2026
# SPDX-License-Identifier: MIT
from bus import shifts


def test_shift_active(monkeypatch) -> None:  # noqa: ANN001
    shift = shifts.SHIFTS[0]

    for hour in range(6, 12):
        monkeypatch.setattr(shifts, "_current_hour", lambda: hour)  # noqa: B023
        assert shift.is_active()

    assert str(shift) == "\x1b[33;7mDawn Guard\x1b[0m"


def test_shift_inactive(monkeypatch) -> None:  # noqa: ANN001
    shift = shifts.SHIFTS[3]

    for hour in range(6, 24):
        monkeypatch.setattr(shifts, "_current_hour", lambda: hour)  # noqa: B023
        assert not shift.is_active()

    assert str(shift) == "\x1b[35;2mZeta\x1b[0m"
