#!/usr/bin/env python3
import sys
import threading
import time
from pathlib import Path

import tomllib
import xdg
from pubnub.enums import PNReconnectionPolicy
from pubnub.pubnub import PNConfiguration, PubNub, SubscribeCallback

from bus.desert_bus import DesertBus
from gdq import utils
from gdq.display.raw import Display
from gdq.money import Dollar


def update_display(bus: DesertBus) -> None:
    display = Display()
    while True:
        utils.update_now()
        display.refresh_terminal()

        bus.width = display.term_w
        display.update_header(bus.header())
        display.update_body(bus.render())
        display.update_footer(bus.footer())
        print(flush=True, end="")
        time.sleep(0.1)


def update_bus(bus: DesertBus, message) -> None:
    bus.total = Dollar(message.message)


class SubscribeHandler(SubscribeCallback):
    def __init__(self, bus: DesertBus, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus = bus

    def message(self, pubnub, message) -> None:
        # print(message.__dict__)
        update_bus(self.bus, message)

        if bool(utils.now >= self.bus.end):
            pubnub.stop()
            sys.exit(0)


def main() -> None:
    toml_path = Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml"
    with open(toml_path, "rb") as toml_file:
        config = tomllib.load(toml_file)

    event_config = config.get("bus")
    if event_config is None:
        print("No marathon named bus found")
        sys.exit(1)

    bus = DesertBus(**event_config)
    bus.total = Dollar(0)

    config = PNConfiguration()
    config.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
    config.subscribe_key = "sub-cbd7f5f5-1d3f-11e2-ac11-877a976e347c"
    config.uuid = "b71bca24-0ad6-463b-9c47-953bfb0c120a"

    def fetch_callback(envelope, status):
        if status.is_error():
            return
        if "db_total" in envelope.channels:
            message = envelope.channels["db_total"][0]
            update_bus(bus, message)

    pubnub = PubNub(config)
    pubnub.add_listener(SubscribeHandler(bus))
    pubnub.subscribe().channels("db_total").execute()
    pubnub.fetch_messages().channels("db_total").maximum_per_channel(1).pn_async(
        fetch_callback
    )

    display_thread = threading.Thread(
        target=update_display,
        args=(bus,),
    )
    display_thread.start()


if __name__ == "__main__":
    main()
