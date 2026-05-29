from io import StringIO
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.forms.tests.factories import (
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
)

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


class ReportLogicWithDeprecatedClearOnHideBehaviorTests(ParametrizedTestCase, TestCase):
    script = BinScriptCheck("report_logic_with_deprecated_clear_on_hide_behavior")

    def test_no_logic(self):
        FormFactory.create(generate_minimal_setup=True)

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No logic rules with a risk of behaving differently in Open Forms 4.0",
                stdout.getvalue(),
            )

    def test_with_empty_value_in_trigger_and_component_visibility_not_affected(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form_definition__configuration={
                "components": [{"type": "textfield", "key": "textfield"}]
            }
        )
        FormLogicFactory.create(
            form=form, json_logic_trigger={"var": {"==": [{"var": "textfield"}, ""]}}
        )

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No logic rules with a risk of behaving differently in Open Forms 4.0",
                stdout.getvalue(),
            )

    @parametrize(
        "logic_trigger",
        [
            {"==": [{"var": "textfield"}, ""]},
            {"===": [{"var": "textfield"}, None]},
            {"!=": [{"var": "textfield"}, None]},
            {"!==": [None, {"var": "textfield"}]},
            {"in": [{"var": "textfield"}, [""]]},
            {"in": [{"var": "textfield"}, ["foo", None]]},
            {
                "or": [
                    {"==": [{"var": "textfield"}, "foo"]},
                    {"==": [{"var": "textfield"}, ""]},
                ]
            },
        ],
    )
    def test_with_empty_value_in_trigger_and_component_visibility_affected_by_other_rule(
        self, logic_trigger
    ):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "components": [{"type": "textfield", "key": "textfield"}],
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "textfield",
                }
            ],
        )

        FormLogicFactory.create(form=form, json_logic_trigger=logic_trigger)

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertFalse(self.script.execute())
            self.assertIn(
                "Found logic rules with a risk of behaving differently in Open Forms "
                "4.0",
                stdout.getvalue(),
            )

    def test_no_empty_value_in_trigger_but_component_visibility_affected_by_other_rule(
        self,
    ):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "label": "fieldset",
                        "components": [
                            {
                                "type": "textfield",
                                "key": "textfield",
                                "label": "textfield",
                            }
                        ],
                    }
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger=True,
            actions=[
                {
                    "action": {
                        "type": "property",
                        "property": {"value": "hidden", "type": "bool"},
                        "state": True,
                    },
                    "component": "textfield",
                }
            ],
        )

        FormLogicFactory.create(
            form=form, json_logic_trigger={"==": [{"var": "textfield"}, "value"]}
        )

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No logic rules with a risk of behaving differently in Open Forms 4.0",
                stdout.getvalue(),
            )

    def test_with_empty_value_in_trigger_and_component_visibility_affected_by_conditional(
        self,
    ):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {"type": "checkbox", "key": "checkbox"},
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "conditional": {"when": "checkbox", "eq": True, "show": False},
                        "components": [{"type": "textfield", "key": "textfield"}],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form, json_logic_trigger={"==": [{"var": "textfield"}, ""]}
        )

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertFalse(self.script.execute())
            self.assertIn(
                "Found logic rules with a risk of behaving differently in Open Forms "
                "4.0",
                stdout.getvalue(),
            )

    def test_with_selectboxes_inside_editgrid(self):
        form = FormFactory.create()
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "editgrid",
                        "key": "editgrid",
                        "components": [
                            {
                                "type": "selectboxes",
                                "key": "selectboxes",
                                "values": [
                                    {"value": "a", "label": "A"},
                                    {"value": "b", "label": "B"},
                                ],
                            }
                        ],
                    },
                ]
            },
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"==": [{"var": "editgrid.0.selectboxes"}, False]},
        )

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No logic rules with a risk of behaving differently in Open Forms 4.0",
                stdout.getvalue(),
            )


class ReportInvalidFormLogicTests(TestCase):
    script = BinScriptCheck("report_invalid_form_logic")

    def test_no_problems(self):
        FormFactory.create(
            generate_minimal_setup=True, new_logic_evaluation_enabled=True
        )

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertTrue(self.script.execute())
            self.assertEqual("", stdout.getvalue())

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

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertFalse(self.script.execute())
            self.assertIn(
                "The following forms have have not been converted to the new logic "
                "evaluation.",
                stdout.getvalue(),
            )

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

        with patch("sys.stdout", new_callable=StringIO) as stdout:
            self.assertFalse(self.script.execute())
            self.assertIn(
                "The following forms have at least one logic rule with "
                "'trigger_from_step' set up, which is incompatible with the new logic "
                "evaluation.",
                stdout.getvalue(),
            )
