from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from ..base import BasePlugin, DecisionDefinition, DecisionDefinitionVersion
from ..management.commands.dmn_evaluate import input_variable
from ..registry import Registry
from ..types import DMNInputOutput, GenericInputOutput

register = Registry()


@register("plugin1")
class Plugin1(BasePlugin):
    @staticmethod
    def get_available_decision_definitions():
        return [DecisionDefinition(identifier="test-1", label="Test definition")]

    @staticmethod
    def evaluate(*args, **kwargs):
        pass

    @staticmethod
    def get_decision_definition_parameters(
        definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        return GenericInputOutput(inputs=[], outputs=[])


@register("plugin2")
class Plugin2(BasePlugin):
    @staticmethod
    def get_available_decision_definitions():
        return [
            DecisionDefinition(identifier="plugin2-1", label="Test definition"),
            DecisionDefinition(identifier="plugin2-2", label="Other definition"),
        ]

    @staticmethod
    def get_decision_definition_versions(definition_id: str):
        if definition_id == "plugin2-1":
            return []
        return [DecisionDefinitionVersion(id="v1", label="first")]

    @staticmethod
    def evaluate(*args, **kwargs):
        pass

    @staticmethod
    def get_decision_definition_parameters(
        definition_id: str, version: str = ""
    ) -> DMNInputOutput:
        pass


@patch("openforms.dmn.management.commands.dmn_list_definitions.register", new=register)
class ListDefinitionsCommandTests(TestCase):
    def test_list_only_definitions(self):
        stdout, stderr = StringIO(), StringIO()

        with self.subTest(engine="plugin1"):
            call_command(
                "dmn_list_definitions", engine="plugin1", stdout=stdout, stderr=stderr
            )

            stdout.seek(0)

            output = stdout.read()
            expected_output = """Found 1 definition(s).

ID      Label
------  ---------------
test-1  Test definition
"""
            self.assertEqual(output, expected_output)

        stdout.seek(0)
        with self.subTest(engine="plugin2"):
            call_command(
                "dmn_list_definitions", engine="plugin2", stdout=stdout, stderr=stderr
            )

            stdout.seek(0)

            output = stdout.read()
            expected_output = """Found 2 definition(s).

ID         Label
---------  ----------------
plugin2-1  Test definition
plugin2-2  Other definition
"""
            self.assertEqual(output, expected_output)

    def test_list_with_versions(self):
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "dmn_list_definitions",
            engine="plugin2",
            show_versions=True,
            stdout=stdout,
            stderr=stderr,
        )

        stdout.seek(0)
        output = stdout.read()

        expected_output = """Found 2 definition(s).

ID         Label             Version ID    Version label
---------  ----------------  ------------  ---------------
plugin2-1  Test definition
plugin2-2  Other definition
                             v1            first
"""
        self.assertEqual(output, expected_output)

    def test_show_versions_filter_by_id(self):
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "dmn_list_definitions",
            engine="plugin2",
            show_versions=True,
            definition_id="plugin2-2",
            stdout=stdout,
            stderr=stderr,
        )

        stdout.seek(0)
        output = stdout.read()

        expected_output = """Found 1 definition(s).

ID         Label             Version ID    Version label
---------  ----------------  ------------  ---------------
plugin2-2  Other definition
                             v1            first
"""
        self.assertEqual(output, expected_output)

    def test_filter_by_definition_id_invalid(self):
        stdout, stderr = StringIO(), StringIO()

        call_command(
            "dmn_list_definitions",
            engine="plugin2",
            show_versions=True,
            definition_id="plugin2-3",
            stdout=stdout,
            stderr=stderr,
        )

        stderr.seek(0)
        output = stderr.read()
        self.assertEqual(output, "No definition with this ID found!\n")


@patch("openforms.dmn.management.commands.dmn_evaluate.register", new=register)
@patch("openforms.dmn.management.commands.dmn_evaluate.evaluate_dmn")
class EvaluateCommandTests(TestCase):
    def test_evaluate_happy_flow(self, mock_evaluate):
        mock_evaluate.return_value = {"result": 42}

        stdout, stderr = StringIO(), StringIO()

        call_command(
            "dmn_evaluate",
            "some-def-id",
            "--engine=plugin1",
            "--vars",
            "foo::int::13",
            "bar::baz",
            stdout=stdout,
            stderr=stderr,
        )

        mock_evaluate.assert_called_once_with(
            "plugin1",
            "some-def-id",
            version="",
            input_values={
                "foo": 13,
                "bar": "baz",
            },
        )

    def test_no_output_vars(self, mock_evaluate):
        mock_evaluate.return_value = {}

        stdout, stderr = StringIO(), StringIO()

        call_command(
            "dmn_evaluate",
            "some-def-id",
            "--engine=plugin1",
            stdout=stdout,
            stderr=stderr,
        )

        mock_evaluate.assert_called_once_with(
            "plugin1",
            "some-def-id",
            version="",
            input_values={},
        )
        stdout.seek(0)
        self.assertIn("No output variables.", stdout.read())

    def test_parsing_input_vars(self, *mocks):
        invalid = [
            "foo",
            "foo::int::bar",
            "foo::bar::baz",
            "foo::str::baz::quux",
        ]

        for vardef in invalid:
            with self.subTest(var=vardef):
                with self.assertRaises(ValueError):
                    input_variable(vardef)

        valid = [
            ("foo::str::bar", ("foo", "bar")),
            ("foo::int::42", ("foo", 42)),
            ("float::float::3.2", ("float", 3.2)),
        ]

        for vardef, (name, value) in valid:
            with self.subTest(var=vardef, expected_name=name, expected_value=value):
                result = input_variable(vardef)

                self.assertEqual(result, (name, value))
