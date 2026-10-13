# Copyright 2026
# SPDX-License-Identifier: MIT
def short_number(number: float) -> str:
    if number >= 1_000_000:  # noqa: PLR2004
        number = number // 10_000 / 100
        return f"{number:.2f}M"
    if number >= 100_000:  # noqa: PLR2004
        number = number // 1_000
        return f"{number:.0f}k"
    if number >= 10_000:  # noqa: PLR2004
        number = number // 100 / 10
        return f"{number:.1f}k"
    if number < 100:  # noqa: PLR2004
        return f"{number:.2f}"
    return f"{number:,.0f}"
