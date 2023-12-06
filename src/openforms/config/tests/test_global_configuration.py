import json
import shutil
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import clamd
from django_webtest import WebTest

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.tests.utils import NOOP_CACHES, disable_2fa

from ..models import GlobalConfiguration


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

    def test_plugin_configuration(self):
        # mocking the admin/solo machinery is not straightforward here...
        config = GlobalConfiguration.get_solo()
        config.plugin_configuration = {
            "authentication": {
                "digid": {
                    "enabled": False,
                }
            }
        }
        config.save()
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        custom_widget = change_page.pyquery(".plugin-config-react")
        self.assertEqual(len(custom_widget), 1)
        self.assertEqual(custom_widget.attr("data-name"), "plugin_configuration")
        self.assertEqual(
            custom_widget.attr("data-value"),
            '{"authentication": {"digid": {"enabled": false}}}',
        )

        # introspect registry
        json_script = custom_widget.find("#plugin_configuration-modules-and-plugins")
        modules_and_plugins = json.loads(json_script.text())
        self.assertIn("authentication", modules_and_plugins)
        self.assertIn(
            {"identifier": "digid", "label": _("DigiD")},
            modules_and_plugins["authentication"],
        )

    def test_configuration_save_form_email_can_be_added(self):
        config = GlobalConfiguration.get_solo()
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        change_page.form["save_form_email_subject_nl"] = "Subject {{form_name}}"
        change_page.form["save_form_email_content_nl"] = "Content {{form_name}}"
        change_page.form.submit()

        config.refresh_from_db()
        self.assertEqual(config.save_form_email_subject, "Subject {{form_name}}")
        self.assertEqual(config.save_form_email_content, "Content {{form_name}}")

    @override_settings(LANGUAGE_CODE="en")
    def test_virus_scan_enabled_not_configured(self):
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        change_page.form["enable_virus_scan"] = True
        response = change_page.form.submit()

        self.assertEqual(200, response.status_code)

        html_soup = response.html

        error_node = html_soup.find("p", attrs={"class": "errornote"})

        self.assertIn("Please correct the error below", error_node.text)

        list_errors = html_soup.find("ul", attrs={"class": "errorlist"})

        self.assertEqual(
            list(list_errors.children)[0].text,
            "ClamAV host and port need to be configured if virus scan is enabled.",
        )

    @override_settings(LANGUAGE_CODE="en")
    def test_virus_scan_enabled_cant_connect(self):
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        change_page.form["enable_virus_scan"] = True
        change_page.form["clamav_host"] = "clamav.bla"
        change_page.form["clamav_port"] = 3310

        with patch.object(
            clamd.ClamdNetworkSocket,
            "ping",
            side_effect=clamd.ConnectionError("Cannot connect!"),
        ):
            response = change_page.form.submit()

        self.assertEqual(200, response.status_code)

        html_soup = response.html

        error_node = html_soup.find("p", attrs={"class": "errornote"})

        self.assertIn("Please correct the error below", error_node.text)

        list_errors = html_soup.find("ul", attrs={"class": "errorlist"})

        self.assertEqual(
            list(list_errors.children)[0].text,
            "Cannot connect to ClamAV: Cannot connect!",
        )


class GlobalConfirmationEmailTests(TestCase):
    def setUp(self):
        super().setUp()

        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]
        config.save()

    def test_validate_content_syntax(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "{{{}}}"

        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            config.full_clean()

    def test_validate_content_required_tags(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "no tags here"
        with self.assertRaisesRegex(
            ValidationError,
            _("Missing required template-tag {tag}").format(
                tag="{% appointment_information %}"
            ),
        ):
            config.full_clean()

    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.confirmation_email_content = "no tags here"

        with self.subTest("valid"):
            config.confirmation_email_content = "bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"

            config.full_clean()

        with self.subTest("invalid"):
            config.confirmation_email_content = "bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"
            with self.assertRaisesMessage(
                ValidationError,
                _("This domain is not in the global netloc allowlist: {netloc}").format(
                    netloc="bad.net"
                ),
            ):
                config.full_clean()


class GlobalSaveFormEmailTests(TestCase):
    def setUp(self):
        super().setUp()
        config = GlobalConfiguration.get_solo()
        config.email_template_netloc_allowlist = ["good.net"]
        config.save()

    def test_validate_content_syntax(self):
        config = GlobalConfiguration.get_solo()
        config.save_form_email_content = "{{{}}}"

        with self.assertRaisesRegex(ValidationError, "Could not parse the remainder:"):
            config.full_clean()

    def test_validate_content_netloc_sanitation_validation(self):
        config = GlobalConfiguration.get_solo()
        config.save_form_email_content = "no tags here"

        with self.subTest("valid"):
            config.save_form_email_content = "bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"

            config.full_clean()

        with self.subTest("invalid"):
            config.save_form_email_content = "bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %} {% cosign_information %}"
            with self.assertRaisesMessage(
                ValidationError,
                _("This domain is not in the global netloc allowlist: {netloc}").format(
                    netloc="bad.net"
                ),
            ):
                config.full_clean()
