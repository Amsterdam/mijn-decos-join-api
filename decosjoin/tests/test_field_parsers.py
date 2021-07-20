from datetime import date, datetime, time
from unittest.case import TestCase

from decosjoin.api.decosjoin.field_parsers import (
    get_translation,
    to_date,
    to_datetime,
    to_int,
    to_string,
    to_string_if_exists,
    to_string_or_empty_string,
    to_time,
)


class ValueParserTests(TestCase):
    def test_to_string(self):
        self.assertEqual(to_string("     test    "), "test")
        self.assertEqual(to_string("test"), "test")
        self.assertEqual(to_string("1"), "1")
        self.assertEqual(to_string(1), "1")

    def test_to_string_or_empty_string(self):
        self.assertEqual(to_string_or_empty_string("test"), "test")
        self.assertEqual(to_string_or_empty_string(None), "")
        self.assertEqual(to_string_or_empty_string(False), "")
        self.assertEqual(to_string_or_empty_string(0), "")
        self.assertEqual(to_string_or_empty_string("False"), "False")

    def test_to_string_if_exists(self):
        zaak = {
            "foo": "bar",
            "bliep": "    blap     ",
        }
        self.assertEqual(to_string_if_exists(zaak, "foo"), "bar")
        self.assertEqual(to_string_if_exists(zaak, "bliep"), "blap")
        self.assertEqual(to_string_if_exists(zaak, "hello"), None)
        self.assertEqual(
            to_string_if_exists(zaak, "hello", "default_value"), "default_value"
        )

    def test_to_int(self):
        self.assertEqual(to_int("1"), 1)


class TranslationParserTests(TestCase):
    def test_get_translations(self):
        translations = [
            ["a", "1Aa", True],
            ["b", "2Aa", False],
            ["C", "3Aa", True],
            ["D", "4Aa", False],
        ]
        self.assertEqual(get_translation("a", translations), "1Aa")
        self.assertEqual(get_translation("A", translations), "1Aa")
        self.assertIsNone(get_translation("b", translations))
        self.assertEqual(get_translation("c", translations), "3Aa")
        self.assertIsNone(get_translation("d", translations))
        self.assertIsNone(get_translation("Nope", translations))

    def test_get_translation(self):
        translations = [["foo", "bar"]]
        self.assertEqual(
            get_translation("test_trans1", translations, True), "test_trans1"
        )
        self.assertEqual(get_translation("test_trans1", translations, False), None)


class DateParserTests(TestCase):
    def test_to_date(self):
        # this comes from the api most likely
        self.assertEqual(to_date("2020-06-16T00:00:00"), date(2020, 6, 16))
        self.assertEqual(to_date("2020-06-16"), date(2020, 6, 16))

        self.assertEqual(to_date(date(2020, 6, 16)), date(2020, 6, 16))
        self.assertEqual(to_date(datetime(2020, 6, 16, 1, 1, 1)), date(2020, 6, 16))

        self.assertEqual(to_date(1), None)

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
        self.assertEqual(
            to_datetime("2020-06-16T01:01:01"), datetime(2020, 6, 16, 1, 1, 1)
        )
        self.assertEqual(to_datetime("2020-06-16"), datetime(2020, 6, 16, 0, 0, 0))

        self.assertEqual(to_datetime(date(2020, 6, 16)), datetime(2020, 6, 16, 0, 0, 0))
        self.assertEqual(
            to_datetime(datetime(2020, 6, 16, 1, 1, 1)), datetime(2020, 6, 16, 1, 1, 1)
        )

        self.assertEqual(to_datetime(1), None)
