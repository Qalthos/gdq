# Copyright 2026
# SPDX-License-Identifier: MIT
import asyncio
from typing import TYPE_CHECKING

from common.display.raw import RawDisplay as Display

if TYPE_CHECKING:
    from bus.desert_bus import DesertBus


async def display(bus: DesertBus) -> None:
    _display = Display()

    def _flush_display(full: bool = False) -> None:  # noqa: FBT001, FBT002
        _display.refresh_terminal()
        _display.update_header(bus.header())
        _display.update_footer(bus.footer())
        if full:
            _display.update_body(bus.render())

    while True:
        _flush_display(True)  # noqa: FBT003
        await asyncio.sleep(0.2)


if __name__ == "__main__":
    from datetime import UTC, datetime

    from bus.desert_bus import DesertBus

    db = DesertBus(datetime.now(UTC))
    asyncio.run(display(db))
