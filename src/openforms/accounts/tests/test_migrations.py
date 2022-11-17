from django.core.management import call_command

from openforms.utils.tests.test_migrations import TestMigrations


class ConvertFrontendAdvancedLogicTests(TestMigrations):
    migrate_from = "0006_user_employee_id"
    migrate_to = "0007_remove_delete_user_perm"
    app = "accounts"

    def setUpBeforeMigration(self, apps):
        call_command("loaddata", "default_groups", verbosity=0)

        Group = apps.get_model("auth", "group")
        default_groups = Group.objects.filter(
            name__in=["Beheerders", "Functioneel beheer"]
        )

        Permission = apps.get_model("auth", "permission")
        delete_user_permission = Permission.objects.get(codename="delete_user")
        for group in default_groups:
            group.permissions.add(delete_user_permission)

    def test_no_user_delete_permission(self):
        Group = self.apps.get_model("auth", "group")
        Permission = self.apps.get_model("auth", "permission")
        default_groups = Group.objects.filter(
            name__in=["Beheerders", "Functioneel beheer"]
        )

        for group in default_groups:
            self.assertFalse(group.permissions.filter(codename="delete_user").exists())

        self.assertTrue(Permission.objects.filter(codename="delete_user").exists())
