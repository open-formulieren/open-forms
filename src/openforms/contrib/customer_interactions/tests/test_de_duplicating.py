from collections.abc import Sequence

from unittest_parametrize import ParametrizedTestCase, parametrize

from ..transform import prepare_addresses_for_frontend
from ..typing import CommunicationChannel


class DeDuplicatingAddressesTests(ParametrizedTestCase):
    @parametrize(
        "first_verified,duplicate_verified,expected_options",
        [
            (
                False,
                False,
                [
                    ("foo1@example.com", False),
                    ("foo2@example.com", True),
                ],
            ),
            (
                False,
                True,
                [
                    ("foo1@example.com", True),
                    ("foo2@example.com", True),
                ],
            ),
            (
                True,
                False,
                [
                    ("foo1@example.com", True),
                    ("foo2@example.com", True),
                ],
            ),
            (
                True,
                True,
                [
                    ("foo1@example.com", True),
                    ("foo2@example.com", True),
                ],
            ),
        ],
    )
    def test_filter_duplicate_addresses(
        self,
        first_verified,
        duplicate_verified,
        expected_options,
    ):
        addresses: Sequence[CommunicationChannel] = [
            {
                "type": "email",
                "options": [
                    {
                        "address": "foo1@example.com",
                        "verification_date": "2024-01-01" if first_verified else None,
                    },
                    {"address": "foo2@example.com", "verification_date": "2024-02-01"},
                    {
                        "address": "foo1@example.com",
                        "verification_date": "2024-02-02"
                        if duplicate_verified
                        else None,
                    },
                ],
                "preferred": "foo1@example.com",
            },
        ]

        result = prepare_addresses_for_frontend(addresses)

        self.assertEqual(
            [
                (option["address"], option["is_verified"])
                for option in result[0]["options"]
            ],
            expected_options,
        )
