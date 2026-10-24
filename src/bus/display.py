# Copyright 2026
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import queue
from typing import TYPE_CHECKING

from bus.desert_bus import DesertBus
from common.display.raw import RawDisplay as Display

if TYPE_CHECKING:
    from bus.db_api import Event


async def display(event: Event, q: queue.Queue) -> None:
    _display = Display()
    bus = DesertBus(event.id, event.starts_at, event.total)

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
            match q.get_nowait():
                case {"auction": auction}:
                    bus.update_auction(auction)
                case {"total": total}:
                    bus.update_total(total)
                case {"prize": prize}:
                    bus.update_prize(prize)
                case other:
                    print(f"unknown message {other}")  # noqa: T201
            full = True
        except queue.Empty:
            pass
        except queue.ShutDown:
            break

        _flush_display(full=full)
        await asyncio.sleep(0.2)
