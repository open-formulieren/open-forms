# Taken from github.com/open-zaak/open-zaak project
# Copyright (C) 2020 Dimpact
import os

import django
from django.conf import settings
from django.contrib.auth.management.commands.createsuperuser import (
    Command as BaseCommand,
)
from django.core.mail import send_mail
from django.urls import reverse

from ...models import User

PASSWORD_FROM_ENV_SUPPORTED = django.VERSION[:2] > (2, 2)


class Command(BaseCommand):
    help = "Set up an initial superuser account if it doesn't exist yet"

    UserModel: type[User]

    def add_arguments(self, parser):
        super().add_arguments(parser)

        parser.add_argument(
            "--password",
            help="Set the password when the superuser is initially created.",
        )
        parser.add_argument(
            "--generate-password",
            action="store_true",
            help=(
                "Generate and e-mail the password. The --password option and "
                "environment variable overrule this flag."
            ),
        )
        parser.add_argument(
            "--email-password-reset",
            action="store_true",
            help="Send a password reset e-mail after user creation.",
        )
        parser.add_argument(
            "--domain",
            help="Domain the app is deployed on. Falls back to settings.ALLOWED_HOSTS[0].",
        )

    def handle(self, **options):
        username = options[self.UserModel.USERNAME_FIELD]
        database = options["database"]
        qs = self.UserModel._default_manager.db_manager(database).filter(
            **{self.UserModel.USERNAME_FIELD: username}
        )
        if qs.exists():
            self.stdout.write(
                self.style.WARNING("Superuser account already exists, exiting")
            )
            return

        # env-var is supported out of the box from Django 3.0+
        password = options.get("password") or os.environ.get(
            "DJANGO_SUPERUSER_PASSWORD"
        )

        if password or options["generate_password"]:
            options["interactive"] = False

        # perform user creation from core Django
        super().handle(**options)

        user = qs.get()

        if not password and options["generate_password"]:
            options["password"] = self.UserModel.objects.make_random_password(length=20)

        if options["password"] or not PASSWORD_FROM_ENV_SUPPORTED:
            self.stdout.write("Setting user password...")
            user.set_password(options["password"])
            user.save()

        if options["generate_password"]:
            password_reset_path = reverse("admin_password_reset")
            default_host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else ""
            if default_host == "*":
                default_host = ""
            domain = options["domain"] or default_host

            pw_reset_link = (
                f"https://{domain}{password_reset_path}" if domain else "unknown url"
            )
            send_mail(
                f"Your admin user for {settings.PROJECT_NAME} ({domain or 'unknown url'})",
                (
                    f"Credentials for project: {settings.PROJECT_NAME}\n\n"
                    f"Username: {username}\nPassword reset link: {pw_reset_link}"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
