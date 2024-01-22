from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy as _

from openforms.forms.models import Form

from ..models import BRPPersonenRequestOptions
from ..validators import validate_verwerking_header


class BRPPersonenRequestOptionsTestCase(SimpleTestCase):
    def test_brp_personen_request_options_str(self):
        options = BRPPersonenRequestOptions(form=Form())
        self.assertEqual(
            str(options),
            _("BRP Request options for form {form_pk}").format(form_pk=None),
        )

    def test_validate_verwerking_header(self):
        with self.assertRaises(ValidationError) as cm:
            validate_verwerking_header("aa@@a")

        self.assertEqual(cm.exception.code, "no_multiple_at_characters")
