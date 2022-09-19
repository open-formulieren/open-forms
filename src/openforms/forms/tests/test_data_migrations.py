from unittest import skip

from openforms.utils.tests.test_migrations import TestMigrations


@skip("Code is moved to squashed migration, these tests are now broken.")
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


@skip("Code is moved to squashed migration, these tests are now broken.")
class MoveOfImageDataMigrationTests(TestMigrations):
    migrate_from = "0013_auto_20211220_1755"
    migrate_to = "0014_file_component"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        self.form_definition_uuid = FormDefinition.objects.create(
            name="Test image replace",
            slug="test-image-replace",
            configuration={
                "components": [
                    {
                        "type": "file",
                        "image": {"resize": {"width": 1000, "height": 1000}},
                    },
                    {
                        "type": "fieldset",
                        "components": [
                            {
                                "type": "file",
                                "image": {"resize": {"width": 1000, "height": 1000}},
                            }
                        ],
                    },
                    {
                        "type": "columns",
                        "columns": [
                            {
                                "components": [
                                    {
                                        "type": "file",
                                        "image": {
                                            "resize": {"width": 1000, "height": 1000}
                                        },
                                    }
                                ]
                            }
                        ],
                    },
                ]
            },
        ).uuid

    def test_image_recursively_replaced(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        update_form_definition = FormDefinition.objects.get(
            uuid=self.form_definition_uuid
        )

        elem = update_form_definition.configuration["components"][0]
        self.assertEqual(
            elem["of"],
            {"image": {"resize": {"width": 1000, "height": 1000}}},
        )
        self.assertEqual(elem["image"], False)

        elem = update_form_definition.configuration["components"][1]["components"][0]
        self.assertEqual(
            elem["of"],
            {"image": {"resize": {"width": 1000, "height": 1000}}},
        )
        self.assertEqual(elem["image"], False)

        elem = update_form_definition.configuration["components"][2]["columns"][0][
            "components"
        ][0]
        self.assertEqual(
            elem["of"],
            {"image": {"resize": {"width": 1000, "height": 1000}}},
        )
        self.assertEqual(elem["image"], False)


@skip("Code is moved to squashed migration, these tests are now broken.")
class FormLogicOrderingMigrationTests(TestMigrations):
    migrate_from = "0028_auto_20220623_1257"
    migrate_to = "0029_make_logic_order_explicit"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        FormLogic = apps.get_model("forms", "FormLogic")
        FormDefinition = apps.get_model("forms", "FormDefinition")

        # set up a complex nested tree with possibly corrupted data to test the
        # depth-first ordering logic
        components = [
            {
                "type": "textfield",
                "key": "top-level-first",
            },
            {
                "type": "fieldset",
                "components": [
                    {
                        "type": "fieldset",
                        "key": "nested1",
                        "components": [
                            {
                                "type": "postcode",
                                "key": "postcode",
                            }
                        ],
                    }
                ],
            },
            {
                "type": "textfield",
                "key": "top-level-last",
            },
        ]
        form_definition1 = FormDefinition.objects.create(
            slug="fd1", configuration={"components": components}
        )
        form_definition2 = FormDefinition.objects.create(
            slug="fd2",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "second-step",
                    }
                ]
            },
        )

        # set up two forms to test the order_with_respect_to behaviour
        form1 = Form.objects.create(slug="form-1")
        FormStep.objects.create(form=form1, form_definition=form_definition2, order=1)
        FormStep.objects.create(form=form1, form_definition=form_definition1, order=0)
        # create form logic rules in "bad" order
        form1_rule_1 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"!": {"==": ["some-value", {"var": "second-step"}]}},
            actions=[],
            is_advanced=True,  # advanced goes to the end
        )
        form1_rule_2 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "unknown-key"}, "some-value"]},
            actions=[],
            is_advanced=False,  # ambiguous goes before advanced
        )
        # multiple rules for the same key are ordered by pk
        form1_rule_3 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "top-level-first"}, "foo"]},
            actions=[],
        )
        form1_rule_4 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "top-level-first"}, "foo"]},
            actions=[],
        )
        form1_rule_5 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "top-level-last"}, "foo"]},
            actions=[],
        )
        # logic rules must be ordered by step
        form1_rule_6 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "second-step"}, "foo"]},
            actions=[],
        )
        # depth first, so we create them in reverse depth order
        form1_rule_7 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "nested1"}, "foo"]},
            actions=[],
        )
        form1_rule_8 = FormLogic.objects.create(
            form=form1,
            order=0,
            json_logic_trigger={"==": [{"var": "postcode"}, "foo"]},
            actions=[],
        )

        self.expected_form_1_order = [
            # no component keys used -> first
            form1_rule_2,
            # simple logic
            form1_rule_3,
            form1_rule_4,  # ordered by component key and then pk
            form1_rule_7,  # parent of depth first key
            form1_rule_8,  # depth first
            form1_rule_5,  # ordered by component key
            # step 2 used -> after everything with step 1
            form1_rule_1,  # ordered by pk if same steps/keys
            form1_rule_6,  # belongs to second step
        ]

        form2 = Form.objects.create(slug="form-2")
        FormStep.objects.create(form=form2, form_definition=form_definition2, order=0)
        FormLogic.objects.create(
            form=form2,
            order=0,
            json_logic_trigger={"==": ["some-value", {"var": "second-step"}]},
            actions=[],
            is_advanced=False,
        )

    def test_ordering_set_correctly(self):
        Form = self.apps.get_model("forms", "Form")

        form1_rules = Form.objects.get(slug="form-1").formlogic_set.all()

        self.assertQuerysetEqual(
            form1_rules.values_list("json_logic_trigger", flat=True),
            [form.json_logic_trigger for form in self.expected_form_1_order],
            transform=lambda x: x,
        )

        # check that the values are all unique
        order_values = list(form1_rules.values_list("order", flat=True))
        self.assertEqual(order_values, [0, 1, 2, 3, 4, 5, 6, 7])

        # check that ordering is with respect to form
        form2_rule = Form.objects.get(slug="form-2").formlogic_set.get()
        self.assertEqual(form2_rule.order, 0)


