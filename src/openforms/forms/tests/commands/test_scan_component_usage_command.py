from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from ..factories import FormDefinitionFactory


class CommandTests(TestCase):
    def test_command(self):
        FormDefinitionFactory.create(configuration={})
        FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"type": "textfield", "key": "text1"},
                    {"type": "textfield", "key": "text2"},
                    {"type": "select", "key": "select1"},
                ]
            }
        )
        FormDefinitionFactory.create(
            configuration={
                "components": [
                    {"type": "textfield", "key": "text1"},
                    {
                        "type": "fieldset",
                        "key": "fieldset",
                        "components": [
                            {"type": "textfield", "key": "text2"},
                            {"type": "select", "key": "select1"},
                        ],
                    },
                ]
            }
        )
        stdout = StringIO()

        call_command("scan_component_usage", "textfield", stdout=stdout)

        output = stdout.getvalue().strip()
        self.assertEqual(output, "Component type 'textfield' is used 4 time(s).")
