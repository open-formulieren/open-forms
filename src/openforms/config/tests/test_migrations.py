from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.utils.tests.test_migrations import TestMigrations


class FamilyMembersDataApiMigrationTest(TestMigrations):
    migrate_from = "0058_alter_globalconfiguration_referentielijsten_services_to_reference_lists_services"
    migrate_to = "0060_copy_family_members_data_api"
    app = "config"

    def setUpBeforeMigration(self, apps):
        NPFamilyMembersModel = apps.get_model(
            "np_family_members", "FamilyMembersTypeConfig"
        )
        np_family_members_config, _ = NPFamilyMembersModel.objects.get_or_create(id=1)
        np_family_members_config.data_api = FamilyMembersDataAPIChoices.haal_centraal
        np_family_members_config.save()

    def test_copy_data_api_setting_to_global_config(self):
        GlobalConfigModel = self.apps.get_model("config", "GlobalConfiguration")
        config, _ = GlobalConfigModel.objects.get_or_create(id=1)

        self.assertEqual(
            config.family_members_data_api, FamilyMembersDataAPIChoices.haal_centraal
        )
