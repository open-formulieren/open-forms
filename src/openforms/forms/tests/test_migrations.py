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
