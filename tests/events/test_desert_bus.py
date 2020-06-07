from gdq.events.desert_bus import dollars_to_hours, hours_to_dollars
from gdq.money import Dollar


class TestDesertBus:
    def test_dollars_to_hours(self):
        # Hours are returned as integers, ensure that the hour count changes
        # at the appropriate dollar level.
        assert dollars_to_hours(Dollar(58.17)) == 23
        assert dollars_to_hours(Dollar(58.18)) == 24

        assert dollars_to_hours(Dollar(353.27)) == 47
        assert dollars_to_hours(Dollar(353.28)) == 48

    def test_hours_to_dollars(self):
        # Dollars are returned to the nearest penny and not the next penny
        # despite the error involved.
        assert hours_to_dollars(24) == Dollar(sum(1.07 ** i for i in range(24)))
        assert hours_to_dollars(48) == Dollar(sum(1.07 ** i for i in range(48)))
