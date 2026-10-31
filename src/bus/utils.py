# Copyright 2026
# SPDX-License-Identifier: MIT
import math

from common.money import Dollar, Money

RATE = 1.07


def dollars_to_hours(dollars: Money) -> int:
    # NOTE: This is not reflexive with hours_to_dollars
    # Slight correction factor to account for sub-cent losses
    raw_value = dollars.to_float() + 0.005
    value = math.log((RATE - 1) * raw_value + 1) / math.log(RATE)
    return math.floor(value)


def hours_to_dollars(hours: int, currency: type[Money] = Dollar) -> Money:
    value = (RATE**hours - 1) / (RATE - 1)
    return currency(value)


def wingding(in_s: str) -> str:
    source = "$(),-.0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    dest = "👓🕿✆📪📫📬📁📂📄🗏🗐🗄⌛🖮🖰🖲🖳✌👌👍👎☜☞☝☟🖐☺😐☹💣☠🏳🏱✈☼💧❄🕆✞🕈✠✡☪♋♌♍♎♏♐♑♒♓🙰🙵●🔾■□🞐❑❒⬧⧫◆❖⬥⌧⮹⌘"
    t = str.maketrans(source, dest)
    return in_s.translate(t)
