from bus.desert_bus import DesertBuck, DesertToonie, next_hours
from bus.records import RECORDS, dollars_to_hours


def test_desert_buck():
    assert DesertBuck(RECORDS[0].total).to_float() == 1


def test_desert_toonie():
    assert DesertToonie(RECORDS[1].total).to_float() == 1


def test_next_hours():
    hours = next_hours(0)
    for i in range(1, 10):
        assert i == dollars_to_hours(next(hours)[0])
