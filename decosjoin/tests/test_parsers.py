from datetime import date, datetime, time
from unittest.case import TestCase

from freezegun import freeze_time

from decosjoin.api.decosjoin.Exception import ParseError
from decosjoin.api.decosjoin.decosjoin_connection import to_date, to_time, to_datetime, _is_current, to_decision


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

        with self.assertRaises(ParseError):
            self.assertEqual(to_time("text"), time(14, 30))

        with self.assertRaises(ParseError):
            to_time(1)

    def test_to_datetime(self):
        self.assertEqual(to_datetime("2020-06-16T01:01:01"), datetime(2020, 6, 16, 1, 1, 1))
        self.assertEqual(to_datetime("2020-06-16"), datetime(2020, 6, 16, 0, 0, 0))

        self.assertEqual(to_datetime(date(2020, 6, 16)), datetime(2020, 6, 16, 0, 0, 0))
        self.assertEqual(to_datetime(datetime(2020, 6, 16, 1, 1, 1)), datetime(2020, 6, 16, 1, 1, 1))

        with self.assertRaises(ParseError):
            to_date(1)


class IsCurrentTest(TestCase):

    @freeze_time("2020-06-16")
    def test_is_current_date(self):
        zaak = {
            "dateFrom": date(2020, 5, 16),
            "dateEnd": date(2020, 7, 16)
        }
        self.assertTrue(_is_current(zaak))

    @freeze_time("2020-06-16T18:33:00")
    def test_is_current_date_same_date_inclusive(self):
        zaak = {
            "dateFrom": date(2020, 6, 16),
            "dateEndInclusive": date(2020, 6, 16)
        }
        self.assertTrue(_is_current(zaak))

    @freeze_time("2020-06-16T18:33:00")
    def test_is_current_date_same_date(self):
        zaak = {
            "dateFrom": date(2020, 6, 16),
            "dateEnd": date(2020, 6, 16)
        }
        self.assertFalse(_is_current(zaak))

    @freeze_time("2020-06-16T18:33:00")
    def test_is_current_datetime(self):
        zaak = {
            "dateFrom": date(2020, 6, 16),
            "dateEnd": date(2020, 6, 16),
            "timeStart": time(18, 0, 0),
            "timeEnd": time(19, 0, 0),
        }
        self.assertTrue(_is_current(zaak))

    @freeze_time("2020-06-16T18:33:00")
    def test_is_current_datetime_false(self):
        zaak = {
            "dateFrom": date(2020, 6, 16),
            "dateEnd": date(2020, 6, 16),
            "timeStart": time(17, 0, 0),
            "timeEnd": time(18, 0, 0),
        }
        self.assertFalse(_is_current(zaak))
