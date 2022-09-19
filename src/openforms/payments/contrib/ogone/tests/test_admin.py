from django.urls import reverse

from django_webtest import WebTest
from furl import furl

from openforms.accounts.tests.factories import SuperUserFactory


class OgoneMerchantAdminTest(WebTest):
    def test_add_ogone_merchant(self):
        user = SuperUserFactory.create()
        url = reverse("admin:payments_ogone_ogonemerchant_add")

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)

        feedback_url = (
            response.html.findAll("div", class_="field-feedback_url")[0]
            .findAll("div", class_="readonly")[0]
            .text
        )

        parsed_url = furl(feedback_url)

        self.assertEqual(parsed_url.host, "testserver")
