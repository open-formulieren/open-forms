from django.urls import reverse

from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory

from .factories import RichTextColorFactory


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
