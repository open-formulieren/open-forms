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
    migrate_from = "0058_formdefinition_component_translations"
    migrate_to = "0059_editgrid_inline_false"
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
                        "inlineEdit": True,
                        "components": [],
                    }
                ]
            },
        )

    def test_inline_edit_is_true(self):
        self.form_definition.refresh_from_db()

        self.assertFalse(
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
    migrate_from = "0051_replace_urls_with_uuids"
    migrate_to = "0056_merge_20221122_1513"
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


class TestLogicParsing(TestMigrations):
    migrate_from = "0002_auto_20210917_1114_squashed_0045_remove_formstep_optional"
    migrate_to = "0046_convert_advanced_logic"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        components = [
            {
                "type": "fieldset",
                "key": "fieldset-1",
                "logic": [
                    {
                        "trigger": {
                            "type": "simple",
                            "simple": {
                                "show": True,
                                "when": "non-existing-object",
                                "eq": "trigger value",
                            },
                        },
                        "actions": [
                            {
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
                ],
            },
        ]
        form_def = FormDefinition.objects.create(
            slug="form_def", configuration={"components": components}
        )
        form = Form.objects.create(slug="form")
        FormStep.objects.create(form=form, form_definition=form_def, order=0)

    def test_logic_records(self):
        """Check that form definition is migrated correctly

        The test checks that migrations from 1.1.x to 2.0.1 with form definitions
        containing references to non-existing objects (a) do not crash and (b) don't
        trigger any logic actions. The forms themselves are left unmodified (garbage in,
        garbage out).
        """
        FormLogic = self.apps.get_model("forms", "FormLogic")
        logic_records = FormLogic.objects.all()
        self.assertFalse(logic_records)


class GenerateLogicDescriptions(TestMigrations):
    app = "forms"
    migrate_from = "0060_formlogic_description"
    migrate_to = "0061_generate_logic_rule_descriptions"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        Form = apps.get_model("forms", "Form")
        FormLogic = apps.get_model("forms", "FormLogic")
        FormStep = apps.get_model("forms", "FormStep")

        form = Form.objects.create(slug="form")
        form_def = FormDefinition.objects.create(
            slug="form_def",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                    },
                    {
                        "type": "editgrid",
                        "key": "items",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "name",
                            },
                        ],
                    },
                ]
            },
        )
        FormStep.objects.create(form=form, form_definition=form_def, order=0)
        # simple rule
        fl1 = FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"!=": [{"var": "textfield"}, "foo"]},
            actions=[
                {
                    "action": {
                        "type": "property",
                        "state": False,
                        "property": {"type": "bool", "value": "hidden"},
                    },
                    "component": "items",
                }
            ],
        )
        self.fl1_pk = fl1.pk
        # complex rule
        fl2 = FormLogic.objects.create(
            form=form,
            order=1,
            json_logic_trigger={
                ">": [
                    {
                        "reduce": [
                            {"var": "items"},
                            {"+": [{"var": "accumulator"}, 1]},
                            0,
                        ]
                    },
                    1,
                ]
            },
            actions=[
                {
                    "action": {
                        "type": "property",
                        "state": False,
                        "property": {"type": "bool", "value": "hidden"},
                    },
                    "component": "textfield",
                }
            ],
        )
        self.fl2_pk = fl2.pk

    def test_description_filled_simple_rule(self):
        FormLogic = self.apps.get_model("forms", "FormLogic")
        instance = FormLogic.objects.get(pk=self.fl1_pk)

        self.assertNotEqual(instance.description, "")

    def test_description_filled_complex_rule(self):
        FormLogic = self.apps.get_model("forms", "FormLogic")
        instance = FormLogic.objects.get(pk=self.fl2_pk)

        self.assertNotEqual(instance.description, "")
