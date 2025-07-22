from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory


@disable_admin_mfa()
class WorldlineMerchantAdminTest(WebTest):
    @override_settings(BASE_URL="https://example.com/foo")
    def test_merchant_detail_page(self):
        user = SuperUserFactory.create()
        url = reverse("admin:payments_worldline_worldlinemerchant_add")

        response = self.app.get(url, user=user)

        self.assertEqual(200, response.status_code)
