from unittest.mock import patch

from django.test import SimpleTestCase

from ..jq_wrappers import (
    _MAX_EXPRESSION_BYTES,
    _MAX_INPUT_BYTES,
    JQExecutionError,
    JQInvalidExpressionError,
    run_jq,
    validate_jq,
)


class JQWrappersTestCase(SimpleTestCase):
    def test_validate_jq_success(self):
        validate_jq(".foo")

    def test_validate_jq_invalid_expression(self):
        with self.assertRaises(JQInvalidExpressionError):
            validate_jq(".foo |")

    @patch("openforms.utils.jq_wrappers.subprocess.run")
    def test_validate_jq_raises_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["/usr/bin/jq", "-c", ".foo"],
            timeout=2,
        )

        with self.assertRaisesMessage(
            JQExecutionError,
            "jq expression validation timed out",
        ):
            validate_jq(".foo")

    def test_validate_jq_max_expression_bytes(self):
        expression = "a" * (_MAX_EXPRESSION_BYTES + 1)

        with self.assertRaisesMessage(
            JQInvalidExpressionError,
            "jq expression is too large",
        ):
            validate_jq(expression)

    def test_run_jq_success(self):
        result = run_jq(
            ".foo",
            {"foo": "bar"},
        )

        self.assertEqual(result, "bar")

    def test_run_jq_cannot_access_environment_variables(self):
        result = run_jq(
            '{"const": env.SECRET_KEY}',
            {},
        )

        self.assertEqual(result, {"const": None})

    @patch("openforms.utils.jq_wrappers.subprocess.run")
    def test_run_jq_raises_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["/usr/bin/jq", "-c", ".foo"],
            timeout=2,
        )

        with self.assertRaisesMessage(
            JQExecutionError,
            "jq execution timed out",
        ):
            run_jq(".foo", {"foo": "bar"})

    def test_run_jq_max_expression_bytes(self):
        expression = "a" * (_MAX_EXPRESSION_BYTES + 1)

        with self.assertRaisesMessage(
            JQInvalidExpressionError,
            "jq expression is too large",
        ):
            run_jq(expression, {"foo": "bar"})

    def test_run_jq_max_input_bytes(self):
        # Make sure the serialized JSON exceeds the configured limit.
        data = {"value": "a" * _MAX_INPUT_BYTES}

        with self.assertRaisesMessage(
            JQExecutionError,
            "jq input is too large",
        ):
            run_jq(".", data)
