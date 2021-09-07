import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from django_webtest import WebTest
from webtest import Upload

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import FormFactory
from openforms.tests.utils import NOOP_CACHES, disable_2fa

from ..models import GlobalConfiguration

LOGO_FILE = Path(settings.BASE_DIR) / "docs" / "logo.svg"


@disable_2fa
@override_settings(
    CACHES=NOOP_CACHES,
    MEDIA_ROOT=tempfile.mkdtemp(),
    SESSION_ENGINE="django.contrib.sessions.backends.db",
)
class AdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()

        self.app.set_user(self.user)

        def _cleanup():
            try:
                shutil.rmtree(settings.MEDIA_ROOT)
            except Exception:
                pass

        self.addCleanup(_cleanup)

    def test_upload_svg(self):
        with self.subTest(part="admin config"):
            url = reverse("admin:config_globalconfiguration_change", args=(1,))

            change_page = self.app.get(url)

            with open(LOGO_FILE, "rb") as infile:
                upload = Upload("logo.svg", infile.read(), "image/svg+xml")

            change_page.form["logo"] = upload
            response = change_page.form.submit()

            self.assertEqual(response.status_code, 302)
            config = GlobalConfiguration.get_solo()
            self.assertEqual(config.logo, "logo/logo.svg")

        with self.subTest(part="logo used"):
            form = FormFactory.create()
            url = reverse("forms:form-detail", kwargs={"slug": form.slug})

            form_page = self.app.get(url)

            header = form_page.pyquery(".page-header")
            self.assertTrue(header)
            self.assertIn("page-header--has-logo", header.attr("class"))
            style = header.find("a").attr("style")
            self.assertEqual(style, f"--of-logo-header-url: url('{config.logo.url}')")

    def test_upload_png(self):
        logo = Path(settings.DJANGO_PROJECT_DIR) / "static" / "img" / "digid.png"
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        with open(logo, "rb") as infile:
            upload = Upload("digid.png", infile.read(), "image/png")

        change_page.form["logo"] = upload
        response = change_page.form.submit()

        self.assertEqual(response.status_code, 302)
        config = GlobalConfiguration.get_solo()
        self.assertEqual(config.logo, "logo/digid.png")

    def test_upload_blank(self):
        # fixes #581
        config = GlobalConfiguration.get_solo()
        config.logo = None
        config.save()

        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        response = change_page.form.submit()

        self.assertEqual(response.status_code, 302)
        config = GlobalConfiguration.get_solo()
        self.assertEqual(config.logo, "")
