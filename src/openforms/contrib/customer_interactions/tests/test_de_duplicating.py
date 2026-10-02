from collections.abc import Sequence

from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.forms.tests.factories import FormVariableFactory
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.variables.constants import FormVariableDataTypes

from ..transform import prepare_addresses_for_frontend
from ..typing import CommunicationChannel


class DeDuplicatingAddressesTests(ParametrizedTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.submission = SubmissionFactory.from_components(
            [
                {
                    "key": "profile",
                    "type": "customerProfile",
                    "label": "Profile",
                    "digitalAddressTypes": ["email", "phoneNumber"],
                    "shouldUpdateCustomerData": True,
                }
            ],
            submitted_data={
                "profile": {},
            },
        )
        self.form_variable = FormVariableFactory.create(
            key="communication-preferences",
            form=self.submission.form,
            user_defined=True,
            data_type=FormVariableDataTypes.array,
            prefill_plugin="communication_preferences",
            prefill_options={
                "customer_interactions_api_group": "some-identifier",
                "profile_form_variable": "profile",
            },
        )

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
                        "reference": "",
                    },
                    {
                        "address": "foo2@example.com",
                        "verification_date": "2024-02-01",
                        "reference": "",
                    },
                    {
                        "address": "foo1@example.com",
                        "verification_date": "2024-02-02"
                        if duplicate_verified
                        else None,
                        "reference": "",
                    },
                ],
                "preferred": "foo1@example.com",
            },
        ]

        result = prepare_addresses_for_frontend(
            addresses, self.submission, self.form_variable.key
        )

        self.assertEqual(
            [
                (option["address"], option["is_verified"])
                for option in result[0]["options"]
            ],
            expected_options,
        )

    def test_filter_duplicate_addresses_with_no_list_value(self):
        self.assertEqual(
            prepare_addresses_for_frontend(
                "None",  # pyright: ignore[reportArgumentType]
                self.submission,
                self.form_variable.key,
            ),
            [],
        )
