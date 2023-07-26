from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext as _

from soap.tests.factories import SoapServiceFactory

from ..models import JccConfig


class ConfigTest(TestCase):
    def test_config_raises_validation_error_when_soap_url_missing(self):
        service = SoapServiceFactory.create(url="")
        instance = JccConfig.get_solo()

        with self.assertRaisesMessage(
            ValidationError, _("Url for Soap Service is not provided.")
        ):
            instance.service = service
            instance.clean_fields()
