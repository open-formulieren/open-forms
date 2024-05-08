"""
Camunda plugin tests.

These tests assume the configuration from the include docker-compose::

    cd /path/to/root/of/repo
    cd docker
    docker-compose -f docker-compose.camunda.yml up -d

The default demo image contains a couple of decision definitions that we can use for
tests. Note that these tests are skipped if Camunda is not available.

You can also point to a different host/URL and/or credentials through environment
variables, see :mod:`openforms.contrib.camunda.tests.utils`.
"""

import logging
from functools import partial
from unittest.mock import patch

from django.test import TestCase

import requests_mock
from lxml import etree
from testfixtures import LogCapture

from openforms.contrib.camunda.tests.utils import get_camunda_client, require_camunda

from ....registry import register
from ....service import evaluate_dmn

_evaluate_dmn = partial(evaluate_dmn, "camunda7")
plugin = register["camunda7"]


@require_camunda
class CamundaDMNTests(TestCase):
    def setUp(self):
        super().setUp()

        # patch the get_client call to return our configured client
        self.camunda_client = get_camunda_client()
        patcher = patch(
            "openforms.dmn.contrib.camunda.plugin.get_client",
            return_value=self.camunda_client,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_list_process_definitions(self):
        definitions = plugin.get_available_decision_definitions()

        # default camunda demo image contains 2 decision definitions, there *may* be
        # additional images deployed for local testing/development
        self.assertGreaterEqual(len(definitions), 2)
        identifiers = {definition.identifier for definition in definitions}
        self.assertTrue(
            {"invoice-assign-approver", "invoiceClassification"}.issubset(identifiers)
        )

    def test_get_decision_definition_versions(self):
        versions = plugin.get_decision_definition_versions("invoiceClassification")

        # 2 versions deployed by default by Camunda, could be more due to local testing
        self.assertGreaterEqual(len(versions), 2)
        versions = {version.id for version in versions}
        self.assertTrue({"1", "2"}.issubset(versions))

    def test_retrieve_xml_looks_like_xml(self):
        xml = plugin.get_definition_xml("invoiceClassification", version="1")

        self.assertIsInstance(xml, str)
        self.assertNotEqual(xml, "")
        # check that it can be parsed with lxml
        tree = etree.fromstring(xml.encode("utf-8"))
        default_ns = tree.nsmap[None]
        self.assertEqual(tree.tag, f"{{{default_ns}}}definitions")

    def test_evaluate_without_pinned_version(self):
        result = _evaluate_dmn(
            "invoiceClassification",
            input_values={
                "invoiceCategory": "Travel Expenses",
                "amount": 30.0,
            },
        )

        self.assertEqual(result, {"invoiceClassification": "day-to-day expense"})

    def test_evaluate_with_pinned_version(self):
        result = _evaluate_dmn(
            "invoiceClassification",
            version="1",
            input_values={
                "invoiceCategory": "Misc",
                "amount": 752.2,
            },
        )

        self.assertEqual(result, {"invoiceClassification": "budget"})

    def test_evaluation_bad_input(self):
        with self.subTest("Camunda 500"):
            with LogCapture(
                level=logging.ERROR, names="openforms.dmn.contrib.camunda.plugin"
            ) as capture:
                result = _evaluate_dmn(
                    "invoiceClassification",
                    # invoiceCategory value is missing
                    input_values={"amount": 30.0},
                )

            self.assertEqual(result, {})

            self.assertEqual(len(capture.records), 2)
            self.assertEqual(
                capture.records[0].msg, "Error occurred while calling Camunda API"
            )
            self.assertRegex(capture.records[1].msg, r"^Camunda error information: .*")

        with self.subTest(
            "Mocked 500 without JSON response body"
        ), requests_mock.Mocker() as m:
            m.get(
                f"{self.camunda_client.root_url}decision-definition",
                json=[{"id": "mocked-id"}],
            )
            m.post(
                f"{self.camunda_client.root_url}decision-definition/mocked-id/evaluate",
                status_code=500,
                text="errored",
            )

            with LogCapture(
                level=logging.ERROR, names="openforms.dmn.contrib.camunda.plugin"
            ) as capture:
                result = _evaluate_dmn(
                    "invoiceClassification",
                    # invoiceCategory value is missing
                    input_values={"amount": 30.0},
                )

            self.assertEqual(result, {})

            self.assertEqual(len(capture.records), 2)
            self.assertEqual(
                capture.records[0].msg, "Error occurred while calling Camunda API"
            )
            self.assertEqual(
                capture.records[1].msg,
                "Could not decode JSON data in error response body",
            )

    def test_get_inputs_outputs(self):
        params = plugin.get_decision_definition_parameters(
            "invoiceClassification", version="1"
        )

        inputs = params.inputs
        outputs = params.outputs

        self.assertEqual(len(inputs), 2)
        self.assertEqual(inputs[0].label, "Invoice Amount")
        self.assertEqual(inputs[0].expression, "amount")
        self.assertEqual(inputs[1].label, "Invoice Category")
        self.assertEqual(inputs[1].expression, "invoiceCategory")

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].label, "Classification")
        self.assertEqual(outputs[0].name, "invoiceClassification")

    def test_get_inputs_outputs_table_with_dependency(self):
        # This decision ID depends on the invoiceClassification table
        params = plugin.get_decision_definition_parameters(
            "invoice-assign-approver", version="1"
        )

        inputs = params.inputs
        outputs = params.outputs

        self.assertEqual(len(inputs), 2)
        self.assertEqual(inputs[0].label, "Invoice Amount")
        self.assertEqual(inputs[0].expression, "amount")
        self.assertEqual(inputs[1].label, "Invoice Category")
        self.assertEqual(inputs[1].expression, "invoiceCategory")

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].label, "Approver Group")
        self.assertEqual(outputs[0].name, "result")
