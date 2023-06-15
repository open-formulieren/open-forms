from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes

from openforms.utils.tests.test_migrations import TestMigrations


class MoveExistingZGWConfigMigrationTests(TestMigrations):
    migrate_from = "0006_zgwapigroupconfig"
    migrate_to = "0007_move_singleton_data"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")
        Service = apps.get_model("zgw_consumers", "Service")

        zrc = Service.objects.create(
            label="Zaak API",
            api_root="http://www.example-zrc.com/api/v1/",
            api_type=APITypes.zrc,
        )
        drc = Service.objects.create(
            label="Document API",
            api_root="http://www.example-drc.com/api/v1/",
            api_type=APITypes.drc,
        )
        ztc = Service.objects.create(
            label="Catalogi API",
            api_root="http://www.example-ztc.com/api/v1/",
            api_type=APITypes.ztc,
        )

        ZgwConfig.objects.create(
            zrc_service=zrc,
            drc_service=drc,
            ztc_service=ztc,
            zaaktype="http://www.example-ztc.com/api/v1/zaaktype/111-222-333",
            informatieobjecttype="http://www.example-ztc.com/api/v1/zaaktype/111-222-333",
            organisatie_rsin="100000009",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            doc_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
            auteur="testeerrr",
        )

    def test_services_migrated_correctly(self):
        ZGWApiGroupConfig = self.apps.get_model("zgw_apis", "ZGWApiGroupConfig")

        migrated_services = ZGWApiGroupConfig.objects.all()

        self.assertEqual(1, migrated_services.count())

        group = migrated_services.get()

        self.assertEqual(group.zrc_service.label, "Zaak API")
        self.assertEqual(group.drc_service.label, "Document API")
        self.assertEqual(group.ztc_service.label, "Catalogi API")
        self.assertEqual(
            group.zaaktype, "http://www.example-ztc.com/api/v1/zaaktype/111-222-333"
        )
        self.assertEqual(
            group.informatieobjecttype,
            "http://www.example-ztc.com/api/v1/zaaktype/111-222-333",
        )
        self.assertEqual(group.organisatie_rsin, "100000009")
        self.assertEqual(
            group.zaak_vertrouwelijkheidaanduiding,
            VertrouwelijkheidsAanduidingen.openbaar,
        )
        self.assertEqual(
            group.doc_vertrouwelijkheidaanduiding,
            VertrouwelijkheidsAanduidingen.beperkt_openbaar,
        )
        self.assertEqual(group.auteur, "testeerrr")


class ReconfigureSoloModelBackwardsMigrationTests(TestMigrations):
    migrate_to = "0006_zgwapigroupconfig"
    migrate_from = "0007_move_singleton_data"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")

        ZgwConfig.objects.create()
        self.zgw_group1 = ZGWApiGroupConfig.objects.create(
            name="ZGW API 1",
            auteur="test 1",
        )
        self.zgw_group2 = ZGWApiGroupConfig.objects.create(
            name="ZGW API 2",
            auteur="test 2",
        )
        self.assertTrue(self.zgw_group1.pk < self.zgw_group2.pk)

    def test_solo_reconfigured_correctly(self):
        ZgwConfig = self.apps.get_model("zgw_apis", "ZgwConfig")

        solo = ZgwConfig.objects.get()

        self.assertEqual(solo.auteur, "test 1")


class BackwardsMigrationNoZGWGroupTests(TestMigrations):
    migrate_to = "0006_zgwapigroupconfig"
    migrate_from = "0007_move_singleton_data"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")

        ZgwConfig.objects.create()

    def test_solo_reconfigured_correctly(self):
        ZgwConfig = self.apps.get_model("zgw_apis", "ZgwConfig")

        solo = ZgwConfig.objects.get()

        self.assertIsNone(solo.zrc_service)


class NoZgwConfigDoesntCreateZGWApiGrouMigrationTest(TestMigrations):
    migrate_from = "0006_zgwapigroupconfig"
    migrate_to = "0007_move_singleton_data"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")

        self.assertFalse(ZgwConfig.objects.exists())

    def test_no_zgw_api_group_created(self):
        ZGWApiGroupConfig = self.apps.get_model("zgw_apis", "ZGWApiGroupConfig")

        self.assertFalse(ZGWApiGroupConfig.objects.exists())


class AddDefaultToSoloModelTests(TestMigrations):
    migrate_from = "0008_auto_20230608_1443"
    migrate_to = "0009_add_default"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")
        Service = apps.get_model("zgw_consumers", "Service")

        zrc = Service.objects.create(
            label="Zaak API",
            api_root="http://www.example-zrc.com/api/v1/",
            api_type=APITypes.zrc,
        )
        drc = Service.objects.create(
            label="Document API",
            api_root="http://www.example-drc.com/api/v1/",
            api_type=APITypes.drc,
        )
        ztc = Service.objects.create(
            label="Catalogi API",
            api_root="http://www.example-ztc.com/api/v1/",
            api_type=APITypes.ztc,
        )

        ZgwConfig.objects.create()
        self.zgw_group = ZGWApiGroupConfig.objects.create(
            name="ZGW API",
            zrc_service=zrc,
            drc_service=drc,
            ztc_service=ztc,
            zaaktype="http://www.example-ztc.com/api/v1/zaaktype/111-222-333",
            informatieobjecttype="http://www.example-ztc.com/api/v1/zaaktype/111-222-333",
            organisatie_rsin="100000009",
            zaak_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            doc_vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
            auteur="testeerrr",
        )

    def test_services_migrated_correctly(self):
        ZgwConfig = self.apps.get_model("zgw_apis", "ZgwConfig")

        solo = ZgwConfig.objects.get()

        self.assertEqual(solo.default_zgw_api_group.pk, self.zgw_group.pk)


class NoZgwGroupLeavesConfigEmptyMigrationTest(TestMigrations):
    migrate_from = "0008_auto_20230608_1443"
    migrate_to = "0009_add_default"
    app = "zgw_apis"

    def setUpBeforeMigration(self, apps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")

        self.assertFalse(ZGWApiGroupConfig.objects.exists())

        ZgwConfig.objects.create()

    def test_no_zgw_api_group_created(self):
        ZgwConfig = self.apps.get_model("zgw_apis", "ZgwConfig")

        solo = ZgwConfig.objects.get()

        self.assertIsNone(solo.default_zgw_api_group)
