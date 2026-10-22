# Copyright 2026
# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING

from phoenix_channels_python_client import PHXChannelsClient

if TYPE_CHECKING:
    import queue

    from phoenix_channels_python_client.phx_messages import ChannelMessage


async def subscribe(q: queue.Queue, event_id: str) -> None:
    async def event_callback(message: ChannelMessage) -> None:
        q.put({message.event: message.payload})

    client = PHXChannelsClient("wss://desertbus.org/api/socket/websocket", api_key="")
    topics = ("auctions", "prizes", "total")
    async with client:
        for topic in topics:
            await client.subscribe_to_topic(f"{topic}:{event_id}", event_callback)
        await client.run_forever()
