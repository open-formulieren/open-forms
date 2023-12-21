from openforms.utils.tests.test_migrations import TestMigrations


class TestAddMoreCustomErrorMessagesTimeComponent(TestMigrations):
    app = "forms"
    migrate_from = "0091_auto_20230831_1152"
    migrate_to = "0092_more_time_custom_errors"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        Form = apps.get_model("forms", "Form")

        self.form_def = FormDefinition.objects.create(
            name="Time",
            slug="time",
            configuration={
                "components": [
                    {
                        "key": "timeWithCustomError",
                        "type": "time",
                        "label": "Tijd with custom error",
                        "maxTime": "13:00:00",
                        "minTime": "12:00:00",
                        "translatedErrors": {
                            "en": {"required": "", "invalid_time": "Tralala"},
                            "nl": {"required": "", "invalid_time": "Tralala"},
                        },
                    }
                ]
            },
        )
        form = Form.objects.create(name="Form time")

        FormStep.objects.create(form=form, form_definition=self.form_def, order=0)

    def test_the_custom_error_is_added(self):
        self.form_def.refresh_from_db()

        self.assertEqual(
            self.form_def.configuration["components"][0]["translatedErrors"],
            {
                "en": {
                    "required": "",
                    "invalid_time": "Tralala",
                    "minTime": "",
                    "maxTime": "",
                },
                "nl": {
                    "required": "",
                    "invalid_time": "Tralala",
                    "minTime": "",
                    "maxTime": "",
                },
            },
        )


class TestAddDateComponentSettings(TestMigrations):
    app = "forms"
    migrate_from = "0092_more_time_custom_errors"
    migrate_to = "0093_date_component_settings"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        Form = apps.get_model("forms", "Form")

        self.form_def = FormDefinition.objects.create(
            name="Date",
            slug="date",
            configuration={
                "components": [
                    {
                        "key": "dateComponent",
                        "type": "date",
                        "label": "Date component",
                        "customOptions": {},
                        "translatedErrors": {
                            "en": {"required": ""},
                            "nl": {"required": ""},
                        },
                    },
                    {
                        "key": "anotherDateComponent",
                        "type": "date",
                        "label": "Another Date component",
                        "translatedErrors": {
                            "en": {"required": ""},
                            "nl": {"required": ""},
                        },
                    },
                ]
            },
        )
        form = Form.objects.create(name="Form date")

        FormStep.objects.create(form=form, form_definition=self.form_def, order=0)

    def test_new_settings(self):
        self.form_def.refresh_from_db()

        self.assertEqual(
            self.form_def.configuration["components"][0]["translatedErrors"],
            {
                "en": {
                    "required": "",
                    "minDate": "",
                    "maxDate": "",
                },
                "nl": {
                    "required": "",
                    "minDate": "",
                    "maxDate": "",
                },
            },
        )

        self.assertTrue(
            self.form_def.configuration["components"][0]["customOptions"][
                "allowInvalidPreload"
            ]
        )
        self.assertTrue(
            self.form_def.configuration["components"][1]["customOptions"][
                "allowInvalidPreload"
            ]
        )


class TestChangeFamilyMembersComponent(TestMigrations):
    app = "forms"
    migrate_from = "0093_date_component_settings"
    migrate_to = "0094_update_config_family"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")
        FormStep = apps.get_model("forms", "FormStep")
        Form = apps.get_model("forms", "Form")

        self.form_def = FormDefinition.objects.create(
            name="Date",
            slug="date",
            configuration={
                "components": [
                    {
                        "key": "npFamilyMembers",
                        "type": "npFamilyMembers",
                        "label": "Family members",
                    },
                ]
            },
        )
        form = Form.objects.create(name="Form with family members")

        FormStep.objects.create(form=form, form_definition=self.form_def, order=0)

    def test_migration(self):
        self.form_def.refresh_from_db()

        self.assertFalse(
            self.form_def.configuration["components"][0]["includePartners"]
        )
        self.assertTrue(self.form_def.configuration["components"][0]["includeChildren"])


