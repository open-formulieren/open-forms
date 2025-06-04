from django.test import TestCase

from freezegun import freeze_time

from openforms.contrib.haal_centraal.data import (
    NaturalPersonDetails as HC_NaturalPersonDetails,
)
from stuf.stuf_bg.data import NaturalPersonDetails as StUFBG_NaturalPersonDetails

from ..filters import filter_members_by_age


@freeze_time("2025-04-25T18:00:00+01:00")
class FamilyMembersFiltersTests(TestCase):
    def test_age_filter_with_empty_input(self):
        data = []
        filtered_results = filter_members_by_age(results=data, min_age=18, max_age=30)

        self.assertEqual(filtered_results, [])

    def test_age_filter_with_missing_date_of_birth(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest(type(item)):
                filtered_results = filter_members_by_age(
                    results=[item], min_age=18, max_age=30
                )
                self.assertEqual(filtered_results, [])

    def test_min_age_passes(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-01-19",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-01-19",
        )

        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=[hc_item], min_age=18)

            self.assertEqual(
                filtered_results,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-01-19",
                        date_of_birth_precision="date",
                    ),
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=[stuf_bg_item], min_age=18)

            self.assertEqual(
                filtered_results,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-01-19",
                    ),
                ],
            )

    def test_min_age_fails(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2017-01-19",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2017-01-19",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest(type(item)):
                filtered_results = filter_members_by_age(results=[item], min_age=18)
                self.assertEqual(filtered_results, [])

    def test_max_age_passes(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-01-19",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-01-19",
        )

        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=[hc_item], max_age=30)

            self.assertEqual(
                filtered_results,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-01-19",
                        date_of_birth_precision="date",
                    ),
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=[stuf_bg_item], max_age=30)

            self.assertEqual(
                filtered_results,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-01-19",
                    ),
                ],
            )

    def test_max_age_fails(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="1986-01-19",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="1986-01-19",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest(type(item)):
                filtered_results = filter_members_by_age(results=[item], max_age=30)
                self.assertEqual(filtered_results, [])

    def test_min_age_depending_on_the_exact_day(self):
        # birthday not occured yet
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-26",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-26",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest(type(item)):
                filtered_results = filter_members_by_age(results=[item], min_age=18)
                self.assertEqual(filtered_results, [])

        # birthday occured
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-24",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-24",
        )

        with self.subTest("haal_centraal"):
            filtered_results2 = filter_members_by_age(results=[hc_item], min_age=18)

            self.assertEqual(
                filtered_results2,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-04-24",
                        date_of_birth_precision="date",
                    )
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results2 = filter_members_by_age(
                results=[stuf_bg_item], min_age=18
            )

            self.assertEqual(
                filtered_results2,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-04-24",
                    )
                ],
            )

    def test_max_age_depending_on_the_exact_day(self):
        # birthday not occured yet
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-26",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2007-04-26",
        )

        with self.subTest("haal_centraal"):
            filtered_results1 = filter_members_by_age(results=[hc_item], max_age=18)

            self.assertEqual(
                filtered_results1,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-04-26",
                        date_of_birth_precision="date",
                    )
                ],
            )

        with self.subTest("haal_centraal"):
            filtered_results2 = filter_members_by_age(
                results=[stuf_bg_item], max_age=18
            )

            self.assertEqual(
                filtered_results2,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        last_name="Pirsen",
                        date_of_birth="2007-04-26",
                    )
                ],
            )

        # birthday occured
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2006-04-24",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="2006-04-24",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest(type(item)):
                filtered_results = filter_members_by_age(results=[item], max_age=18)
                self.assertEqual(filtered_results, [])

    def test_missing_date_of_birth_fails(self):
        hc_item = HC_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="",
            date_of_birth_precision="date",
        )

        stuf_bg_item = StUFBG_NaturalPersonDetails(
            bsn="123456788",
            first_names="Doe",
            last_name="Pirsen",
            date_of_birth="",
        )

        for item in (hc_item, stuf_bg_item):
            with self.subTest():
                filtered_results = filter_members_by_age(
                    results=[item], min_age=18, max_age=30
                )
                self.assertEqual(filtered_results, [])

    def test_incomplete_dates_of_birth(self):
        with self.subTest("haal_centraal"):
            # year and month
            hc_item = HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                last_name="Pirsen",
                date_of_birth="2002-01",
                date_of_birth_precision="year_month",
            )

            filtered_results1 = filter_members_by_age(results=[hc_item], min_age=18)

            self.assertEqual(filtered_results1, [])

            # year
            hc_item = HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                last_name="Pirsen",
                date_of_birth="2002",
                date_of_birth_precision="year",
            )

            filtered_results2 = filter_members_by_age(results=[hc_item], min_age=18)

            self.assertEqual(filtered_results2, [])

        with self.subTest("stuf_bg"):
            # year and month
            stuf_bg_item = StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                last_name="Pirsen",
                date_of_birth="2002-01",
            )

            filtered_results1 = filter_members_by_age(
                results=[stuf_bg_item], min_age=18
            )

            self.assertEqual(filtered_results1, [])

            # year
            stuf_bg_item = StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                last_name="Pirsen",
                date_of_birth="2002",
            )

            filtered_results2 = filter_members_by_age(
                results=[stuf_bg_item], min_age=18
            )

            self.assertEqual(filtered_results2, [])
