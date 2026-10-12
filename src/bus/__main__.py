#!/usr/bin/env python3
# Copyright 2023
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import sys
import threading

from bus.db_api import get_primary
from bus.desert_bus import DesertBus
from bus.display import display
from bus.phoenix import subscribe


async def run() -> None:
    try:
        event = get_primary()
    except RuntimeError as exc:
        print(exc)  # noqa: T201
        sys.exit(1)

    bus = DesertBus(start=event.starts_at)
    bus.total = event.total

    display_thread = threading.Thread(target=lambda: asyncio.run(display(bus)))
    display_thread.start()

    await subscribe(bus, event.id)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
