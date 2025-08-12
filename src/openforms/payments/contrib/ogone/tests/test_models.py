from django.test import SimpleTestCase

from openforms.payments.contrib.ogone.tests.factories import (
    OgoneWebhookConfigurationFactory,
)


class OgoneWebhookModelTests(SimpleTestCase):
    def test_string_represenation(self):
        configuration = OgoneWebhookConfigurationFactory.build(webhook_key_id="Foobar")

        self.assertEqual(str(configuration), "Foobar")
