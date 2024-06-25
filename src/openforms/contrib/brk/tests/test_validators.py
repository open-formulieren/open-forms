from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

import requests_mock
from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.contrib.brk.models import BRKConfig
from openforms.pre_requests.base import PreRequestHookBase
from openforms.pre_requests.registry import Registry
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..validators import BRKZakelijkGerechtigdeValidator
from .base import TEST_FILES, BRKTestMixin


@temp_private_root()
class BRKValidatorTestCase(BRKTestMixin, OFVCRMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_brk_validator_no_auth(self):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_no_auth = SubmissionFactory.create(
            form__generate_minimal_setup=True,
        )

        with self.assertRaisesMessage(
            ValidationError, _("No BSN is available to validate your address.")
        ):
            validator(
                {"postcode": "not_relevant", "houseNumber": "same"}, submission_no_auth
            )

    def test_brk_validator_no_bsn(self):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_no_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            auth_info__plugin="demo",
            auth_info__attribute=AuthAttribute.kvk,
        )

        with self.assertRaisesMessage(
            ValidationError, _("No BSN is available to validate your address.")
        ):
            validator(
                {"postcode": "not_relevant", "houseNumber": "same"}, submission_no_bsn
            )

    def test_brk_validator_wrong_bsn(self):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_wrong_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="wrong_bsn",
            auth_info__plugin="demo",
        )

        with self.assertRaisesMessage(
            ValidationError,
            _("According to our records, you are not a legal owner of this property."),
        ):
            validator({"postcode": "7361EW", "houseNumber": "21"}, submission_wrong_bsn)

    def test_brk_validator_bsn(self):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="71291440",
            auth_info__plugin="demo",
        )

        with self.assertRaisesMessage(
            ValidationError, _("No property found for this address.")
        ):
            validator({"postcode": "1234AA", "houseNumber": "1"}, submission_bsn)

        with self.assertRaisesMessage(
            ValidationError, _("No property found for this address.")
        ):
            validator(
                {
                    "postcode": "7361EW",
                    "houseNumber": "21",
                    "houseLetter": "A",
                    "houseNumberAddition": "B",
                },
                submission_bsn,
            )

        try:
            validator({"postcode": "7361EW", "houseNumber": "21"}, submission_bsn)
        except ValidationError as exc:
            raise self.failureException(
                "Input data unexpectedly did not validate"
            ) from exc

    @requests_mock.Mocker()
    def test_brk_validator_requests_error(self, m: requests_mock.Mocker):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="71291440",
            auth_info__plugin="demo",
        )

        m.get(
            "https://api.brk.kadaster.nl/esd-eto-apikey/bevragen/v2/kadastraalonroerendezaken?postcode=1234AA&huisnummer=1",
            status_code=400,
        )

        with self.assertRaisesMessage(
            ValidationError,
            _(
                "There was an error while retrieving the available properties. Please try again later."
            ),
        ):
            validator({"postcode": "1234AA", "houseNumber": "1"}, submission_bsn)

    def test_pre_request_hooks_called(self):
        pre_req_register = Registry()
        mock = MagicMock()

        @pre_req_register("test")
        class PreRequestHook(PreRequestHookBase):
            def __call__(self, *args, **kwargs):
                mock(*args, **kwargs)

        validator = BRKZakelijkGerechtigdeValidator("brk_validator")
        submission_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="71291440",
            auth_info__plugin="demo",
        )

        with patch("openforms.pre_requests.clients.registry", new=pre_req_register):
            validator({"postcode": "7361EW", "houseNumber": "21"}, submission_bsn)

        self.assertEqual(mock.call_count, 2)  # 2 API calls expected
        context = mock.call_args.kwargs["context"]
        self.assertIsNotNone(context)  # type: ignore


class BRKValidatorNotConfiguredTestCase(TestCase):
    def setUp(self):
        super().setUp()

        patcher = patch(
            "openforms.contrib.brk.client.BRKConfig.get_solo",
            return_value=BRKConfig(),
        )
        self.config_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_brk_validator_not_configured(self):
        validator = BRKZakelijkGerechtigdeValidator("brk_validator")

        submission_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="71291440",
            auth_info__plugin="demo",
        )

        with self.assertRaisesMessage(
            ValidationError,
            _(
                "There was an error while retrieving the available properties. Please try again later."
            ),
        ):
            validator({"postcode": "1234AA", "houseNumber": "1"}, submission_bsn)
