from django.db.migrations.state import StateApps

from zgw_consumers.constants import APITypes

from openforms.utils.tests.test_migrations import TestMigrations


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


class SetZGWAPIGroupTest(TestMigrations):
    app = "zgw_apis"
    migrate_from = "0012_remove_zgwapigroupconfig_informatieobjecttype_and_more"
    migrate_to = "0013_set_zgw_api_group"

    def setUpBeforeMigration(self, apps: StateApps):
        ZGWApiGroupConfig = apps.get_model("zgw_apis", "ZGWApiGroupConfig")
        ZgwConfig = apps.get_model("zgw_apis", "ZgwConfig")
        FormRegistrationBackend = apps.get_model("forms", "FormRegistrationBackend")
        Form = apps.get_model("forms", "Form")

        self.group = ZGWApiGroupConfig.objects.create(name="zgw api group")
        ZgwConfig.objects.create(default_zgw_api_group=self.group)
        form = Form.objects.create(name="test form")

        FormRegistrationBackend.objects.create(
            form=form,
            key="global-defaults",
            name="global-defaults",
            backend="zgw-create-zaak",
            options={},
        )

    def test_sets_zgw_api_group(self):
        FormRegistrationBackend = self.apps.get_model(
            "forms", "FormRegistrationBackend"
        )

        backend = FormRegistrationBackend.objects.get()
        self.assertEqual(backend.options["zgw_api_group"], self.group.pk)
