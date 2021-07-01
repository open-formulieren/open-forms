from django.test import TestCase
from django.urls import reverse

from openforms.config.models import GlobalConfiguration


class PrivacyPolicyViewTests(TestCase):
    def test_render_template(self):
        config = GlobalConfiguration.get_solo()
        config.privacy_policy_content = "<div>This is a security policy</div>"
        config.save()

        response = self.client.get(reverse("privacy-policy:privacy-policy"))

        self.assertEqual(200, response.status_code)
        self.assertIn(
            "<div>This is a security policy</div>", response.content.decode("utf-8")
        )
