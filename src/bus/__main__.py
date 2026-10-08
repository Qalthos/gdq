#!/usr/bin/env python3
# Copyright 2023
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import sys
import time
from threading import Thread

from bus.db_api import get_primary
from bus.desert_bus import DesertBus
from bus.phoenix import subscribe
from common.display.raw import Display


class DisplayThread(Thread):
    bus: DesertBus
    display: Display

    def __init__(self, bus: DesertBus) -> None:
        super().__init__()
        self.bus = bus
        self.display = Display()

    def run(self) -> None:
        while True:
            self.display.refresh_terminal()
            self.bus.width = self.display.term_w
            self.display.update_header(self.bus.header())
            self.display.update_body(self.bus.render())
            self.display.update_footer(self.bus.footer())
            print(flush=True, end="")
            time.sleep(0.2)


async def run() -> None:
    try:
        event = get_primary()
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)

    bus = DesertBus(start=event.starts_at)
    bus.total = event.total

    display = DisplayThread(bus)
    display.start()

    await subscribe(bus, event.id)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
