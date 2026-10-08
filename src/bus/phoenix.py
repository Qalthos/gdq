# Copyright 2026
# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING

from phoenix_channels_python_client import PHXChannelsClient

if TYPE_CHECKING:
    from phoenix_channels_python_client.phx_messages import ChannelMessage

    from bus.desert_bus import DesertBus


async def subscribe(bus: DesertBus, event_id: str) -> None:  # noqa: ARG001

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
