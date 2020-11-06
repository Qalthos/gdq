#!/usr/bin/env python3
import argparse
import sys
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import toml
import xdg

from gdq import runners, utils
from gdq.display.raw import Display
from gdq.events import Marathon


def refresh_event(marathon: Marathon, base_args: argparse.Namespace, event_args: argparse.Namespace) -> bool:
    # Recaclulate terminal size
    marathon.refresh_all()

    for _ in utils.slow_refresh_with_progress(base_args.interval):
        # Update current time for display.
        utils.update_now()

        display = Display()
        display.update_header(marathon.header(width=display.term_w, args=event_args))
        display.update_body(marathon.render(width=display.term_w, args=event_args))
        display.update_footer(marathon.footer(width=display.term_w, args=event_args))
        if base_args.oneshot:
            return False

    return True


def list_events(config: Mapping[str, Any]) -> None:
    event_times: dict[str, tuple[datetime, Optional[datetime]]] = {}
    for name, marathon_config in utils.show_iterable_progress(config.items(), offset=1):
        runner = runners.get_runner(marathon_config)
        try:
            event_times[name] = runner.get_times()
        except Exception as exc:
            print(f"{name}: {exc!s}")

    for name, (start, end) in sorted(event_times.items(), key=lambda x: x[1]):
        if end is None:
            end = start.astimezone() + timedelta(days=7)

        if utils.now < start:
            print(f"{name} will start in {start - utils.now}")
        elif end < utils.now:
            print(f"{name} finished on {end}")
        else:
            print(f"{name} is ongoing")


def main() -> None:
    with open(Path(xdg.XDG_CONFIG_HOME) / "gdq" / "config.toml") as toml_file:
        config = toml.load(toml_file)

    base_parser = runners.get_base_parser()
    base_args, extra_args = base_parser.parse_known_args()

    if base_args.list:
        list_events(config)
        sys.exit(0)

    event_config = config.get(base_args.stream_name)
    if event_config is None:
        print(f"No marathon named {base_args.stream_name} found")
        sys.exit(1)

    runner = runners.get_runner(event_config, extra_args)

    try:
        marathon = runner.get_marathon()
    except KeyError as exc:
        print(str(exc))
        sys.exit(2)

    active = True
    while active:
        try:
            active = refresh_event(marathon, base_args, runner.args)
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
