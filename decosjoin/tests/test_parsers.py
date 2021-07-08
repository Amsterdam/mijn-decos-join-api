from datetime import date, datetime, time
from unittest.case import TestCase

from decosjoin.api.decosjoin.Exception import ParseError
from decosjoin.api.decosjoin.decosjoin_connection import to_date, to_time, to_datetime, to_decision, to_title


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

    def test_to_title(self):
        test_value = 'TVM - RVV - Object'
        self.assertEqual(to_title(test_value), 'Tijdelijke verkeersmaatregel')

        test_value = 'GPP'
        self.assertEqual(to_title(test_value), 'Vaste parkeerplaats voor gehandicapten (GPP)')

        test_value = 'GPK'
        self.assertEqual(to_title(test_value), 'Europse gehandicaptenparkeerkaart (GPK)')

        test_value = 'Omzettingsvergunning'
        self.assertEqual(to_title(test_value), 'Vergunning voor kamerverhuur')

        test_value = 'E-RVV - TVM'
        self.assertEqual(to_title(test_value), 'e-RVV (Gratis verkeersontheffing voor elektrisch goederenvervoer)')

        test_value = 'Vakantieverhuur afmelding'
        self.assertEqual(to_title(test_value), 'Geannuleerde verhuur')

        test_value = 'Vakantieverhuur'
        self.assertEqual(to_title(test_value), 'Geplande verhuur')

        test_value = 'B&B - vergunning'
        self.assertEqual(to_title(test_value), 'Vergunning bed & breakfast')

        test_value = 'Vakantieverhuur vergunningsaanvraag'
        self.assertEqual(to_title(test_value), 'Vergunning vakantieverhuur')


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
        self.assertEqual(to_time(datetime(2021, 5, 25, 1, 0, 0)), "01:00")
        self.assertEqual(to_time(time(1, 0, 0)), "01:00")

        self.assertEqual(to_time("14:30"), "14:30")
        self.assertEqual(to_time("14.30"), "14:30")

        self.assertEqual(to_time("24.00"), "24:00")

        self.assertIsNone(to_time("30:70"))
        self.assertIsNone(to_time("24:01"))
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
