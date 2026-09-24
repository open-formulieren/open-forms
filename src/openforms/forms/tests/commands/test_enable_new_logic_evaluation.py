from io import StringIO
from unittest.mock import patch

from django.core.management import CommandError, call_command
from django.test import TestCase

from ...models import Form, FormLogic
from ..factories import FormFactory, FormLogicFactory, FormStepFactory


class CommandTests(TestCase):
    def test_happy_dry_run(self):
        FormFactory.create(
            name="foo", generate_minimal_setup=True, new_logic_evaluation_enabled=False
        )
        FormFactory.create(name="bar", new_logic_evaluation_enabled=False)  # no steps
        FormFactory.create(
            name="baz", new_logic_evaluation_enabled=False, is_appointment=True
        )  # appointment

        stdout = StringIO()
        call_command("enable_new_logic_evaluation_for_all_forms", stdout=stdout)

        output = stdout.getvalue().strip()
        self.assertIn(
            "New logic evaluation has been enabled for the following forms:", output
        )
        for name in ("foo", "bar", "baz"):
            self.assertIn(name, output)
        for form in Form.objects.iterator():
            self.assertFalse(form.new_logic_evaluation_enabled)

    def test_happy(self):
        FormFactory.create(
            name="foo", generate_minimal_setup=True, new_logic_evaluation_enabled=False
        )
        FormFactory.create(name="bar", new_logic_evaluation_enabled=False)  # no steps
        FormFactory.create(
            name="baz", new_logic_evaluation_enabled=False, is_appointment=True
        )  # appointment

        stdout = StringIO()
        call_command(
            "enable_new_logic_evaluation_for_all_forms",
            "--no-dry-run",
            stdout=stdout,
        )

        output = stdout.getvalue().strip()
        self.assertIn(
            "New logic evaluation has been enabled for the following forms:", output
        )
        for name in ("foo", "bar", "baz"):
            self.assertIn(name, output)
        for form in Form.objects.iterator():
            self.assertTrue(form.new_logic_evaluation_enabled)

    def test_new_logic_evaluation_already_enabled(self):
        FormFactory.create(
            generate_minimal_setup=True, new_logic_evaluation_enabled=True
        )

        stdout = StringIO()
        call_command("enable_new_logic_evaluation_for_all_forms", stdout=stdout)

        output = stdout.getvalue().strip()
        self.assertEqual("All forms are already converted.", output)
        self.assertTrue(Form.objects.get().new_logic_evaluation_enabled)

    def test_with_cycle(self):
        form = FormFactory.create(name="Cool form", new_logic_evaluation_enabled=False)
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "foo"},
                    {"type": "textfield", "key": "bar"},
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "foo"}, "a"]},
            actions=[
                {
                    "action": {"type": "variable", "value": "b"},
                    "variable": "bar",
                },
            ],
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "bar"}, "b"]},
            actions=[
                {
                    "action": {"type": "variable", "value": "a"},
                    "variable": "foo",
                },
            ],
        )

        stdout = StringIO()
        with self.assertRaises(CommandError):
            call_command(
                "enable_new_logic_evaluation_for_all_forms",
                "--no-dry-run",
                stdout=stdout,
            )

        output = stdout.getvalue().strip()
        self.assertIn("The following forms still contain cycles", output)
        self.assertIn("Cool form", output)
        self.assertIn("bar, foo", output)
        self.assertFalse(Form.objects.get().new_logic_evaluation_enabled)

    def test_with_trigger_from_step(self):
        form = FormFactory.create(new_logic_evaluation_enabled=False)
        step = FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "textfield", "key": "foo"},
                    {"type": "textfield", "key": "bar"},
                ]
            },
        )

        FormLogicFactory.create(
            form=form,
            trigger_from_step=step,
            json_logic_trigger={"==": [{"var": "bar"}, "b"]},
            actions=[
                {
                    "action": {"type": "variable", "value": "a"},
                    "variable": "foo",
                },
            ],
        )

        stdout = StringIO()
        call_command(
            "enable_new_logic_evaluation_for_all_forms", "--no-dry-run", stdout=stdout
        )

        output = stdout.getvalue().strip()
        self.assertIn(
            "New logic evaluation has been enabled for the following forms:", output
        )
        self.assertTrue(Form.objects.get().new_logic_evaluation_enabled)
        self.assertIsNone(FormLogic.objects.get().trigger_from_step)

    def test_with_error_during_conversion(self):
        FormFactory.create(
            name="foo", generate_minimal_setup=True, new_logic_evaluation_enabled=False
        )

        stderr = StringIO()
        with (
            patch(
                "openforms.forms.models.Form.apply_logic_analysis",
                side_effect=ValueError,
            ),
            self.assertRaises(CommandError),
        ):
            call_command(
                "enable_new_logic_evaluation_for_all_forms",
                "--no-dry-run",
                stderr=stderr,
            )

        output = stderr.getvalue().strip()
        self.assertIn("Conversion of the following forms failed unexpectedly.", output)
        self.assertFalse(Form.objects.get().new_logic_evaluation_enabled)
