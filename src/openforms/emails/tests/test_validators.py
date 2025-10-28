from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.validators import URLSanitationValidator


class URLSanitationValidatorTest(TestCase):
    def test_validator(self):
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]  # pyright: ignore[reportAttributeAccessIssue]
        config.save()

        validator = URLSanitationValidator()

        with self.subTest("valid basic"):
            validator("http://good.net")

        with self.subTest("valid mixed"):
            validator("bla bla http://good.net bla http://good.net/xyz?123 bla bla ")

        with self.subTest(
            "valid with BASE_URL via global get_system_netloc_allowlist()"
        ):
            validator(
                f"bla bla {settings.BASE_URL} bla http://good.net/xyz?123 bla bla "
            )

        message = _("This domain is not in the global netloc allowlist: {netloc}")

        with self.subTest("invalid basic"):
            with self.assertRaisesMessage(
                ValidationError, message.format(netloc="bad.net")
            ):
                validator("http://bad.net")

        with self.subTest("invalid mixed"):
            with self.assertRaisesMessage(
                ValidationError, message.format(netloc="bad.net")
            ):
                validator("http://good.net http://bad.net")

        with self.subTest("invalid extra"):
            with self.assertRaisesMessage(
                ValidationError, message.format(netloc="bad.net")
            ):
                validator("bla bla http://bad.net/xyz?123 bla bla ")

        with self.subTest("Valid with http://www."):
            validator("http://www.good.net")
