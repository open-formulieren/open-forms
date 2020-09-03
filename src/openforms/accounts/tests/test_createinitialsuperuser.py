from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import exceptions, reverse

from ..models import User


class CreateInitialSuperuserTests(TestCase):
    def test_create_initial_superuser_command(self):
        call_command("createinitialsuperuser", "maykin", "support@maykinmedia.nl")
        user = User.objects.get()

        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        try:
            link = f'{settings.ALLOWED_HOSTS[0]}{reverse("admin:index")}'
        except exceptions.NoReverseMatch:
            link = settings.ALLOWED_HOSTS[0]
        self.assertEqual(
            sent_mail.subject, f"Credentials for {settings.PROJECT_NAME} ({link})"
        )
        self.assertListEqual(sent_mail.recipients(), ["support@maykinmedia.nl"])

    @override_settings(ALLOWED_HOSTS=[])
    def test_create_initial_superuser_command_allowed_hosts_empty(self):
        call_command("createinitialsuperuser", "maykin", "support@maykinmedia.nl")
        user = User.objects.get()

        self.assertTrue(user.has_usable_password())
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        self.assertEqual(len(mail.outbox), 1)

        sent_mail = mail.outbox[0]
        link = "unknown url"
        self.assertEqual(
            sent_mail.subject, f"Credentials for {settings.PROJECT_NAME} ({link})"
        )
        self.assertListEqual(sent_mail.recipients(), ["support@maykinmedia.nl"])
