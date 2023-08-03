from rest_framework.reverse import reverse

from openforms.forms.constants import ConfirmationEmailOptions
from openforms.utils.tests.test_migrations import TestMigrations

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


class TestAddRadioType(TestMigrations):
    migrate_from = "0064_auto_20230113_1641"
    migrate_to = "0065_set_radio_data_type"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with radio",
            slug="definition-with-radio",
            configuration={
                "components": [
                    {
                        "key": "someRadioString",
                        "type": "radio",
                        "label": "Radiooo Striiing",
                    },
                    {
                        "key": "someRadioInt",
                        "type": "radio",
                        "label": "Radiooo Iiint",
                        "dataType": "int",
                    },
                    {
                        "key": "SomeTextField",
                        "type": "textfield",
                        "label": "Text Field",
                    },
                ]
            },
        )

    def test_radio_has_datatype(self):
        self.form_definition.refresh_from_db()

        self.assertEqual(
            self.form_definition.configuration["components"][0]["dataType"], "string"
        )
        self.assertEqual(
            self.form_definition.configuration["components"][1]["dataType"], "int"
        )
        self.assertNotIn(
            "dataType", self.form_definition.configuration["components"][2]
        )


class TestFixTypo(TestMigrations):
    migrate_from = "0066_merge_20230119_1618"
    migrate_to = "0067_fix_typo_20230124_1624"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition1 = FormDefinition.objects.create(
            name="Definition with typo",
            slug="definition-with-typo",
            configuration={
                "components": [
                    {
                        "key": "someString",
                        "registration": {"attribute": "Strainitiator_straatat"},
                    },
                ]
            },
        )
        # dummy form_definition for testing KeyError
        self.form_definition2 = FormDefinition.objects.create(
            name="Definition with missing registration key",
            slug="definition-with-missing-key",
            configuration={
                "components": [
                    {
                        "key": "someString",
                    },
                ]
            },
        )

    def test_typo_is_fixed(self):
        self.form_definition1.refresh_from_db()

        self.assertEqual(
            self.form_definition1.configuration["components"][0]["registration"][
                "attribute"
            ],
            "initiator_straat",
        )

    def test_missing_key(self):
        """Check that missing key does not cause an error"""

        self.form_definition2.refresh_from_db()


class TestAddDataSourceToOptions(TestMigrations):
    migrate_from = "0067_fix_typo_20230124_1624"
    migrate_to = "0068_add_options_data_source"

    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        self.form_definition = FormDefinition.objects.create(
            name="Definition with radio",
            slug="definition-with-radio",
            configuration={
                "components": [
                    {
                        "label": "Select Boxes",
                        "key": "selectBoxes",
                        "type": "selectboxes",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "defaultValue": {"a": True, "b": False},
                    },
                    {
                        "label": "Select",
                        "key": "select",
                        "data": {
                            "values": [
                                {"label": "A", "value": "a"},
                                {"label": "B", "value": "b"},
                            ],
                            "json": "",
                            "url": "",
                            "resource": "",
                            "custom": "",
                        },
                        "type": "select",
                        "defaultValue": "a",
                    },
                    {
                        "label": "Select",
                        "key": "select1",
                        "type": "select",
                        "multiple": True,
                        "data": {
                            "values": [
                                {"label": "A", "value": "a"},
                                {"label": "B", "value": "b"},
                            ]
                        },
                        "defaultValue": ["a", "b"],
                    },
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "defaultValue": "b",
                    },
                ]
            },
        )

    def test_options_have_data_source(self):
        self.form_definition.refresh_from_db()

        self.assertEqual(
            self.form_definition.configuration["components"][0]["openForms"]["dataSrc"],
            "manual",
        )
        self.assertEqual(
            self.form_definition.configuration["components"][1]["openForms"]["dataSrc"],
            "manual",
        )
        self.assertEqual(
            self.form_definition.configuration["components"][2]["openForms"]["dataSrc"],
            "manual",
        )
        self.assertEqual(
            self.form_definition.configuration["components"][3]["openForms"]["dataSrc"],
            "manual",
        )


