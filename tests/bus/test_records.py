import pytest
from bus.records import RECORDS, Record, dollars_to_hours, hours_to_dollars
from gdq.money import Dollar


@pytest.mark.parametrize(
    ("dollars", "hours"),
    [
        (58.17, 23),
        (58.18, 24),
        (353.27, 47),
        (353.28, 48),
    ],
)
def test_dollars_to_hours(dollars: float, hours: int):
    # Hours are returned as integers, ensure that the hour count changes
    # at the appropriate dollar level.
    assert dollars_to_hours(Dollar(dollars)) == hours


@pytest.mark.parametrize("hour", range(48))
def test_hours_to_dollars(hour: int):
    # Dollars are returned to the nearest penny and not the next penny
    # despite the error involved.
    assert hours_to_dollars(hour) == Dollar(sum(1.07**i for i in range(hour)))


@pytest.mark.parametrize("record", [RECORDS[0]])
def test_record_name(record: Record):
    assert str(record) == "Desert Bus For Hope"
