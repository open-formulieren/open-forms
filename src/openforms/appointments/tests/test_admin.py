from django.contrib.auth.models import Permission
from django.urls import reverse

from django_webtest import WebTest
from freezegun import freeze_time

from openforms.accounts.tests.factories import (
    StaffUserFactory,
    SuperUserFactory,
    UserFactory,
)

from .factories import AppointmentInfoFactory


class AppointmentInfoAdminTests(WebTest):
    @freeze_time("2021-11-26T17:00:00+01:00")
    def test_cancel_and_change_links_only_for_superuser(self):
        normal, staff = non_superusers = [
            UserFactory.create(),
            StaffUserFactory.create(),
        ]
        permission = Permission.objects.get(
            content_type__app_label="appointments", codename="view_appointmentinfo"
        )
        # set up changelist permissions
        for user in non_superusers:
            user.user_permissions.add(permission)

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
