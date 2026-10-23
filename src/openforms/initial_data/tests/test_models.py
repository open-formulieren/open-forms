from datetime import UTC, datetime

from django.db import IntegrityError
from django.test import override_settings

import time_machine
from hypothesis import assume, given, strategies as st
from hypothesis.extra.django import TestCase

from openforms.authentication.tests.strategies import branch_numbers, kvk_numbers
from openforms.forms.tests.factories import FormFactory

from ..constants import SupportedAuthAttributes
from .factories import InitialSubmissionDataFactory


class InitialSubmissionDataModelTests(TestCase):
    @override_settings(LANGUAGE_CODE="en")
    def test_string_representation(self):
        form = FormFactory.build(internal_name="my form")
        initial_data = InitialSubmissionDataFactory.build(
            form=form,
            representee_auth_attribute=SupportedAuthAttributes.kvk,
        )

        representation = str(initial_data)

        self.assertEqual(representation, "KvK number for my form")

    @time_machine.travel("2026-01-01T00:00:00+00:00", tick=False)
    def test_expiry_date_calculation(self):
        initial_data = InitialSubmissionDataFactory.create(ttl=3)

        self.assertEqual(
            initial_data.expiry_date, datetime(2026, 1, 1, 3, 0, 0, tzinfo=UTC)
        )

    @given(auth_attribute=..., branch_number=branch_numbers)
    def test_cannot_store_branch_number_for_non_kvk_auth_attribute(
        self,
        auth_attribute: SupportedAuthAttributes,
        branch_number: str,
    ):
        assume(auth_attribute != SupportedAuthAttributes.kvk)

        with self.assertRaises(IntegrityError):
            InitialSubmissionDataFactory.create(
                representee_auth_attribute=auth_attribute,
                representee_branch_number=branch_number,
            )

    @given(
        branch_number=st.one_of(branch_numbers, st.just("")),
        kvk_number=kvk_numbers,
    )
    def test_can_store_branch_number_for_kvk_auth_attribute(
        self, branch_number: str, kvk_number: str
    ):
        initial_data = InitialSubmissionDataFactory.create(
            representee_auth_attribute=SupportedAuthAttributes.kvk,
            representee_auth_value=kvk_number,
            representee_branch_number=branch_number,
        )

        self.assertIsNotNone(initial_data.pk)
