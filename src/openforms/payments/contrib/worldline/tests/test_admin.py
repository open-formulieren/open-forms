from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from furl import furl
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.payments.contrib.worldline.constants import WorldlineEndpoints


@disable_admin_mfa()
class WorldlineMerchantAdminTest(WebTest):
    @override_settings(BASE_URL="https://example.com/foo")
    def test_merchant_detail_page(self):
        user = SuperUserFactory.create()
        url = reverse("admin:payments_worldline_worldlinemerchant_add")

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)

        endpoint_url = (
            response.html.findAll("div", class_="field-endpoint")[0]
            .findAll("div", class_="readonly")[0]
            .text
        )

        parsed_url = furl(endpoint_url)

        self.assertEqual(str(parsed_url), WorldlineEndpoints.test)
