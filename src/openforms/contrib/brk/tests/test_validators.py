from django.contrib.auth.hashers import make_password as get_salted_hash
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from privates.test import temp_private_root

from openforms.authentication.constants import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.utils.tests.vcr import OFVCRMixin

from ..validators import BRKZaakgerechtigdeValidator
from .base import TEST_FILES, BRKTestMixin


@temp_private_root()
class BRKValidatorTestCase(OFVCRMixin, BRKTestMixin, TestCase):
    VCR_TEST_FILES = TEST_FILES

    def test_brk_validator(self):

        validator = BRKZaakgerechtigdeValidator()

        submission_no_bsn = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            auth_info__plugin="demo",
            auth_info__attribute=AuthAttribute.kvk,
        )

        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("Owner")}
        ):
            validator(
                {"postcode": "not_relevant", "houseNumber": "same"}, submission_no_bsn
            )

        submission_not_hashed = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=False,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value="123456789",
            auth_info__plugin="demo",
        )

        submission_hashed = SubmissionFactory.create(
            form__generate_minimal_setup=True,
            form__authentication_backends=["demo"],
            form__formstep__form_definition__login_required=False,
            auth_info__attribute_hashed=True,
            auth_info__attribute=AuthAttribute.bsn,
            auth_info__value=get_salted_hash("123456789"),
            auth_info__plugin="demo",
        )

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
            ValidationError, _("%(type)s does not exist.") % {"type": _("Owner")}
        ):
            validator(
                {"postcode": "wrong", "houseNumber": "wrong"}, submission_not_hashed
            )

        validator({"postcode": "1234AA", "houseNumber": "123"}, submission_not_hashed)
        validator({"postcode": "1234AA", "houseNumber": "123"}, submission_hashed)

        with self.assertRaisesMessage(
            ValidationError, _("%(type)s does not exist.") % {"type": _("Owner")}
        ):
            validator(
                {"postcode": "1234AA", "houseNumber": "123"}, submission_wrong_bsn
            )
