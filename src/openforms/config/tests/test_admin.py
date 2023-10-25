from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.urls import reverse

from openforms.config.models import CSPSetting
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory

from ..admin import CSPSettingAdmin


class TestCSPAdmin(TestCase):
    def test_content_type_link(self):
        OgoneMerchantFactory()

        csp = CSPSetting.objects.get()

        admin_site = AdminSite()
        admin = CSPSettingAdmin(CSPSetting, admin_site)

        expected_url = reverse(
            "admin:payments_ogone_ogonemerchant_change",
            kwargs={"object_id": str(csp.object_id)},
        )
        expected_link = f'<a href="{expected_url}">{str(csp.content_object)}</a>'

        link = admin.content_type_link(csp)

        self.assertEqual(link, expected_link)
