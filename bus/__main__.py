#!/usr/bin/env python3
import sys
import time
import tomllib
from pathlib import Path
from threading import Thread

import requests
import xdg
from pubnub.enums import PNReconnectionPolicy
from pubnub.pubnub import PNConfiguration, PubNub, SubscribeCallback

from bus.desert_bus import DesertBus
from gdq import utils
from gdq.display.raw import Display
from gdq.money import Dollar


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
            print(flush=True)
            time.sleep(1)


class SubscribeHandler(SubscribeCallback):
    def __init__(self, bus: DesertBus, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bus = bus

    def message(self, pubnub, message) -> None:
        self.bus.total = Dollar(message.message)

        if bool(utils.now <= self.bus.end):
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
    state = requests.get("https://desertbus.org/wapi/init", timeout=10).json()
    bus.total = Dollar(state["total"])

    display = DisplayThread(bus)
    display.start()

    pn_config = PNConfiguration()
    pn_config.reconnect_policy = PNReconnectionPolicy.EXPONENTIAL
    pn_config.subscribe_key = event_config["key"]
    pn_config.uuid = event_config["uuid"]

    pubnub = PubNub(pn_config)
    pubnub.add_listener(SubscribeHandler(bus))
    pubnub.subscribe().channels("db_total").execute()


if __name__ == "__main__":
    main()
