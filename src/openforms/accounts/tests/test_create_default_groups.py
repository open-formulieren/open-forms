from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase

from ..management.commands.create_default_groups import (
    BEHANDELAARS_PERMISSIONS,
    FUNCTIONAL_BEHEERS_PERMISSIONS,
    REDACTUERS_PERMISSIONS,
)


class CreateDefaultGroupsTests(TestCase):
    def test_create_default_groups_command(self):
        call_command("create_default_groups")

        self.assertTrue(Group.objects.filter(name="Beheerders").exists())
        self.assertTrue(Group.objects.filter(name="Functioneel beheers").exists())
        self.assertTrue(Group.objects.filter(name="Redacteurs").exists())
        self.assertTrue(Group.objects.filter(name="Behandelaars").exists())

        self.assertQuerysetEqual(
            Group.objects.get(name="Beheerders").permissions.all(),
            Permission.objects.all(),
            transform=lambda x: x,
        )

        permissions_name_to_value = {
            "Functioneel beheers": FUNCTIONAL_BEHEERS_PERMISSIONS,
            "Redacteurs": REDACTUERS_PERMISSIONS,
            "Behandelaars": BEHANDELAARS_PERMISSIONS,
        }

        for group_name, permissions in permissions_name_to_value.items():
            with self.subTest(group_name=group_name, permissions=permissions):
                self.assertQuerysetEqual(
                    Group.objects.get(name=group_name).permissions.all(),
                    Permission.objects.filter(name__in=permissions),
                    transform=lambda x: x,
                )
