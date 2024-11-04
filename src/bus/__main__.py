#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import xdg
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub import PNConfiguration, PubNub

from bus.desert_bus import DesertBus
from gdq import utils
from gdq.display.raw import Display
from gdq.money import Dollar

if TYPE_CHECKING:
    from pubnub.models.consumer.common import PNStatus
    from pubnub.models.consumer.history import PNFetchMessagesResult
    from pubnub.models.consumer.pubsub import PNMessageResult


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


class SubscribeHandler(SubscribeCallback):  # type: ignore[misc]
    def __init__(self, bus: DesertBus) -> None:
        super().__init__()
        self.bus = bus

    def message(self, pubnub: PubNub, message: PNMessageResult) -> None:
        self.bus.total = Dollar(message.message)

        now = datetime.now(UTC)
        if bool(now >= self.bus.end):
            pubnub.stop()
            sys.exit(0)


def main() -> None:
    config_path = Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml"
    with config_path.open("rb") as toml_file:
        config = tomllib.load(toml_file)

    event_config = config.get("bus")
    if event_config is None:
        print("No marathon named bus found")
        sys.exit(1)

    bus = DesertBus(start=event_config["start"])

    pn_config = PNConfiguration()
    pn_config.subscribe_key = event_config["key"]
    pn_config.user_id = str(uuid.uuid4())

    channels = "total%3AJNQGRZPRCSSJ,total%3ARZZQRDQNLNLW"

    def fetch_callback(envelope: PNFetchMessagesResult, status: PNStatus) -> None:
        if status.is_error():
            print("Request returned an error!")
            return
        for channel_name, items in envelope.channels.items():
            if channel_name.startswith("total"):
                bus.total = Dollar(items[0].message)

    pubnub = PubNub(pn_config)
    pubnub.add_listener(SubscribeHandler(bus))
    pubnub.subscribe().channels(channels).execute()
    pubnub.fetch_messages().channels(channels).maximum_per_channel(1).pn_async(
        fetch_callback,
    )

    display = DisplayThread(bus)
    display.start()


if __name__ == "__main__":
    main()
