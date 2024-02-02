from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory

from .factories import ThemeFactory


@disable_admin_mfa()
class ThemePreviewTests(WebTest):
    def test_can_preview_theme_via_admin_list(self):
        user = SuperUserFactory.create()
        theme = ThemeFactory.create()
        form = FormFactory.create(generate_minimal_setup=True)
        assert form.theme != theme

        changelist = self.app.get(reverse("admin:config_theme_changelist"), user=user)
        form_page = changelist.click(_("Show preview"))
        form_page.form["form"].select(str(form.id))

        response = form_page.form.submit()
        self.assertRedirects(
            response,
            reverse(
                "forms:theme-preview", kwargs={"theme_pk": theme.pk, "slug": form.slug}
            ),
        )
