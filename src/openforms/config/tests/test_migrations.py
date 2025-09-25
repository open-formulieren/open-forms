from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.utils.tests.test_migrations import TestMigrations


class FamilyMembersDataApiMigrationTest(TestMigrations):
    migrate_from = "0055_v270_to_v300"
    migrate_to = "0056_v300_to_v330"
    app = "config"

    def setUpBeforeMigration(self, apps):
        NPFamilyMembersModel = apps.get_model(
            "np_family_members", "FamilyMembersTypeConfig"
        )
        np_family_members_config, _ = NPFamilyMembersModel.objects.get_or_create(id=1)
        np_family_members_config.data_api = FamilyMembersDataAPIChoices.haal_centraal
        np_family_members_config.save()

        GlobalConfigModel = apps.get_model("config", "GlobalConfiguration")
        GlobalConfigModel.objects.get_or_create(id=1)

    def test_copy_data_api_setting_to_global_config(self):
        GlobalConfigModel = self.apps.get_model("config", "GlobalConfiguration")
        config = GlobalConfigModel.objects.first()

        self.assertEqual(
            config.family_members_data_api, FamilyMembersDataAPIChoices.haal_centraal
        )
