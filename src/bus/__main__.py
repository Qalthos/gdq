#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
import tomllib
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING

import xdg
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub import PNConfiguration, PNStatusCategory, PubNub

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

    def status(self, pubnub: PubNub, status: PNStatus) -> None:
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            print("disconnected")
            pubnub.reconnect()
        elif status.category == PNStatusCategory.PNTimeoutCategory:
            print("timeout")
            pubnub.reconnect()

    def message(self, pubnub: PubNub, message: PNMessageResult) -> None:
        self.bus.total = Dollar(message.message)

        now = datetime.now(UTC)
        if bool(now >= (self.bus.end + timedelta(hours=2))):
            pubnub.stop()
            sys.exit(0)


def init_pubnub(key: str, channel: str, bus: DesertBus) -> None:
    pn_config = PNConfiguration()
    pn_config.subscribe_key = key
    pn_config.user_id = str(uuid.uuid4())

    pubnub = PubNub(pn_config)
    pubnub.add_listener(SubscribeHandler(bus))

    def fetch_callback(envelope: PNFetchMessagesResult, status: PNStatus) -> None:
        if status and status.is_error():
            print("Request returned an error!")
            return
        for channel_name, items in envelope.channels.items():
            if channel_name == channel:
                print(items[0].message)
                bus.total = Dollar(items[0].message)

    # Fetch current total
    pubnub.fetch_messages().channels(channel).maximum_per_channel(1).pn_async(
        fetch_callback,
    )

    # Subscribe to updates
    data_channel = pubnub.channel(channel).subscription()
    data_channel.subscribe()


def main() -> None:
    config_path = Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml"
    with config_path.open("rb") as toml_file:
        config = tomllib.load(toml_file)

    event_config = config.get("bus")
    if event_config is None:
        print("No marathon named bus found")
        sys.exit(1)

    bus = DesertBus(start=event_config["start"])
    init_pubnub(event_config["key"], event_config["channel"], bus)

    display = DisplayThread(bus)
    display.start()


if __name__ == "__main__":
    main()
