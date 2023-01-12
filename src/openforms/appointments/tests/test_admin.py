from unittest.mock import patch

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from freezegun import freeze_time

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)

from ..contrib.demo.plugin import DemoAppointment
from ..models import AppointmentsConfig
from ..registry import Registry
from .factories import AppointmentInfoFactory


class TestPlugin(DemoAppointment):
    verbose_name = _("Test plugin")
    is_demo_plugin = False


class AppointmentInfoAdminTests(WebTest):
    @freeze_time("2021-11-26T17:00:00+01:00")
    def test_cancel_and_change_links_only_for_superuser(self):
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
    def test_cancel_and_change_links(self):
        user = SuperUserFactory.create()
        # appointment in the past
        AppointmentInfoFactory.create(
            registration_ok=True, start_time="2021-11-01T17:00:00+01:00"
        )
        # appointment in the future
        AppointmentInfoFactory.create(
            registration_ok=True, start_time="2021-11-30T17:00:00+01:00"
        )

        changelist = self.app.get(
            reverse("admin:appointments_appointmentinfo_changelist"), user=user
        )

        self.assertEqual(changelist.status_code, 200)
        object_actions_col = changelist.pyquery(".field-get_object_actions")

        # future appointment
        app1_links = object_actions_col.eq(0).find("a")
        self.assertEqual(len(app1_links), 2)

        # past appointment
        app2_links = object_actions_col.eq(1).find("a")
        self.assertEqual(len(app2_links), 0)


class AppointmentsConfigAdminTests(WebTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = SuperUserFactory.create()

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

        with patch("openforms.appointments.admin.register", test_register):
            response = self.app.get(url, user=self.user)

        self.assertEqual(response.status_code, 200)

        form = response.form
        plugin_options = form["plugin"].options

        self.assertEqual([p[0] for p in plugin_options], ["", "test1", "test2"])
