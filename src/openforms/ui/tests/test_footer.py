from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest

from openforms.accounts.tests.factories import UserFactory
from openforms.config.models import GlobalConfiguration


class FooterTest(WebTest):
    @patch("openforms.config.models.GlobalConfiguration.get_solo")
    def test_privacy_policy_link_in_footer(self, m_get_solo):
        m_get_solo.return_value = GlobalConfiguration(
            privacy_policy_url="http://example-policy.com"
        )
        user = UserFactory.create(is_staff=True)

        response = self.app.get(reverse("forms:form-list"), user=user)

        self.assertEqual(200, response.status_code)

        footer_node = response.html.find("footer")
        link_node = footer_node.find("a", text=_("Privacy policy"))

        self.assertIsNotNone(link_node)
        self.assertEqual(link_node.attrs["href"], "http://example-policy.com")