class TestRemoveValueExpression(TestMigrations):
    migrate_from = "0069_form_appointment_enabled"
    migrate_to = "0070_remove_value_expression"

    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        self.form_definition = FormDefinition.objects.create(
            name="Definition with radio",
            slug="definition-with-radio",
            configuration={
                "components": [
                    {
                        "key": "repeatingGroup",
                        "type": "editgrid",
                        "components": [{"type": "textfield", "key": "name"}],
                    },
                    {"key": "textField", "type": "textfield"},
                    {
                        "label": "Select Boxes",
                        "key": "selectBoxes",
                        "type": "selectboxes",
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "openForms": {
                            "dataSrc": "variable",
                            "itemsExpression": {"var": "repeatingGroup"},
                            "valueExpression": {"var": "name"},
                        },
                    },
                    {
                        "label": "Select",
                        "key": "select",
                        "data": {
                            "values": [
                                {"label": "", "value": ""},
                            ],
                        },
                        "openForms": {
                            "dataSrc": "variable",
                            "itemsExpression": {"var": "textField"},
                        },
                        "type": "select",
                    },
                    {
                        "label": "Radio",
                        "key": "radio",
                        "type": "radio",
                        "values": [
                            {"label": "test", "value": "test"},
                        ],
                        "openForms": {
                            "dataSrc": "manual",
                        },
                    },
                ]
            },
        )

    def test_options_have_data_source(self):
        self.form_definition.refresh_from_db()

        self.assertNotIn(
            "openForms", self.form_definition.configuration["components"][0]
        )
        self.assertNotIn(
            "openForms", self.form_definition.configuration["components"][1]
        )

        self.assertEqual(
            self.form_definition.configuration["components"][2]["openForms"][
                "itemsExpression"
            ],
            {"map": [{"var": "repeatingGroup"}, {"var": "name"}]},
        )
        self.assertNotIn(
            "valueExpression",
            self.form_definition.configuration["components"][2]["openForms"],
        )

        self.assertEqual(
            self.form_definition.configuration["components"][3]["openForms"][
                "itemsExpression"
            ],
            {"var": "textField"},
        )
        self.assertNotIn(
            "valueExpression",
            self.form_definition.configuration["components"][3]["openForms"],
        )

        self.assertNotIn(
            "valueExpression",
            self.form_definition.configuration["components"][4]["openForms"],
        )
        self.assertNotIn(
            "itemsExpression",
            self.form_definition.configuration["components"][4]["openForms"],
        )


class TestChangeValidateOnSetting(TestMigrations):
    migrate_from = "0072_check_form_variable_datatype"
    migrate_to = "0073_change_bsn_validation"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with BSN",
            slug="definition-with-bsn",
            configuration={
                "components": [
                    {
                        "key": "BSNField",
                        "type": "bsn",
                        "label": "BSN Field",
                        "validateOn": "change",
                    }
                ]
            },
        )

    def test_validate_on_is_blur(self):
        self.form_definition.refresh_from_db()

        self.assertEqual(
            "blur", self.form_definition.configuration["components"][0]["validateOn"]
        )


class TestAddCustomErrorsNumberComponent(TestMigrations):
    migrate_from = "0073_change_bsn_validation"
    migrate_to = "0074_add_custom_errors_numbers"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with number component",
            slug="definition-with-number",
            configuration={
                "components": [
                    {
                        "key": "Number",
                        "type": "number",
                        "translatedErrors": {
                            "en": {"required": ""},
                            "nl": {"required": ""},
                        },
                    },
                    {
                        "key": "Text Field",
                        "type": "textfield",
                        "translatedErrors": {
                            "en": {"pattern": "", "required": "", "maxLength": ""},
                            "nl": {"pattern": "", "required": "", "maxLength": ""},
                        },
                    },
                ]
            },
        )

    def test_translated_errors_are_udpated(self):
        self.form_definition.refresh_from_db()

        self.assertEqual(
            {
                "en": {
                    "required": "",
                    "max": "",
                    "min": "",
                },
                "nl": {
                    "required": "",
                    "max": "",
                    "min": "",
                },
            },
            self.form_definition.configuration["components"][0]["translatedErrors"],
        )
        self.assertEqual(
            {
                "en": {"pattern": "", "required": "", "maxLength": ""},
                "nl": {"pattern": "", "required": "", "maxLength": ""},
            },
            self.form_definition.configuration["components"][1]["translatedErrors"],
        )


