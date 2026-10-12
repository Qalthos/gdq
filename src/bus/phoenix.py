# Copyright 2026
# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING

from phoenix_channels_python_client import PHXChannelsClient

if TYPE_CHECKING:
    import queue

    from phoenix_channels_python_client.phx_messages import ChannelMessage


async def subscribe(q: queue.Queue, event_id: str) -> None:

    async def fetch_callback(message: ChannelMessage) -> None:
        print(message.topic)  # noqa: T201
        print(message.event)  # noqa: T201
        print(message.payload)  # noqa: T201
        if message.topic == "total":
            q.put(message.payload)

    client = PHXChannelsClient("wss://desertbus.org/api/socket/websocket", api_key="")
    print("Connecting...")  # noqa: T201
    async with client:
        for topic in ("auctions", "prizes", "total"):
            full_topic = f"{topic}:{event_id}"
            await client.subscribe_to_topic(full_topic, fetch_callback)
        await client.run_forever()
