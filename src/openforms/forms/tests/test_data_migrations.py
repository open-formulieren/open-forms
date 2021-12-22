from openforms.utils.tests.test_migrations import TestMigrations


class ReplaceWidgetDataMigrationTests(TestMigrations):
    migrate_from = "0012_merge_20211222_0831"
    migrate_to = "0013_auto_20211220_1755"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition_uuid = FormDefinition.objects.create(
            name="Test widget replace",
            slug="test-widget-replace",
            configuration={
                "components": [
                    {"type": "select", "widget": "html5"},
                    {
                        "type": "fieldset",
                        "components": [{"type": "select", "widget": "html5"}],
                    },
                    {
                        "type": "columns",
                        "columns": [
                            {"components": [{"type": "select", "widget": "html5"}]}
                        ],
                    },
                ]
            },
        ).uuid

    def test_widget_recursively_replaced(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        update_form_definition = FormDefinition.objects.get(
            uuid=self.form_definition_uuid
        )

        self.assertEqual(
            "choicesjs", update_form_definition.configuration["components"][0]["widget"]
        )
        self.assertEqual(
            "choicesjs",
            update_form_definition.configuration["components"][1]["components"][0][
                "widget"
            ],
        )
        self.assertEqual(
            "choicesjs",
            update_form_definition.configuration["components"][2]["columns"][0][
                "components"
            ][0]["widget"],
        )
