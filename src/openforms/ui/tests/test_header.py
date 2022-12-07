from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory


class HeaderTest(WebTest):
    @patch("openforms.config.models.GlobalConfiguration.get_solo")
    def test_logo_label(self, get_solo_mock):
        get_solo_mock.return_value = GlobalConfiguration(
            organization_name="My organization"
        )
        form = FormFactory.create()
        url = reverse("forms:form-detail", kwargs={"slug": form.slug})

        response = self.app.get(url)

        self.assertEqual(200, response.status_code)

        header_node = response.html.find("header")
        link_node = header_node.find("a")
        aria_label = link_node.get("aria-label")
        title = link_node.get("title")

        expected_label = _("Back to website of %(name)s") % {"name": "My organization"}
        self.assertEqual(aria_label, expected_label)
        self.assertEqual(title, expected_label)
