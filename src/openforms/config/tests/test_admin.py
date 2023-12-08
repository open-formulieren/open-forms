from django.contrib.admin.sites import AdminSite
from django.test import TestCase
from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.config.models import CSPSetting
from openforms.payments.contrib.ogone.tests.factories import OgoneMerchantFactory

from ..admin import CSPSettingAdmin
from .factories import RichTextColorFactory


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


class ColorAdminTests(WebTest):
    def test_color_changelist(self):
        RichTextColorFactory.create_batch(9)
        url = reverse("admin:config_richtextcolor_changelist")
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)

    def test_color_detail(self):
        color = RichTextColorFactory.create()
        url = reverse("admin:config_richtextcolor_change", args=(color.pk,))
        user = SuperUserFactory.create()

        response = self.app.get(url, user=user)

        self.assertEqual(response.status_code, 200)
