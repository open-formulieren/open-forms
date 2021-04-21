from django.contrib.auth import get_user_model
from django.urls import reverse

from django_webtest import WebTest

from openforms.forms.tests.factories import FormFactory


class ZGWFormConfigAdminTests(WebTest):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john",
            password="secret",
            email="john@example.com",
            is_superuser=True,
            is_staff=True,
        )

    def test_form_zgw_config_inline(self):
        form = FormFactory.create(
            backend="openforms.contrib.zgw.backends.create_zaak_backend"
        )
        response = self.app.get(
            reverse("admin:forms_form_change", args=(form.pk,)), user=self.user
        )

        # Inline formset for ZGWFormConfig should be visible
        self.assertIsNotNone(response.html.find("div", {"id": "zgwformconfig-group"}))
