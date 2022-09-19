from openforms.utils.tests.test_migrations import TestMigrations

from ..models import Form, FormDefinition, FormStep

CONFIGURATION = {
    "components": [
        {"type": "textfield", "key": "test1"},
        {
            "type": "fieldset",
            "key": "test2",
            "components": [],
            "logic": [
                {
                    "name": "Rule 1",
                    "trigger": {
                        "type": "javascript",  # Not supported, will be skipped
                        "javascript": "result = data['test'];",
                    },
                    "actions": [
                        {
                            "name": "Rule 1 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": True,
                        }
                    ],
                },
                {
                    "name": "Rule 2",
                    "trigger": {
                        "type": "simple",
                        "simple": {
                            "show": True,
                            "when": "test1",
                            "eq": "trigger value",
                        },
                    },
                    "actions": [
                        {
                            "name": "Rule 2 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Hidden",
                                "value": "hidden",
                                "type": "boolean",
                            },
                            "state": False,
                        }
                    ],
                },
                {
                    "name": "Rule 3",
                    "trigger": {
                        "type": "json",
                        "json": {"==": [{"var": "test1"}, "test"]},
                    },
                    "actions": [
                        {
                            "name": "Rule 3 Action 1",
                            "type": "property",
                            "property": {
                                "label": "Required",
                                "value": "validate.required",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 2",
                            "type": "property",
                            "property": {
                                "label": "Disabled",
                                "value": "disabled",
                                "type": "boolean",
                            },
                            "state": True,
                        },
                        {
                            "name": "Rule 3 Action 3",
                            "type": "property",
                            "property": {
                                "label": "Title",
                                "value": "title",  # Not supported, will be skipped
                                "type": "string",
                            },
                            "text": "A new title",
                        },
                    ],
                },
            ],
        },
    ]
}


class ConvertFrontendAdvancedLogicTests(TestMigrations):
    migrate_from = "0002_auto_20210917_1114_squashed_0045_remove_formstep_optional"
    migrate_to = "0046_convert_advanced_logic"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        form_definition = FormDefinition.objects.create(
            name="Definition1",
            slug="definition1",
            configuration=CONFIGURATION,
        )
        form1 = Form.objects.create(name="Form1", slug="form-1")
        form2 = Form.objects.create(name="Form2", slug="form-2")
        FormStep.objects.create(form=form1, form_definition=form_definition, order=1)
        FormStep.objects.create(form=form2, form_definition=form_definition, order=2)
        self.form1 = form1
        self.form2 = form2
        self.form_definition = form_definition

    def test_migrate_logic(self):
        self.assertEqual(2, self.form1.formlogic_set.count())
        self.assertEqual(2, self.form2.formlogic_set.count())

        self.form_definition.refresh_from_db()

        self.assertEqual(
            [], self.form_definition.configuration["components"][1]["logic"]
        )
