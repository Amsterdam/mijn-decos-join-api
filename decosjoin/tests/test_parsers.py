from datetime import date, datetime, time
from unittest.case import TestCase

from decosjoin.api.decosjoin.decosjoin_connection import (to_date, to_datetime,
                                                          to_decision, to_time)
from decosjoin.api.decosjoin.Exception import ParseError


class ConversionTests(TestCase):

    def test_to_decision(self):
        decision = 'Verleend met borden'
        self.assertEqual(to_decision(decision), 'Verleend')

        decision = 'Niet verleend'
        self.assertEqual(to_decision(decision), 'Niet verleend')

        decision = 'Verleend zonder bebording'
        self.assertEqual(to_decision(decision), 'Verleend')

        decision = 'Verleend zonder'
        self.assertEqual(to_decision(decision), 'Verleend zonder')


class DateParserTests(TestCase):
    def test_to_date(self):
        # this comes from the api most likely
        self.assertEqual(to_date("2020-06-16T00:00:00"), date(2020, 6, 16))
        self.assertEqual(to_date("2020-06-16"), date(2020, 6, 16))

        self.assertEqual(to_date(date(2020, 6, 16)), date(2020, 6, 16))
        self.assertEqual(to_date(datetime(2020, 6, 16, 1, 1, 1)), date(2020, 6, 16))

        with self.assertRaises(ParseError):
            to_date(1)

    def test_to_time(self):
        self.assertEqual(to_time(time(1, 0, 0)), time(1, 0, 0))

        self.assertEqual(to_time("14:30"), time(14, 30))
        self.assertEqual(to_time("14.30"), time(14, 30))

        self.assertIsNone(to_time("30:70"))
        self.assertIsNone(to_time("not parsable"))
        self.assertIsNone(to_time(1))
        self.assertIsNone(None)

    def test_to_datetime(self):
        self.assertEqual(to_datetime("2020-06-16T01:01:01"), datetime(2020, 6, 16, 1, 1, 1))
        self.assertEqual(to_datetime("2020-06-16"), datetime(2020, 6, 16, 0, 0, 0))

        self.assertEqual(to_datetime(date(2020, 6, 16)), datetime(2020, 6, 16, 0, 0, 0))
        self.assertEqual(to_datetime(datetime(2020, 6, 16, 1, 1, 1)), datetime(2020, 6, 16, 1, 1, 1))

        with self.assertRaises(ParseError):
            to_date(1)
