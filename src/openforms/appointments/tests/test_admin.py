from contextlib import contextmanager
from unittest.mock import patch

from django.test import tag
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time
from maykin_2fa.test import disable_admin_mfa

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)
from openforms.plugins.validators import PluginExistsValidator
from openforms.utils.tests.cache import clear_caches

from ..contrib.demo.plugin import DemoAppointment
from ..fields import AppointmentBackendChoiceField
from ..models import AppointmentsConfig
from ..registry import Registry
from .factories import AppointmentFactory, AppointmentInfoFactory


@contextmanager
def patch_registry(register):
    field = AppointmentsConfig._meta.get_field("plugin")
    assert isinstance(field, AppointmentBackendChoiceField)
    validators = [
        validator
        for validator in field.validators
        if isinstance(validator, PluginExistsValidator)
    ]
    assert len(validators) == 1, "Expected only one PluginValidator"
    validator = validators[0]
    with (
        patch("openforms.appointments.admin.register", register),
        patch("openforms.appointments.utils.register", register),
        patch.object(field, "registry", register),
        patch.object(validator, "registry", register),
    ):
        yield


class TestPlugin(DemoAppointment):
    verbose_name = _("Test plugin")
    is_demo_plugin = False


@disable_admin_mfa()
class AppointmentInfoAdminTests(WebTest):
    @freeze_time("2021-11-26T17:00:00+01:00")
    def test_cancel_link_only_for_superuser(self):
        normal, staff = [
            UserFactory.create(user_permissions=["view_appointmentinfo"]),
            StaffUserFactory.create(user_permissions=["view_appointmentinfo"]),
        ]

        # appointment in the future
        AppointmentInfoFactory.create(
            registration_ok=True, start_time="2021-11-30T17:00:00+01:00"
        )

        # test content on page
        with self.subTest(user="non-staff"):
            changelist = self.app.get(
                reverse("admin:appointments_appointmentinfo_changelist"),
                user=normal,
            )

            self.assertEqual(changelist.status_code, 302)

        with self.subTest(user="staff, no superuser"):
            changelist = self.app.get(
                reverse("admin:appointments_appointmentinfo_changelist"),
                user=staff,
            )

            self.assertEqual(changelist.status_code, 200)

            object_actions_col = changelist.pyquery(".field-get_object_actions")
            self.assertFalse(object_actions_col)

    @freeze_time("2021-11-26T17:00:00+01:00")
    def test_cancel_link(self):

        user = SuperUserFactory.create()
        # appointment in the past
        AppointmentFactory.create(
            appointment_info__registration_ok=True,
            appointment_info__start_time="2021-11-01T17:00:00+01:00",
        )
        # appointment in the future
        AppointmentFactory.create(
            appointment_info__registration_ok=True,
            appointment_info__start_time="2021-11-30T17:00:00+01:00",
        )

        changelist = self.app.get(
            reverse("admin:appointments_appointmentinfo_changelist"), user=user
        )

        self.assertEqual(changelist.status_code, 200)
        object_actions_col = changelist.pyquery(".field-get_object_actions")

        # future appointment
        app1_links = object_actions_col.eq(0).find("a")
        self.assertEqual(len(app1_links), 1)

        # past appointment
        app2_links = object_actions_col.eq(1).find("a")
        self.assertEqual(len(app2_links), 0)


@disable_admin_mfa()
class AppointmentsConfigAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

    def setUp(self):
        super().setUp()
        self.addCleanup(clear_caches)

    def test_plugin_choices(self):
        """
        show available plugins from registry as field choices
        """
        test_register = Registry()
        test_register("test1")(TestPlugin)
        test_register("test2")(TestPlugin)

        url = reverse(
            "admin:appointments_appointmentsconfig_change",
            args=(AppointmentsConfig.singleton_instance_id,),
        )

        with patch_registry(test_register):
            response = self.app.get(url, user=self.user)

        self.assertEqual(response.status_code, 200)

        form = response.forms["appointmentsconfig_form"]
        plugin_options = form["plugin"].options

        self.assertEqual([p[0] for p in plugin_options], ["", "test1", "test2"])

    @tag("gh-2471")
    def test_configure_default_location(self):
        test_register = Registry()
        test_register("test")(TestPlugin)

        url = reverse(
            "admin:appointments_appointmentsconfig_change",
            args=(AppointmentsConfig.singleton_instance_id,),
        )

        with patch_registry(test_register):
            with self.subTest("no plugin selected -> block setting a location"):
                response = self.app.get(url, user=self.user)

                self.assertEqual(response.status_code, 200)
                form = response.forms["appointmentsconfig_form"]

                self.assertEqual(form["plugin"].value, "")
                location = form["limit_to_location"]
                self.assertEqual(location.tag, "input")
                self.assertIn("disabled", location.attrs)
                self.assertEqual(
                    location.attrs["placeholder"],
                    _("Please configure the plugin first"),
                )

            config = AppointmentsConfig.get_solo()
            config.plugin = "test"
            config.save()

            with self.subTest("plugin selected -> show available locations"):
                response = self.app.get(url, user=self.user)

                self.assertEqual(response.status_code, 200)
                form = response.forms["appointmentsconfig_form"]

                self.assertEqual(form["plugin"].value, "test")
                location = form["limit_to_location"]
                self.assertEqual(location.tag, "select")
                form["limit_to_location"].select("1")
                form.submit(name="_save")

                config.refresh_from_db()
                self.assertEqual(config.limit_to_location, "1")

            with self.subTest("clearing plugin clears the location"):
                config.limit_to_location = "1"
                config.save()

                response = self.app.get(url, user=self.user)

                form = response.forms["appointmentsconfig_form"]
                form["plugin"].select("")

                form.submit(name="_save")

                config.refresh_from_db()
                self.assertEqual(config.plugin, "")
                self.assertEqual(config.limit_to_location, "")
