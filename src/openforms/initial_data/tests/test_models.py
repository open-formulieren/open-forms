from datetime import UTC, datetime

from django.test import TestCase, override_settings

import time_machine

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
