from django.test import SimpleTestCase

from openforms.payments.contrib.ogone.tests.factories import (
    OgoneMerchantFactory,
    OgoneWebhookConfigurationFactory,
)


class OgoneMerchantModelTests(SimpleTestCase):
    def test_string_represenation(self):
        merchant = OgoneMerchantFactory.build(label="Foobar")

        self.assertEqual(str(merchant), "Foobar")


class OgoneWebhookModelTests(SimpleTestCase):
    def test_string_represenation(self):
        configuration = OgoneWebhookConfigurationFactory.build(webhook_key_id="Foobar")

        self.assertEqual(str(configuration), "Foobar")
