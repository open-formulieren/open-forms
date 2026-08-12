from django.test import TestCase

from unittest_parametrize import ParametrizedTestCase, parametrize

from openforms.forms.tests.factories import FormDefinitionFactory, FormFactory

from ..script_checks import BinScriptCheck
from .utils import capture_output


class ReportConditionalEQpropertiesTests(ParametrizedTestCase, TestCase):
    script = BinScriptCheck("report_conditional_eq_properties")

    def test_no_conditional(self):
        FormFactory.create(generate_minimal_setup=True)

        with capture_output() as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No applicable form definitions found.",
                stdout.getvalue(),
            )

    @parametrize(
        "conditional",
        [
            {
                "show": False,
                "when": "textfield",
            },
            {
                "show": False,
            },
            {
                "when": "textfield",
            },
        ],
    )
    def test_report_components(self, conditional):
        configuration = {
            "components": [
                {
                    "type": "licenseplate",
                    "key": "licensePlate",
                    "label": "Licenseplate",
                    "validate": {
                        "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"
                    },
                    "conditional": conditional,
                }
            ],
        }

        form_definition = FormDefinitionFactory.build(configuration=configuration)
        form_definition.save()  # call the save method to set the _num_components field

        FormFactory.create(
            generate_minimal_setup=True,
            internal_name="conditional form",
            formstep__form_definition=form_definition,
        )

        with capture_output() as stdout:
            self.assertFalse(self.script.execute())
            self.assertIn(
                "Found possible form definition configurations with unwanted changes.",
                stdout.getvalue(),
            )

    @parametrize(
        "conditional",
        [
            {
                "show": True,
                "when": "textfield",
                "eq": "foobar",
            },
            {
                "show": False,
                "when": "textfield",
                "eq": "foobar",
            },
            {
                "show": False,
                "when": "",
                "eq": "foobar",
            },
            {
                "show": True,
                "when": "textfield",
                "eq": "",
            },
            {
                "show": None,
                "when": None,
                "eq": "",
            },
            {
                "eq": "",
            },
            {},
        ],
    )
    def test_no_report(self, conditional):
        configuration = {
            "components": [
                {
                    "type": "licenseplate",
                    "key": "licensePlate",
                    "label": "Licenseplate",
                    "validate": {
                        "pattern": r"^[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}\-[a-zA-Z0-9]{1,3}$"
                    },
                    "conditional": conditional,
                }
            ],
        }

        form_definition = FormDefinitionFactory.build(configuration=configuration)
        form_definition.save()  # call the save method to set the _num_components field

        FormFactory.create(
            generate_minimal_setup=True,
            internal_name="conditional form",
            formstep__form_definition=form_definition,
        )

        with capture_output() as stdout:
            self.assertTrue(self.script.execute())
            self.assertIn(
                "No applicable form definitions found.",
                stdout.getvalue(),
            )
