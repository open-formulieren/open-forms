from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

REDACTUERS_PERMISSIONS = [
    "Can add Confirmation email template",
    "Can change Confirmation email template",
    "Can delete Confirmation email template",
    "Can view Confirmation email template",
    "Can add form",
    "Can change form",
    "Can delete form",
    "Can view form",
    "Can add Form definition",
    "Can change Form definition",
    "Can delete Form definition",
    "Can view Form definition",
    "Can add form step",
    "Can change form step",
    "Can delete form step",
    "Can view form step",
]


FUNCTIONAL_BEHEERS_PERMISSIONS = [
    "Can add BRP Configuration",
    "Can change BRP Configuration",
    "Can view BRP Configuration",
    "Can add General configuration",
    "Can change General configuration",
    "Can view General configuration",
    "Can add haal centraal config",
    "Can change haal centraal config",
    "Can view haal centraal config",
    "Can add Haal Centraal configuration",
    "Can change Haal Centraal configuration",
    "Can view Haal Centraal configuration",
    "Can add SOAP service",
    "Can change SOAP service",
    "Can view SOAP service",
    "Can add stuf bg config",
    "Can change stuf bg config",
    "Can view stuf bg config",
    "Can add ZGW API's configuration",
    "Can change ZGW API's configuration",
    "Can view ZGW API's configuration",
    "Can add NLX configuration",
    "Can change NLX configuration",
    "Can view NLX configuration",
    "Can add service",
    "Can change service",
    "Can view service",
]


BEHANDELAARS_PERMISSIONS = ["Can view Submission"]


class Command(BaseCommand):
    help = "Creates the default permissions for that users could have"

    def handle(self, *args, **options):
        beheerders_group = Group.objects.create(name="Beheerders")
        beheerders_group.permissions.add(*Permission.objects.all())

        functional_beheer_group = Group.objects.create(name="Functioneel beheers")
        functional_beheer_permissions = Permission.objects.filter(
            name__in=FUNCTIONAL_BEHEERS_PERMISSIONS
        )
        functional_beheer_group.permissions.add(*functional_beheer_permissions)

        redacteurs_group = Group.objects.create(name="Redacteurs")
        redacteurs_permissions = Permission.objects.filter(
            name__in=REDACTUERS_PERMISSIONS
        )
        redacteurs_group.permissions.add(*redacteurs_permissions)

        behandelaars_group = Group.objects.create(name="Behandelaars")
        behandelaars_permissions = Permission.objects.filter(
            name__in=BEHANDELAARS_PERMISSIONS
        )
        behandelaars_group.permissions.add(*behandelaars_permissions)

        self.stdout.write(self.style.SUCCESS("Groups successfully created"))
