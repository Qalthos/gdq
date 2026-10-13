# Copyright 2026
# SPDX-License-Identifier: MIT
import asyncio
import queue
from typing import TYPE_CHECKING

from bus.desert_bus import DesertBus
from common.display.raw import RawDisplay as Display

if TYPE_CHECKING:
    from bus.db_api import Event


async def display(event: Event, q: queue.Queue) -> None:
    _display = Display()
    bus = DesertBus(event.starts_at, event.total)

    def _flush_display(*, full: bool = False) -> None:
        _display.refresh_terminal()
        _display.update_header(bus.header())
        _display.update_footer(bus.footer())
        if full:
            _display.update_body(bus.render())

    _flush_display(full=True)
    while True:
        full = False
        try:
            total = q.get_nowait()
            bus.update_total(total)
            full = True
        except queue.Empty:
            pass
        except queue.ShutDown:
            break

        _flush_display(full=full)
        await asyncio.sleep(0.2)
