import unittest

from bs4 import BeautifulSoup

from gdq import events
from gdq.parsers import gdq_tracker


class TestGDQ(unittest.TestCase):
    def test_read_total(self):
        html = """<small>
            Donation Total:
            $49,285.88 (986) —
            Max/Avg Donation:
            $4,000.00/$49.99
        </small>"""
        soup = BeautifulSoup(html, "html.parser")

        total = gdq_tracker.read_total(soup, events.MarathonBase.donation_re, atof=events.MarathonBase._atof)
        self.assertEqual(total, 49285.88)

    def test_read_total_euro(self):
        html = """<small>
           Donation Total:
            € 37 643,96 (2598) —
           Max/Avg Donation:
            € 777,77/€ 14,49
        </small>"""
        soup = BeautifulSoup(html, "html.parser")

        total = gdq_tracker.read_total(soup, events.MarathonBaseEuro.donation_re, atof=events.MarathonBaseEuro._atof)
        self.assertEqual(total, 37643.96)
