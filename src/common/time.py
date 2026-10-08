# Copyright 2026
# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import timedelta


def timedelta_as_hours(delta: timedelta) -> str:
    """Format a timedelta in HHH:MM format."""

    minutes = delta.total_seconds() // 60
    hours, minutes = divmod(minutes, 60)

    return f"{hours:.0f}:{minutes:02.0f}"
