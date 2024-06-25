from unittest.mock import patch

from django.utils.translation import gettext_lazy as _

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin
from openforms.utils.tests.vcr import OFVCRMixin
from openforms.validations.registry import Registry

from ..validators import BRKZakelijkGerechtigdeValidator
from .base import TEST_FILES, BRKTestMixin


class BRKValidatorIntegrationTestCase(
    SubmissionsMixin, BRKTestMixin, OFVCRMixin, APITestCase
):
    VCR_TEST_FILES = TEST_FILES

    def setUp(self) -> None:
        super().setUp()
        register = Registry()
        register("brk-zakelijk-gerechtigd")(BRKZakelijkGerechtigdeValidator)

        patcher = patch("openforms.validations.api.views.register", new=register)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_brk_validator_integration(self) -> None:
        submission = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="12345678",
            auth_info__plugin="demo",
        )
        self._add_submission_to_session(submission)

        response = self.client.post(
            reverse(
                "api:validate-value", kwargs={"validator": "brk-zakelijk-gerechtigd"}
            ),
            {
                "value": {
                    "postcode": "1234 aB",
                    "houseNumber": "1",
                    "houseLetter": "A",
                    "houseNumberAddition": "Add",
                },
                "submission_uuid": str(submission.uuid),
            },
            format="json",
        )

        expected = {
            "is_valid": False,
            "messages": [_("No property found for this address.")],
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, expected)
