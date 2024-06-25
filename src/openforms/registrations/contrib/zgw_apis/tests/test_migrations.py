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


class NoZgwConfigDoesntCreateZGWApiGroupMigrationTest(TestMigrations):
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


class MoveDefaultsToFormTest(TestMigrations):
    app = "zgw_apis"
    migrate_from = "0010_zgwapigroupconfig_content_json"
    migrate_to = "0011_move_zgw_api_group_defaults_to_form"

    def setUpBeforeMigration(self, apps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")
        Service = apps.get_model("zgw_consumers", "Service")
        Form = apps.get_model("forms", "Form")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")

        # create services
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
        services = {
            "zrc_service": zrc,
            "drc_service": drc,
            "ztc_service": ztc,
        }

        # create different config groups & default config
        group1 = ZGWApiGroupConfig.objects.create(
            zaaktype="http://www.example-ztc.com/api/v1/zaaktypen/1",
            informatieobjecttype="http://www.example-ztc.com/api/v1/informatieobjecttypen/1",
            **services,
        )
        group2 = ZGWApiGroupConfig.objects.create(
            zaaktype="http://www.example-ztc.com/api/v1/zaaktypen/2",
            informatieobjecttype="http://www.example-ztc.com/api/v1/informatieobjecttypen/2",
            **services,
        )
        ZgwConfig.objects.create(default_zgw_api_group=group1)

        # form with different backend options
        form = Form.objects.create(name="test form")
        self.backend1 = FormRegistrationBackend.objects.create(
            form=form,
            key="global-defaults",
            name="global-defaults",
            backend="zgw-create-zaak",
            options={},
        )
        self.backend2 = FormRegistrationBackend.objects.create(
            form=form,
            key="different-group",
            name="different-group",
            backend="zgw-create-zaak",
            options={"zgw_api_group": group2.id},
        )
        self.backend3 = FormRegistrationBackend.objects.create(
            form=form,
            key="explicit-types-set",
            name="explicit-types-set",
            backend="zgw-create-zaak",
            options={
                "zaaktype": "http://www.example-ztc.com/api/v1/zaaktypen/3",
                "informatieobjecttype": "http://www.example-ztc.com/api/v1/informatieobjecttypen/3",
            },
        )
        self.backend4 = FormRegistrationBackend.objects.create(
            form=form,
            key="explicit-types-set-explicit-group",
            name="explicit-types-set-explicit-group",
            backend="zgw-create-zaak",
            options={
                "zgw_api_group": group2.id,
                "zaaktype": "http://www.example-ztc.com/api/v1/zaaktypen/3",
                "informatieobjecttype": "http://www.example-ztc.com/api/v1/informatieobjecttypen/3",
            },
        )

    def test_defaults_added_to_backends(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )
        backend1 = FormRegistrationBackend.objects.get(id=self.backend1.id)
        backend2 = FormRegistrationBackend.objects.get(id=self.backend2.id)
        backend3 = FormRegistrationBackend.objects.get(id=self.backend3.id)
        backend4 = FormRegistrationBackend.objects.get(id=self.backend4.id)

        with self.subTest("backend 1"):
            options = backend1.options
            self.assertIn("zaaktype", options)
            self.assertEqual(
                options["zaaktype"], "http://www.example-ztc.com/api/v1/zaaktypen/1"
            )

            self.assertIn("informatieobjecttype", options)
            self.assertEqual(
                options["informatieobjecttype"],
                "http://www.example-ztc.com/api/v1/informatieobjecttypen/1",
            )

        with self.subTest("backend 2"):
            options = backend2.options
            self.assertIn("zaaktype", options)
            self.assertEqual(
                options["zaaktype"], "http://www.example-ztc.com/api/v1/zaaktypen/2"
            )

            self.assertIn("informatieobjecttype", options)
            self.assertEqual(
                options["informatieobjecttype"],
                "http://www.example-ztc.com/api/v1/informatieobjecttypen/2",
            )

        with self.subTest("backend 3"):
            options = backend3.options
            self.assertIn("zaaktype", options)
            self.assertEqual(
                options["zaaktype"], "http://www.example-ztc.com/api/v1/zaaktypen/3"
            )

            self.assertIn("informatieobjecttype", options)
            self.assertEqual(
                options["informatieobjecttype"],
                "http://www.example-ztc.com/api/v1/informatieobjecttypen/3",
            )

        with self.subTest("backend 4"):
            options = backend4.options
            self.assertIn("zaaktype", options)
            self.assertEqual(
                options["zaaktype"], "http://www.example-ztc.com/api/v1/zaaktypen/3"
            )

            self.assertIn("informatieobjecttype", options)
            self.assertEqual(
                options["informatieobjecttype"],
                "http://www.example-ztc.com/api/v1/informatieobjecttypen/3",
            )
