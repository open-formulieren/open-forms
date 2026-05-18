from django.test import SimpleTestCase, TestCase

from openforms.forms.tests.factories import FormFactory, FormLogicFactory

from ..script_checks import BinScriptCheck


class DjangoScriptTests(SimpleTestCase):
    def test_check_script(self):
        scripts = (
            ("check_pass", True),
            ("check_fail", False),
            ("check_error", False),
        )
        for script, expected_outcome in scripts:
            with self.subTest(script=script):
                script_check = BinScriptCheck(script)

                self.assertEqual(script_check.execute(), expected_outcome)


class ReportInvalidFormLogicTests(TestCase):
    script = BinScriptCheck("report_invalid_form_logic")

    def test_no_problems(self):
        FormFactory.create(
            generate_minimal_setup=True, new_logic_evaluation_enabled=True
        )

        self.assertTrue(self.script.execute())

    def test_form_not_converted(self):
        form = FormFactory.create(
            generate_minimal_setup=True, new_logic_evaluation_enabled=False
        )
        FormLogicFactory.create(
            form=form,
            trigger_from_step=form.formstep_set.get(),
            json_logic_trigger=True,
            actions=[
                {
                    "form_step_uuid": str(form.formstep_set.get().uuid),
                    "action": {
                        "name": "Step is not applicable",
                        "type": "disable-next",
                    },
                }
            ],
        )

        self.assertFalse(self.script.execute())

    def test_new_logic_evaluation_enabled_with_trigger_from_step(self):
        form = FormFactory.create(
            generate_minimal_setup=True, new_logic_evaluation_enabled=True
        )
        FormLogicFactory.create(
            form=form,
            trigger_from_step=form.formstep_set.get(),
            json_logic_trigger=True,
            actions=[
                {
                    "form_step_uuid": str(form.formstep_set.get().uuid),
                    "action": {
                        "name": "Step is not applicable",
                        "type": "disable-next",
                    },
                }
            ],
        )

        self.assertFalse(self.script.execute())
