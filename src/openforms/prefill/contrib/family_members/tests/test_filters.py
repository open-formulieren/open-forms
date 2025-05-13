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
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="",
            ),
        ]

        for data in (HC_DATA, STUF_BG_DATA):
            with self.subTest():
                filtered_results = filter_members_by_age(
                    results=data, min_age=18, max_age=30
                )
                self.assertEqual(filtered_results, [])

    def test_min_age_passes(self):
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-01-19",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-01-19",
            ),
        ]
        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(
                filtered_results,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-01-19",
                        date_of_birth_precision="date",
                    ),
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(
                filtered_results,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-01-19",
                    ),
                ],
            )

    def test_min_age_fails(self):
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2017-01-19",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2017-01-19",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(filtered_results, [])

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(filtered_results, [])

    def test_max_age_passes(self):
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-01-19",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-01-19",
            ),
        ]
        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=HC_DATA, max_age=30)

            self.assertEqual(
                filtered_results,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-01-19",
                        date_of_birth_precision="date",
                    ),
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=STUF_BG_DATA, max_age=30)

            self.assertEqual(
                filtered_results,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-01-19",
                    ),
                ],
            )

    def test_max_age_fails(self):
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="1986-01-19",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="1986-01-19",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results = filter_members_by_age(results=HC_DATA, max_age=30)

            self.assertEqual(filtered_results, [])

        with self.subTest("stuf_bg"):
            filtered_results = filter_members_by_age(results=STUF_BG_DATA, max_age=30)

            self.assertEqual(filtered_results, [])

    def test_min_age_depending_on_the_exact_day(self):
        # birthday not occured yet
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-26",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-26",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results1 = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(filtered_results1, [])

        with self.subTest("stuf_bg"):
            filtered_results1 = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(filtered_results1, [])

        # birthday occured
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-24",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-24",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results2 = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(
                filtered_results2,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-04-24",
                        date_of_birth_precision="date",
                    )
                ],
            )

        with self.subTest("stuf_bg"):
            filtered_results2 = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(
                filtered_results2,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-04-24",
                    )
                ],
            )

    def test_max_age_depending_on_the_exact_day(self):
        # birthday not occured yet
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-26",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2007-04-26",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results1 = filter_members_by_age(results=HC_DATA, max_age=18)

            self.assertEqual(
                filtered_results1,
                [
                    HC_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-04-26",
                        date_of_birth_precision="date",
                    )
                ],
            )

        with self.subTest("haal_centraal"):
            filtered_results2 = filter_members_by_age(results=STUF_BG_DATA, max_age=18)

            self.assertEqual(
                filtered_results2,
                [
                    StUFBG_NaturalPersonDetails(
                        bsn="123456788",
                        first_names="Doe",
                        lastname="Pirsen",
                        date_of_birth="2007-04-26",
                    )
                ],
            )

        # birthday occured
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2006-04-24",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="2006-04-24",
            ),
        ]

        with self.subTest("haal_centraal"):
            filtered_results3 = filter_members_by_age(results=HC_DATA, max_age=18)

            self.assertEqual(filtered_results3, [])

        with self.subTest("stuf_bg"):
            filtered_results4 = filter_members_by_age(results=STUF_BG_DATA, max_age=18)

            self.assertEqual(filtered_results4, [])

    def test_missing_date_of_birth_fails(self):
        HC_DATA = [
            HC_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="",
                date_of_birth_precision="date",
            )
        ]

        STUF_BG_DATA = [
            StUFBG_NaturalPersonDetails(
                bsn="123456788",
                first_names="Doe",
                lastname="Pirsen",
                date_of_birth="",
            ),
        ]

        for data in (HC_DATA, STUF_BG_DATA):
            with self.subTest():
                filtered_results = filter_members_by_age(
                    results=data, min_age=18, max_age=30
                )
                self.assertEqual(filtered_results, [])

    def test_incomplete_dates_of_birth(self):
        with self.subTest("haal_centraal"):
            # year and month
            HC_DATA = [
                HC_NaturalPersonDetails(
                    bsn="123456788",
                    first_names="Doe",
                    lastname="Pirsen",
                    date_of_birth="2002-01",
                    date_of_birth_precision="year_month",
                )
            ]

            filtered_results1 = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(filtered_results1, [])

            # year
            HC_DATA = [
                HC_NaturalPersonDetails(
                    bsn="123456788",
                    first_names="Doe",
                    lastname="Pirsen",
                    date_of_birth="2002",
                    date_of_birth_precision="year",
                )
            ]

            filtered_results2 = filter_members_by_age(results=HC_DATA, min_age=18)

            self.assertEqual(filtered_results2, [])

        with self.subTest("stuf_bg"):
            # year and month
            STUF_BG_DATA = [
                StUFBG_NaturalPersonDetails(
                    bsn="123456788",
                    first_names="Doe",
                    lastname="Pirsen",
                    date_of_birth="2002-01",
                ),
            ]

            filtered_results1 = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(filtered_results1, [])

            # year
            STUF_BG_DATA = [
                StUFBG_NaturalPersonDetails(
                    bsn="123456788",
                    first_names="Doe",
                    lastname="Pirsen",
                    date_of_birth="2002",
                ),
            ]

            filtered_results2 = filter_members_by_age(results=STUF_BG_DATA, min_age=18)

            self.assertEqual(filtered_results2, [])