@skip("Code is moved to squashed migration, these tests are now broken.")
class AdvancedFormLogicOrderingMigrationTests(TestMigrations):
    migrate_from = "0028_auto_20220623_1257"
    migrate_to = "0029_make_logic_order_explicit"
    app = "forms"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormStep = apps.get_model("forms", "FormStep")
        FormLogic = apps.get_model("forms", "FormLogic")
        FormDefinition = apps.get_model("forms", "FormDefinition")

        # set up two steps and some advanced rules that can be re-ordered properly
        form_definition1 = FormDefinition.objects.create(
            slug="fd1",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    },
                    {
                        "type": "textfield",
                        "key": "text2",
                    },
                ]
            },
        )
        form_definition2 = FormDefinition.objects.create(
            slug="fd2",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text3",
                    }
                ]
            },
        )
        form = Form.objects.create(slug="form")
        FormStep.objects.create(form=form, form_definition=form_definition1, order=0)
        FormStep.objects.create(form=form, form_definition=form_definition2, order=1)

        # set up advanced rules that can be explicitly ordered based on which components
        # they use.
        #
        # rule 1: doesn't use any variables/keys -> can go first
        # rule 2: uses a var from step 2 -> goes after step 1 rules
        # rule 3: only uses step 1 vars
        # rule 4: uses step 1 and step 2 vars
        rule_1 = FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"!": {"==": ["some-value", "some-value"]}},
            actions=[],
            is_advanced=True,
        )
        rule_2 = FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"!": {"var": "text3"}},
            actions=[],
            is_advanced=True,
        )
        rule_3 = FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [{"var": "text2"}, {"var": "text1"}]},
            actions=[],
            is_advanced=True,
        )
        rule_4 = FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger={"==": [{"var": "text2"}, {"var": "text3"}]},
            actions=[],
            is_advanced=True,
        )

        self.expected_order = [
            rule_1,
            rule_3,
            rule_4,
            rule_2,
        ]

    def test_ordering_set_correctly(self):
        Form = self.apps.get_model("forms", "Form")

        form1_rules = Form.objects.get(slug="form").formlogic_set.all()

        self.assertQuerysetEqual(
            form1_rules.values_list("id", flat=True),
            [form.id for form in self.expected_order],
            transform=lambda x: x,
        )


@skip("Code is moved to squashed migration, these tests are now broken.")
class ConvertLogicActionValueToVariableTests(TestMigrations):
    app = "forms"
    migrate_from = "0040_set_number_of_formio_components"
    migrate_to = "0041_convert_logic_action_type_value_to_variable"

    def setUpBeforeMigration(self, apps):
        Form = apps.get_model("forms", "Form")
        FormLogic = apps.get_model("forms", "FormLogic")
        FormStep = apps.get_model("forms", "FormStep")
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormVariable = apps.get_model("forms", "FormVariable")

        fd = FormDefinition.objects.create(
            slug="fd",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "text1",
                    }
                ]
            },
        )
        form = Form.objects.create(slug="form")
        FormStep.objects.create(form=form, form_definition=fd, order=0)
        FormVariable.objects.create_for_form(form)
        FormLogic.objects.create(
            form=form,
            order=0,
            json_logic_trigger=True,
            actions=[
                {
                    "component": "text1",
                    "formStep": "",
                    "action": {
                        "type": "value",
                        "property": {},
                        "value": "Updated value",
                    },
                }
            ],
            is_advanced=True,
        )

    def test_logic_check_calculates_new_value(self):
        Form = self.apps.get_model("forms", "Form")
        form = Form.objects.get()
        logic = form.formlogic_set.get()

        self.assertEqual(
            logic.actions[0],
            {
                "component": "",
                "variable": "text1",
                "formStep": "",
                "action": {
                    "type": "variable",
                    "property": {},
                    "value": "Updated value",
                },
            },
        )
