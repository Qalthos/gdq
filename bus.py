#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
import math
import operator

import requests

from gdq import utils


START = datetime(2019, 11, 8, 16, tzinfo=timezone.utc)
SHIFTS = [
    {"color": "\x1b[33", "hour": 20, "name": "Dawn Guard"},
    {"color": "\x1b[31", "hour": 2, "name": "Alpha Flight"},
    {"color": "\x1b[34", "hour": 8, "name": "Night Watch"},
    {"color": "\x1b[35", "hour": 14, "name": "Zeta"},
]
RECORDS = {
    22_805.00: {"year": 2007, "name": "Desert Bus for Hope"},
    70_423.79: {"year": 2008, "name": "Desert Bus for Hope 2: Bus Harder"},
    140_449.68: {"year": 2009, "name": "Desert Bus for Hope 3: It's Desert Bus 6 in Japan"},
    209_400.82: {"year": 2010, "name": "Desert Bus for Hope 4: A New Hope"},
    383_125.10: {"year": 2011, "name": "Desert Bus for Hope 5: De5ert Bus"},
    443_630.00: {"year": 2012, "name": "Desert Bus for Hope 6: Desert Bus 3 in America"},
    523_520.00: {"year": 2013, "name": "Desert Bus for Hope 007"},
    643_242.58: {"year": 2014, "name": "Desert Bus for Hope 8"},
    683_720.00: {"year": 2015, "name": "Desert Bus for Hope 9: The Joy of Bussing"},
    695_242.57: {"year": 2016, "name": "Desert Bus X"},
    655_402.56: {"year": 2017},
    730_289.37: {"year": 2018},
    865_000.00: {"year": 2019},
}
terminal = utils.Terminal()


def refresh_bus():
    utils.NOW = datetime.now(timezone.utc).replace(microsecond=0)
    terminal.refresh()

    # Money raised
    state = requests.get("https://desertbus.org/wapi/init").json()
    total = state["total"]
    hours = dollars_to_hours(total)

    # Clear screen & reset cursor position
    print("\x1b[2J\x1b[H", end="")

    if utils.NOW < START:
        print(f"Starting in {START - utils.NOW}")
    elif utils.NOW < (START + timedelta(hours=hours + 1)):
        print(shift_banners())
    else:
        print("It's over!")

    desert_buck, desert_toonie = list(RECORDS.keys())[:2]
    print(f"${total:,.2f} | {math.floor(hours)} hours | d฿{total / desert_buck:,.2f} | d฿²{total / desert_toonie:,.2f}")

    if utils.NOW > START:
        if utils.NOW < START + (timedelta(hours=(hours + 1))):
            print(calculate_estimate(total))
            print_records(total, hours)
            print(f"\x1b[{terminal.height - 1}H{bus_progress(hours)}")
        else:
            return False

    utils.slow_progress_bar(terminal)
    return True


def shift_banners():
    # Shift detection
    shifts = sorted(SHIFTS, key=operator.itemgetter("hour"))
    for shift in shifts:
        if utils.NOW.hour < shift["hour"]:
            break
    else:
        shift = shifts[0]

    banners = []
    min_width = 10 + 12 + 11 + 4 + 3

    reflow = 0
    if terminal.width <= (11 * 4) + 3:
        shift_width = 0
        if terminal.width >= min_width:
            reflow = min_width - terminal.width
    else:
        shift_width = (terminal.width - 3) // 4
        reflow = terminal.width - 3 - (shift_width * 4)

    for index, shift_info in enumerate(SHIFTS):
        boldness = '2'
        if shift_info == shift:
            boldness = '7'

        mod = 0
        if reflow < 0 and index == 3:
            mod = 4 - reflow
        elif index < reflow:
            mod = 1
        banners.append(f"{shift_info['color']};{boldness}m{shift_info['name'].center(shift_width+mod, '═')}\x1b[0m")

    return '|'.join(banners)


def calculate_estimate(total):
    future_hours = 0
    future_total = total
    while future_hours != dollars_to_hours(future_total):
        future_hours = dollars_to_hours(future_total)
        future_total = (total * timedelta(hours=future_hours)) / (utils.NOW - START)
    return f"${future_total:,.2f} estimated total ({future_hours} hours)"


def bus_progress(hours, overall=False):
    td_bussed = utils.NOW - START
    td_total = timedelta(hours=math.floor(hours))

    hours_done = f"[{timedelta_as_hours(td_bussed)}]"
    hours_left = f"[-{timedelta_as_hours(START + td_total - utils.NOW)}]"
    progress_width = terminal.width - len(hours_done) - len(hours_left) - 3

    # Scaled to last passed record
    last_record = timedelta()
    future_stops = []

    for record in sorted(RECORDS.keys()):
        td_record = timedelta(hours=dollars_to_hours(record))
        if td_record <= td_bussed:
            # We've passed this record, but make a note that we've come this far.
            last_record = td_record
        elif td_record < td_total:
            # In the future, but still on the hook for it.
            future_stops.append(td_record)
        else:
            # Don't worry about records we havent reached yet.
            break

    if overall:
        percent_done = td_bussed / td_total
        last_record = timedelta()
    else:
        percent_done = (last_record - td_bussed) / (last_record - td_total)
    bussed_width = math.floor(progress_width * percent_done)
    bus = f"{'─' * bussed_width}🚍{' ' * (progress_width - bussed_width - 1)}🏁"

    for stop in future_stops:
        stop_location = math.floor(((last_record - stop) / (last_record - td_total)) * progress_width)
        if bus[stop_location:stop_location+2] == "  ":
            bus = bus[:stop_location] + "🚏" + bus[stop_location+2:]

    return f"{hours_done}{bus}{hours_left}\x1b[0m"


def print_records(total, hours):
    # This number doesn't agree with anyone, and I don't know why
    #print(f"${total + sum(RECORDS.keys()):,.2f} lifetime total.")
    print()

    last_hour = math.floor(hours)
    next_level = 0
    for record, event in sorted(RECORDS.items()):
        if record > total:
            hours = dollars_to_hours(record)
            while hours > last_hour:
                last_hour += 1
                next_hour = hours_to_dollars(last_hour) - total
                print(f"${next_hour:,.2f} until hour {last_hour}")

            next_level = record - total
            if "name" in event:
                print(f"${next_level:,.2f} until {event['name']}")
            else:
                print(f"${next_level:,.2f} until Desert Bus {event['year']}")

    if next_level == 0:
        print("NEW RECORD!")

    last_hour += 1
    print(f"${hours_to_dollars(last_hour) - total:,.2f} until hour {last_hour}")


def dollars_to_hours(dollars, rate=1.07):
    # NOTE: This is not reflexive with hours_to_dollats
    return math.floor(math.log((dollars * (rate - 1)) + 1) / math.log(rate))


def hours_to_dollars(hours, rate=1.07):
    return (1 - (rate ** hours)) / (1 - rate)


def timedelta_as_hours(delta: timedelta) -> str:
    """Format a timedelta in HHH:MM format."""

    minutes = delta.total_seconds() / 60
    hours, minutes = divmod(minutes, 60)
    # Avoid :60
    if math.ceil(minutes) == 60:
        hours, minutes = hours + 1, 0
    return f"{hours:.0f}:{minutes:02.0f}"


def main():
    while True:
        try:
            if refresh_bus() is False:
                break
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
