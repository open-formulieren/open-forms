from django.test import SimpleTestCase

from ..models import OgoneMerchant
from .factories import OgoneWebhookConfigurationFactory


class OgoneMerchantTests(SimpleTestCase):
    def test_model_str_for_unsaved_instance(self):
        instance = OgoneMerchant()

        result = str(instance)

        self.assertIsInstance(result, str)


class OgoneWebhookModelTests(SimpleTestCase):
    def test_string_represenation(self):
        configuration = OgoneWebhookConfigurationFactory.build(webhook_key_id="Foobar")

        self.assertEqual(str(configuration), "Foobar")
