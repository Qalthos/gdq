# Copyright 2026
# SPDX-License_identifier: MIT
from common.display import SquishableString


def test_center() -> None:
    ss = SquishableString("12345", str.center)

    s = ss.render(10)
    assert s == "  12345   "
