from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import ConfirmationEmailTemplate


class ConfirmationEmailTests(TestCase):
    def test_validate_content_can_be_parsed(self):
        email = ConfirmationEmailTemplate(content="{{{}}}")

        with self.assertRaises(ValidationError):
            email.clean()