class TestTimeComponentValidatorMigration(TestMigrations):
    app = "forms"
    migrate_from = "0095_formstep_form_form_definition_unique_together"
    migrate_to = "0096_move_time_component_validators"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        FormDefinition.objects.create(
            name="Date",
            slug="date",
            configuration={
                "components": [
                    {
                        "key": "time1",
                        "type": "time",
                        "label": "Time 1",
                    },
                    {
                        "key": "time2",
                        "type": "time",
                        "label": "Time 2",
                        "minTime": "10:00",
                        "maxTime": "20:00",
                    },
                    {
                        "key": "time3",
                        "type": "time",
                        "label": "Time 3",
                        "minTime": None,
                        "validate": {
                            "required": True,
                        },
                    },
                    {
                        "key": "time4",
                        "type": "time",
                        "label": "Time 4",
                        "maxTime": "20:00",
                    },
                ]
            },
        )

    def test_migration(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")

        form_def = FormDefinition.objects.get()
        time1, time2, time3, time4 = form_def.configuration["components"]

        self.assertNotIn("minTime", time1)
        self.assertNotIn("maxTime", time1)
        self.assertNotIn("validate", time1)

        self.assertNotIn("minTime", time2)
        self.assertNotIn("maxTime", time2)
        self.assertIn("validate", time2)
        self.assertEqual(time2["validate"]["minTime"], "10:00")
        self.assertEqual(time2["validate"]["maxTime"], "20:00")

        self.assertNotIn("minTime", time3)
        self.assertNotIn("maxTime", time3)
        self.assertIn("validate", time3)
        self.assertIsNone(time3["validate"]["minTime"])
        self.assertNotIn("maxTime", time3["validate"])

        self.assertNotIn("minTime", time4)
        self.assertNotIn("maxTime", time4)
        self.assertIn("validate", time4)
        self.assertNotIn("minTime", time4["validate"])
        self.assertEqual(time4["validate"]["maxTime"], "20:00")


class TestPrefillUpdateDefaultValuesMigration(TestMigrations):
    app = "forms"
    migrate_from = "0097_formstep_is_applicable"
    migrate_to = "0098_update_default_value_components_prefill"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        FormDefinition.objects.create(
            name="Date",
            slug="date",
            configuration={
                "components": [
                    {
                        # No prefill:
                        "key": "textfield",
                        "type": "textfield",
                        "label": "Textfield 1",
                    },
                    {
                        # Prefill with values:
                        "key": "date",
                        "type": "date",
                        "label": "Date 1",
                        "prefill": {
                            "plugin": "my_plugin",
                            "attribute": "my_attr",
                            "identifierRole": "main",
                        },
                    },
                    {
                        # Prefill with OK default values:
                        "key": "datetime",
                        "type": "datetime",
                        "label": "Datetime 1",
                        "prefill": {
                            "plugin": "",
                            "attribute": "",
                            "identifierRole": "main",
                        },
                    },
                    {
                        # Prefill with not OK default values:
                        "key": "postcode",
                        "type": "postcode",
                        "label": "Postcode 1",
                        "prefill": {
                            "plugin": None,
                            "attribute": None,
                            "identifierRole": "main",
                        },
                    },
                    {
                        # Prefill without the keys:
                        "key": "bsn",
                        "type": "bsn",
                        "label": "BSN 1",
                        "prefill": {
                            "identifierRole": "main",
                        },
                    },
                    {
                        # Prefill as None:
                        "key": "bsn2",
                        "type": "bsn",
                        "label": "BSN 2",
                        "prefill": None,
                    },
                ]
            },
        )

    def test_migration(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")

        form_def = FormDefinition.objects.get()
        textfield, date, datetime, postcode, bsn1, bsn2 = form_def.configuration[
            "components"
        ]

        self.assertNotIn("prefill", textfield)

        self.assertEqual(
            date["prefill"],
            {
                "plugin": "my_plugin",
                "attribute": "my_attr",
                "identifierRole": "main",
            },
        )

        self.assertEqual(
            datetime["prefill"],
            {
                "plugin": "",
                "attribute": "",
                "identifierRole": "main",
            },
        )

        self.assertEqual(
            postcode["prefill"],
            {
                "plugin": "",
                "attribute": "",
                "identifierRole": "main",
            },
        )

        self.assertEqual(
            bsn1["prefill"],
            {
                "identifierRole": "main",
            },
        )

        self.assertIsNone(bsn2["prefill"])


class TestSetDataSrcMigration(TestMigrations):
    app = "forms"
    migrate_from = "0099_form_theme"
    migrate_to = "0100_ensure_datasrc_property"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        FormDefinition.objects.create(
            name="DataSrc",
            slug="datasrc",
            configuration={
                "components": [
                    # Select variants
                    {
                        # dataSrc already set
                        "key": "select1",
                        "type": "select",
                        "label": "Select 1",
                        "openForms": {
                            "dataSrc": "variable",
                            "itemsExpression": "foo",
                        },
                    },
                    {
                        # dataSrc not set
                        "key": "select2",
                        "type": "select",
                        "label": "Select 2",
                        "openForms": {},
                        "data": {"values": [{"value": "option1", "label": "Option 1"}]},
                    },
                    {
                        # dataSrc not set (bis)
                        "key": "select3",
                        "type": "select",
                        "label": "Select 3",
                        "data": {"values": [{"value": "option1", "label": "Option 1"}]},
                    },
                    {
                        # dataSrc already set (bis)
                        "key": "select4",
                        "type": "select",
                        "label": "Select 4",
                        "openForms": {
                            "dataSrc": "manual",
                        },
                        "data": {"values": [{"value": "option1", "label": "Option 1"}]},
                    },
                    # Radio variants
                    {
                        # dataSrc already set
                        "key": "radio1",
                        "type": "radio",
                        "label": "radio 1",
                        "openForms": {
                            "dataSrc": "variable",
                            "itemsExpression": "foo",
                        },
                    },
                    {
                        # dataSrc not set
                        "key": "radio2",
                        "type": "radio",
                        "label": "radio 2",
                        "openForms": {},
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                    {
                        # dataSrc not set (bis)
                        "key": "radio3",
                        "type": "radio",
                        "label": "radio 3",
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                    {
                        # dataSrc already set (bis)
                        "key": "radio4",
                        "type": "radio",
                        "label": "radio 4",
                        "openForms": {
                            "dataSrc": "manual",
                        },
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                    # Selectboxes variants
                    {
                        # dataSrc already set
                        "key": "selectboxes1",
                        "type": "selectboxes",
                        "label": "selectboxes 1",
                        "openForms": {
                            "dataSrc": "variable",
                            "itemsExpression": "foo",
                        },
                    },
                    {
                        # dataSrc not set
                        "key": "selectboxes2",
                        "type": "selectboxes",
                        "label": "selectboxes 2",
                        "openForms": {},
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                    {
                        # dataSrc not set (bis)
                        "key": "selectboxes3",
                        "type": "selectboxes",
                        "label": "selectboxes 3",
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                    {
                        # dataSrc already set (bis)
                        "key": "selectboxes4",
                        "type": "selectboxes",
                        "label": "selectboxes 4",
                        "openForms": {
                            "dataSrc": "manual",
                        },
                        "values": [{"value": "option1", "label": "Option 1"}],
                    },
                ]
            },
        )

    def test_migration(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")

        form_def = FormDefinition.objects.get()
        (
            select1,
            select2,
            select3,
            select4,
            radio1,
            radio2,
            radio3,
            radio4,
            selectboxes1,
            selectboxes2,
            selectboxes3,
            selectboxes4,
        ) = form_def.configuration["components"]

        with self.subTest("select"):
            self.assertEqual(select1["openForms"]["dataSrc"], "variable")
            self.assertEqual(select2["openForms"]["dataSrc"], "manual")
            self.assertEqual(select3["openForms"]["dataSrc"], "manual")
            self.assertEqual(select4["openForms"]["dataSrc"], "manual")

        with self.subTest("radio"):
            self.assertEqual(radio1["openForms"]["dataSrc"], "variable")
            self.assertEqual(radio2["openForms"]["dataSrc"], "manual")
            self.assertEqual(radio3["openForms"]["dataSrc"], "manual")
            self.assertEqual(radio4["openForms"]["dataSrc"], "manual")

        with self.subTest("selectboxes"):
            self.assertEqual(selectboxes1["openForms"]["dataSrc"], "variable")
            self.assertEqual(selectboxes2["openForms"]["dataSrc"], "manual")
            self.assertEqual(selectboxes3["openForms"]["dataSrc"], "manual")
            self.assertEqual(selectboxes4["openForms"]["dataSrc"], "manual")


class TestUpdateActionProperty(TestMigrations):
    app = "forms"
    migrate_from = "0100_ensure_datasrc_property"
    migrate_to = "0101_update_action_property"

    def setUpBeforeMigration(self, apps):
        FormLogic = apps.get_model("forms", "FormLogic")
        Form = apps.get_model("forms", "Form")

        form = Form.objects.create(name="Form time")
        FormLogic.objects.create(
            order=0,
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "component": "nicePostcode",
                    "action": {
                        "name": "Make not required",
                        "type": "property",
                        "property": {
                            "type": "object",
                            "value": "validate",
                        },
                        "state": {"required": True},
                    },
                }
            ],
        )
        FormLogic.objects.create(
            order=1,
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "component": "nicePostcode",
                    "action": {
                        "type": "property",
                        "property": {"type": "bool", "value": "hidden"},
                        "state": True,
                        "value": "",
                    },
                }
            ],
        )
        FormLogic.objects.create(
            order=2,
            form=form,
            json_logic_trigger=True,
            actions=[],
        )

    def test_migration(self):
        FormLogic = self.apps.get_model("forms", "FormLogic")

        self.assertEqual(
            FormLogic.objects.get(order=0).actions[0],
            {
                "component": "nicePostcode",
                "action": {
                    "name": "Make not required",
                    "type": "property",
                    "property": {
                        "type": "bool",
                        "value": "validate.required",
                    },
                    "state": True,
                },
            },
        )
        self.assertEqual(
            FormLogic.objects.get(order=1).actions[0],
            {
                "component": "nicePostcode",
                "action": {
                    "type": "property",
                    "property": {"type": "bool", "value": "hidden"},
                    "state": True,
                    "value": "",
                },
            },
        )

class TestFormioTranslationsMigration(TestMigrations):
    app = "forms"
    migrate_from = "0101_update_action_property"
    migrate_to = "0102_convert_formio_translations"

    def setUpBeforeMigration(self, apps):
        FormDefinition = apps.get_model("forms", "FormDefinition")

        FormDefinition.objects.create(
            name="Translations",
            slug="translations",
            configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "textfield",
                        "label": "Reused label",
                        "description": "Textfield description",
                        "tooltip": "",
                    },
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "Reused label",
                        "components": [
                            {
                                "type": "content",
                                "key": "content",
                                "html": "<p>Some content</p>",
                            },
                            {
                                "type": "radio",
                                "key": "radio",
                                "label": "Radio label",
                                "values": [
                                    {
                                        "value": "option-1",
                                        "label": "Option 1",
                                    },
                                ],
                            },
                            {
                                "type": "select",
                                "key": "select",
                                "label": "Reused label",
                                "data": {
                                    "values": [
                                        {
                                            "value": "option-1",
                                            "label": "Option 1",
                                        },
                                        {
                                            "value": "option-2",
                                            "label": "Option 2",
                                        },
                                    ],
                                },
                            },
                        ],
                    },
                ]
            },
            component_translations={
                "nl": {
                    "Reused label": "Herbruikt label",
                    "Textfield description": "Omschrijving van tekstveld",
                    "<p>Some content</p>": "<p>Inhoud</p>",
                    # "Radio label": "DELIBERATELY OMITTED",
                    "Option 1": "Optie 1",
                },
            },
        )

    def test_translations_moved_to_components(self):
        FormDefinition = self.apps.get_model("forms", "FormDefinition")
        fd = FormDefinition.objects.get()

        textfield, fieldset = fd.configuration["components"]
        content, radio, select = fieldset["components"]

        with self.subTest("textfield"):
            self.assertIn("openForms", textfield)
            self.assertIn("translations", textfield["openForms"])
            self.assertIn("nl", textfield["openForms"]["translations"])
            textfield_nl_translations = textfield["openForms"]["translations"]["nl"]
            self.assertEqual(
                textfield_nl_translations,
                {
                    "label": "Herbruikt label",
                    "description": "Omschrijving van tekstveld",
                },
            )

        with self.subTest("fieldset"):
            self.assertIn("openForms", fieldset)
            self.assertIn("translations", fieldset["openForms"])
            self.assertIn("nl", fieldset["openForms"]["translations"])
            fieldset_nl_translations = fieldset["openForms"]["translations"]["nl"]
            self.assertEqual(fieldset_nl_translations, {"label": "Herbruikt label"})

        with self.subTest("content"):
            self.assertIn("openForms", content)
            self.assertIn("translations", content["openForms"])
            self.assertIn("nl", content["openForms"]["translations"])
            content_nl_translations = content["openForms"]["translations"]["nl"]
            self.assertEqual(content_nl_translations, {"html": "<p>Inhoud</p>"})

        with self.subTest("radio"):
            self.assertNotIn("openForms", radio)

            radio_option_1 = radio["values"][0]
            self.assertIn("openForms", radio_option_1)
            self.assertIn("translations", radio_option_1["openForms"])
            self.assertIn("nl", radio_option_1["openForms"]["translations"])
            radio_option_1_nl_translations = radio_option_1["openForms"][
                "translations"
            ]["nl"]
            self.assertEqual(
                radio_option_1_nl_translations,
                {
                    "label": "Optie 1",
                },
            )

        with self.subTest("select"):
            self.assertIn("openForms", select)
            self.assertIn("translations", select["openForms"])
            self.assertIn("nl", select["openForms"]["translations"])
            select_nl_translations = select["openForms"]["translations"]["nl"]
            self.assertEqual(select_nl_translations, {"label": "Herbruikt label"})

            select_option_1, select_option_2 = select["data"]["values"]

            self.assertIn("openForms", select_option_1)
            self.assertIn("translations", select_option_1["openForms"])
            self.assertIn("nl", select_option_1["openForms"]["translations"])
            select_option_1_nl_translations = select_option_1["openForms"][
                "translations"
            ]["nl"]
            self.assertEqual(
                select_option_1_nl_translations,
                {
                    "label": "Optie 1",
                },
            )

            self.assertNotIn("openForms", select_option_2)
