from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase


class TestMigrations(TestCase):
    """
    Adapted from https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
    """

    app = None
    migrate_from = None
    migrate_to = None

    def setUp(self):
        assert self.migrate_from and self.migrate_to and self.app, (
            "TestCase '%s' must define migrate_from, migrate_to and app properties"
            % type(self).__name__
        )
        self.migrate_from = [(self.app, self.migrate_from)]
        self.migrate_to = [(self.app, self.migrate_to)]
        executor = MigrationExecutor(connection)
        old_apps = executor.loader.project_state(self.migrate_from).apps

        # Reverse to the original migration
        executor.migrate(self.migrate_from)

        self.setUpBeforeMigration(old_apps)

        # Run the migration to test
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(self.migrate_to)

        self.apps = executor.loader.project_state(self.migrate_to).apps

    def setUpBeforeMigration(self, apps):
        pass


class ReplateWidgetDataMigrationTests(TestMigrations):
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
