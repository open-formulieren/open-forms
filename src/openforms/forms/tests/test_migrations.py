from rest_framework.reverse import reverse

from openforms.utils.tests.test_migrations import TestMigrations

from ..api.serializers.logic.action_serializers import LogicComponentActionSerializer

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
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")

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


class FixBrokenConvertedLogicTests(TestMigrations):
    migrate_from = "0046_convert_advanced_logic"
    migrate_to = "0047_fix_broken_converted_rules"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormLogic = apps.get_model("forms", "FormLogic")

        form = Form.objects.create(name="Form", slug="form")
        rule1 = FormLogic.objects.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [{"var": "test1"}, "trigger value"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 1 Action 1",
                    "type": "property",
                    "state": False,
                    "property": {
                        "type": "boolean",
                        "label": "Hidden",
                        "value": "hidden",
                    },
                },
                # Valid rule
                {
                    "action": {
                        "name": "Rule 1 Action 1",
                        "type": "property",
                        "state": False,
                        "property": {
                            "type": "bool",
                            "label": "Hidden",
                            "value": "hidden",
                        },
                    },
                    "component": "test2",
                },
            ],
        )
        rule2 = FormLogic.objects.create(
            form=form,
            order=2,
            json_logic_trigger={"==": [{"var": "test1"}, "test"]},
            actions=[
                # Invalid rule
                {
                    "name": "Rule 2 Action 1",
                    "type": "property",
                    "property": {
                        "value": "validate",
                        "type": "json",
                    },
                    "state": {"required": True},
                }
            ],
        )

        self.form = form
        self.rule1 = rule1
        self.rule2 = rule2

    def test_migrate_logic(self):
        self.assertEqual(2, self.form.formlogic_set.count())

        self.rule1.refresh_from_db()
        self.rule2.refresh_from_db()

        serializer1 = LogicComponentActionSerializer(data=self.rule1.actions, many=True)
        self.assertTrue(serializer1.is_valid())

        serializer2 = LogicComponentActionSerializer(data=self.rule2.actions, many=True)
        self.assertTrue(serializer2.is_valid())


class TestChangeInlineEditSetting(TestMigrations):
    migrate_from = "0047_fix_broken_converted_rules"
    migrate_to = "0048_update_formio_default_setting"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with repeating group",
            slug="definition-with-repeating-group",
            configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "label": "Repeating Group",
                        "inlineEdit": False,
                        "components": [],
                    }
                ]
            },
        )

    def test_inline_edit_is_true(self):
        self.form_definition.refresh_from_db()

        self.assertTrue(
            self.form_definition.configuration["components"][0]["inlineEdit"]
        )


class TestUpdateTranslationFields(TestMigrations):
    migrate_from = "0050_auto_20221024_1252"
    migrate_to = "0051_update_translation_fields"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Vertaalbare naam",
            configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "label": "Repeating Group",
                        "inlineEdit": False,
                        "components": [],
                    }
                ]
            },
        )

    def test_update_translation_fields(self):
        self.form_definition.refresh_from_db()

        self.assertEqual(self.form_definition.name, "Vertaalbare naam")
        self.assertEqual(self.form_definition.name_nl, "Vertaalbare naam")
        self.assertEqual(self.form_definition.name_en, None)


class TestConvertURLsToUUIDs(TestMigrations):
    migrate_from = "0050_alter_formvariable_key"
    migrate_to = "0051_replace_urls_with_uuids"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        FormLogic = apps.get_model("forms", "FormLogic")

        form = Form.objects.create(name="Form", slug="form")
        form_definition = FormDefinition.objects.create(
            name="Vertaalbare naam",
            configuration={
                "components": [
                    {
                        "key": "test",
                        "type": "textfield",
                    }
                ]
            },
        )
        form_step = FormStep.objects.create(
            form=form, form_definition=form_definition, order=0
        )

        form_step_path = reverse(
            "api:form-steps-detail",
            kwargs={"form_uuid_or_slug": form.uuid, "uuid": form_step.uuid},
        )

        self.rule = FormLogic.objects.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [{"var": "test"}, "test"]},
            actions=[
                {
                    "form_step": f"http://example.com{form_step_path}",
                    "action": {
                        "name": "Step is not applicable",
                        "type": "step-not-applicable",
                    },
                }
            ],
        )
        self.form_step = form_step

    def test_assert_url_converted_correctly(self):
        self.rule.refresh_from_db()

        self.assertEqual(
            self.rule.actions[0]["form_step_uuid"], str(self.form_step.uuid)
        )


class TestChangeHideLabelSetting(TestMigrations):
    migrate_from = "0054_merge_20221114_1308"
    migrate_to = "0055_make_hidelabel_false"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with repeating group",
            slug="definition-with-repeating-group",
            configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "label": "Repeating Group",
                        "hideLabel": True,
                        "components": [],
                    },
                    {
                        "key": "SomeTextField",
                        "type": "textfield",
                        "label": "Text Field",
                        "hideLabel": True,
                    },
                ]
            },
        )

    def test_editgrid_hidelabel_false(self):
        self.form_definition.refresh_from_db()

        self.assertFalse(
            self.form_definition.configuration["components"][0]["hideLabel"]
        )
        self.assertTrue(
            self.form_definition.configuration["components"][1]["hideLabel"]
        )


class TestFixRulesWithCheckboxes(TestMigrations):
    migrate_from = "0055_make_hidelabel_false"
    migrate_to = "0056_fix_rules_with_selectboxes"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        Form = apps.get_model("forms", "Form")
        FormLogic = apps.get_model("forms", "FormLogic")

        form_definition = FormDefinition.objects.create(
            name="Definition with select boxes",
            slug="definition-with-select-boxes",
            configuration={
                "components": [
                    {
                        "key": "selectBoxes",
                        "type": "selectboxes",
                        "label": "Select Boxes",
                        "values": [
                            {
                                "label": "A",
                                "value": "a",
                            },
                            {
                                "label": "B",
                                "value": "b",
                            },
                        ],
                    },
                    {
                        "key": "textField",
                        "type": "textfield",
                        "label": "Text Field",
                    },
                ]
            },
        )

        form = Form.objects.create(name="Form", slug="form")
        FormStep.objects.create(form=form, form_definition=form_definition, order=0)

        self.rule_well_formatted = FormLogic.objects.create(
            form=form,
            order=1,
            json_logic_trigger={"==": [{"var": "selectBoxes.a"}, True]},
            actions=[],
        )
        self.rule_badly_formatted = FormLogic.objects.create(
            form=form,
            order=2,
            json_logic_trigger={"==": [{"var": "selectBoxes"}, "a"]},
            actions=[],
        )

    def test_fix_badly_formatted_rules(self):
        self.rule_well_formatted.refresh_from_db()
        self.rule_badly_formatted.refresh_from_db()

        self.assertEqual(
            self.rule_well_formatted.json_logic_trigger,
            {"==": [{"var": "selectBoxes.a"}, True]},
        )
        self.assertEqual(
            self.rule_badly_formatted.json_logic_trigger,
            {"==": [{"var": "selectBoxes.a"}, True]},
        )
