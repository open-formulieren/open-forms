from openforms.formio.utils import iter_components
from openforms.utils.tests.test_migrations import TestMigrations


class TestChangeOpenWhenEmptyConfiguration(TestMigrations):
    migrate_from = "0048_update_formio_default_setting"
    migrate_to = "0049_remove_editgrid_open_when_empty"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        start_components = [
            {
                "type": "editgrid",
                "key": "editgrid1",
                "components": [],
            },
            {
                "type": "editgrid",
                "key": "editgrid2",
                "openWhenEmpty": False,
                "components": [],
            },
            {
                "type": "editgrid",
                "key": "editgrid3",
                "openWhenEmpty": True,
                "components": [],
            },
            {
                "type": "fieldset",
                "key": "fieldset1",
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid4",
                        "openWhenEmpty": True,
                        "components": [],
                    },
                ],
            },
        ]
        FormDefinition.objects.create(
            name="Definition with repeating group",
            slug="definition-with-repeating-group",
            configuration={"components": start_components},
        )

    def test_open_when_empty_is_false(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fd = FormDefinition.objects.get()
        components = {
            component["key"]: component
            for component in iter_components(fd.configuration)
        }

        with self.subTest("editgrid1"):
            component = components["editgrid1"]

            self.assertNotIn("openWhenEmpty", component)

        with self.subTest("editgrid2"):
            component = components["editgrid2"]

            self.assertFalse(component["openWhenEmpty"])

        with self.subTest("editgrid3"):
            component = components["editgrid3"]

            self.assertFalse(component["openWhenEmpty"])

        with self.subTest("editgrid4"):
            component = components["editgrid4"]

            self.assertFalse(component["openWhenEmpty"])
