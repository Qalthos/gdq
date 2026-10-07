#!/usr/bin/env python3
# Copyright 2024
# SPDX-License-Identifier: MIT
from __future__ import annotations

import asyncio
import sys
import time
from threading import Thread
from typing import TYPE_CHECKING

from phoenix_channels_python_client import PHXChannelsClient

from bus.db_api import get_events
from bus.desert_bus import DesertBus
from gdq import utils
from gdq.display.raw import Display

if TYPE_CHECKING:
    from phoenix_channels_python_client.phx_messages import ChannelMessage


class DisplayThread(Thread):
    bus: DesertBus
    display: Display

    def __init__(self, bus: DesertBus) -> None:
        super().__init__()
        self.bus = bus
        self.display = Display()

    def run(self) -> None:
        while True:
            utils.update_now()
            self.display.refresh_terminal()
            self.bus.width = self.display.term_w
            self.display.update_header(self.bus.header())
            self.display.update_body(self.bus.render())
            self.display.update_footer(self.bus.footer())
            print(flush=True, end="")
            time.sleep(0.2)


async def init_phoenix(bus: DesertBus, event_id: str) -> None:  # noqa: ARG001

    async def fetch_callback(message: ChannelMessage) -> None:
        print(message.topic)
        print(message.event)
        print(message.payload)

    client = PHXChannelsClient("wss://desertbus.org/api/socket/websocket", api_key="")
    print("Connecting...")
    async with client:
        for topic in ("auctions", "prizes", "total"):
            full_topic = f"{topic}:{event_id}"
            await client.subscribe_to_topic(full_topic, fetch_callback)
        await client.run_forever()


async def run() -> None:
    events = get_events()
    for event in events:
        if event.primary:
            print(event.name)
            # current event
            break
    else:
        print("No primary event found?")
        sys.exit(1)

    bus = DesertBus(start=event.starts_at)
    bus.total = event.total

    display = DisplayThread(bus)
    display.start()

    await init_phoenix(bus, event.id)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
