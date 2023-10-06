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
