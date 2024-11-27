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
from maykin_2fa.test import disable_admin_mfa
from webtest import Form as WebTestForm

from openforms.accounts.tests.factories import SuperUserFactory
from openforms.tests.utils import NOOP_CACHES

from ..models import GlobalConfiguration


def _ensure_arrayfields(form: WebTestForm, config: GlobalConfiguration | None = None):
    if config is None:
        config = GlobalConfiguration.get_solo()  # type: ignore
    # set the values manually, normally this is done through JS (django-jsonform takes
    # care of it)
    form["email_template_netloc_allowlist"] = json.dumps(
        config.email_template_netloc_allowlist
    )
    form["recipients_email_digest"] = json.dumps(config.recipients_email_digest)


@disable_admin_mfa()
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

        form = change_page.forms["globalconfiguration_form"]
        form["save_form_email_subject_nl"] = "Subject {{form_name}}"
        form["save_form_email_content_nl"] = "Content {{form_name}}"
        _ensure_arrayfields(form, config=config)
        form.submit()

        config.refresh_from_db()
        self.assertEqual(config.save_form_email_subject, "Subject {{form_name}}")
        self.assertEqual(config.save_form_email_content, "Content {{form_name}}")

    @override_settings(LANGUAGE_CODE="en")
    def test_virus_scan_enabled_not_configured(self):
        url = reverse("admin:config_globalconfiguration_change", args=(1,))

        change_page = self.app.get(url)

        form = change_page.forms["globalconfiguration_form"]
        form["enable_virus_scan"] = True
        _ensure_arrayfields(form)
        response = form.submit()

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

        form = change_page.forms["globalconfiguration_form"]
        form["enable_virus_scan"] = True
        form["clamav_host"] = "clamav.bla"
        form["clamav_port"] = 3310

        with patch.object(
            clamd.ClamdNetworkSocket,
            "ping",
            side_effect=clamd.ConnectionError("Cannot connect!"),
        ):
            _ensure_arrayfields(form)
            response = form.submit()

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
        self.addCleanup(GlobalConfiguration.clear_cache)

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
            config.confirmation_email_content = "bla bla http://good.net/bla?x=1 {% appointment_information %} {% payment_information %}"

            config.full_clean()

        with self.subTest("invalid"):
            config.confirmation_email_content = "bla bla http://bad.net/bla?x=1 {% appointment_information %} {% payment_information %}"
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
        self.addCleanup(GlobalConfiguration.clear_cache)

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
