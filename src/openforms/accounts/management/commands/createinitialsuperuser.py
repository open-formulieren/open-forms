from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.urls import exceptions, reverse


class Command(BaseCommand):
    help = "Creates an initial superuser account and mails the credentials to the specified email"

    def add_arguments(self, parser):
        parser.add_argument(
            "username", help="Specifies the username for the superuser.",
        )
        parser.add_argument(
            "email", help="Specifies the email for the superuser.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        email = options["email"]

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING("Initial superuser already exists, doing nothing")
            )
            return

        password = User.objects.make_random_password(length=20)
        user = User.objects.create_superuser(
            username=username, email=email, password=password
        )

        try:
            link = f'{settings.ALLOWED_HOSTS[0]}{reverse("admin:index")}'
        except IndexError:
            link = "unknown url"
        except exceptions.NoReverseMatch:
            link = settings.ALLOWED_HOSTS[0]

        send_mail(
            f"Credentials for {settings.PROJECT_NAME} ({link})",
            f"Credentials for project: {settings.PROJECT_NAME}\n\nUsername: {username}\nPassword: {password}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        self.stdout.write(self.style.SUCCESS("Initial superuser successfully created"))