class TestRemoveConfirmationEmailForwardOptions(TestMigrations):
    migrate_from = "0075_form_send_confirmation_email"
    migrate_to = "0076_move_confirmation_email_setting"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        self.form1 = Form.objects.create(
            name="Form with no confirmation email",
            slug="form-with-no-confirmation-email",
            confirmation_email_option=ConfirmationEmailOptions.no_email,
        )
        self.form2 = Form.objects.create(
            name="Form with confirmation email global",
            slug="form-with-confirmation-email-global",
            confirmation_email_option=ConfirmationEmailOptions.global_email,
        )
        self.form3 = Form.objects.create(
            name="Form with confirmation email custom",
            slug="form-with-confirmation-email-custom",
            confirmation_email_option=ConfirmationEmailOptions.form_specific_email,
        )

    def test_forward_migration(self):
        self.form1.refresh_from_db()
        self.form2.refresh_from_db()
        self.form3.refresh_from_db()

        self.assertFalse(self.form1.send_confirmation_email)
        self.assertTrue(self.form2.send_confirmation_email)
        self.assertTrue(self.form3.send_confirmation_email)


class TestRemoveConfirmationEmailBackwardsOptions(TestMigrations):
    migrate_to = "0075_form_send_confirmation_email"
    migrate_from = "0076_move_confirmation_email_setting"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        self.form1 = Form.objects.create(
            name="Form with no confirmation email",
            slug="form-with-no-confirmation-email",
            send_confirmation_email=False,
        )
        self.form2 = Form.objects.create(
            name="Form with confirmation email global",
            slug="form-with-confirmation-email-global",
            send_confirmation_email=True,
        )
        self.form3 = Form.objects.create(
            name="Form with confirmation email custom",
            slug="form-with-confirmation-email-custom",
            send_confirmation_email=True,
        )

        ConfirmationEmailTemplate = apps.get_model(
            "emails", "ConfirmationEmailTemplate"
        )

        ConfirmationEmailTemplate.objects.create(
            content="Custom content", form=self.form2
        )  # Incomplete template
        ConfirmationEmailTemplate.objects.create(
            subject="Custom subject", content="Custom content", form=self.form3
        )  # Complete template

    def test_backwards_migration(self):
        self.form1.refresh_from_db()
        self.form2.refresh_from_db()
        self.form3.refresh_from_db()

        self.assertEqual(
            self.form1.confirmation_email_option, ConfirmationEmailOptions.no_email
        )
        self.assertEqual(
            self.form2.confirmation_email_option, ConfirmationEmailOptions.global_email
        )
        self.assertEqual(
            self.form3.confirmation_email_option,
            ConfirmationEmailOptions.form_specific_email,
        )


class TestAddShowInSummaryDefault(TestMigrations):
    migrate_from = "0079_replace_cosign_component"
    migrate_to = "0080_add_show_in_summary_default"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition = FormDefinition.objects.create(
            name="Definition with Content Component",
            slug="definition-with-content",
            configuration={
                "components": [
                    {
                        "type": "content",
                        "key": "content",
                        "html": "<p>WYSIWYG with <strong>markup</strong></p>",
                        "input": False,
                        "label": "Content",
                        "hidden": False,
                    }
                ]
            },
        )

    def test_forward_migration(self):
        self.form_definition.refresh_from_db()

        content_component = self.form_definition.configuration["components"][0]

        self.assertEqual(
            content_component,
            {
                "type": "content",
                "key": "content",
                "html": "<p>WYSIWYG with <strong>markup</strong></p>",
                "input": False,
                "label": "Content",
                "hidden": False,
                "showInSummary": False,
            },
        )


class TestMoveFormStepSlug(TestMigrations):
    app = "forms"
    migrate_from = "0085_auto_20230802_1025"
    migrate_to = "0086_migrate_form_definition_slugs"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        Form = apps.get_model("forms", "Form")

        configuration = {"components": []}
        fd1 = FormDefinition.objects.create(
            name="FD 1", slug="fd-1", configuration=configuration
        )
        fd2 = FormDefinition.objects.create(
            name="FD 2", slug="fd-2", is_reusable=True, configuration=configuration
        )

        form1 = Form.objects.create(name="Form 1")
        form2 = Form.objects.create(name="Form 2")

        FormStep.objects.create(form=form1, form_definition=fd1, order=0)
        FormStep.objects.create(form=form1, form_definition=fd2, order=1)
        FormStep.objects.create(form=form2, form_definition=fd2, order=0)

    def test_slugs_filled_from_form_definition(self):
        FormStep = self.apps.get_model("forms", "FormStep")

        form1_step_order_to_slug = {
            step.order: step.slug
            for step in FormStep.objects.filter(form__name="Form 1")
        }
        self.assertEqual(form1_step_order_to_slug, {0: "fd-1", 1: "fd-2"})

        form2_step_order_to_slug = {
            step.order: step.slug
            for step in FormStep.objects.filter(form__name="Form 2")
        }
        self.assertEqual(form2_step_order_to_slug, {0: "fd-2"})
