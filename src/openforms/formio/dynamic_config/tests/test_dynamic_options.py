from django.test import TestCase

from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.dynamic_config import rewrite_formio_components
from openforms.submissions.tests.factories import SubmissionFactory


class TestDynamicConfigAddingOptions(TestCase):
    def test_manual_options_not_updated(self):
        configuration = {
            "components": [
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "A", "value": "a"},
                        {"label": "B", "value": "b"},
                    ],
                    "dataSrc": "manual",
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "A", "value": "a"},
                            {"label": "B", "value": "b"},
                        ],
                        "dataSrc": "manual",
                        "json": "",
                        "url": "",
                        "resource": "",
                        "custom": "",
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "A", "value": "a"},
                        {"label": "B", "value": "b"},
                    ],
                    "dataSrc": "manual",
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration), submission, {"some": "data"}
        )

        self.assertEqual(
            configuration["components"][0]["values"],
            [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
        )
        self.assertEqual(
            configuration["components"][1]["data"]["values"],
            [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
        )
        self.assertEqual(
            configuration["components"][2]["values"],
            [
                {"label": "A", "value": "a"},
                {"label": "B", "value": "b"},
            ],
        )

    def test_variable_options_repeating_group(self):
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [{"type": "textfield", "key": "name"}],
                },
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "dataSrc": "variable",
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"repeatingGroup": [{"name": "Test1"}, {"name": "Test2"}]},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )
        self.assertEqual(
            configuration["components"][2]["data"]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )
        self.assertEqual(
            configuration["components"][3]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )

    def test_variable_options_repeating_group_empty_data(self):
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [{"type": "textfield", "key": "name"}],
                },
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "dataSrc": "variable",
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        "valuePath": {"var": "name"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"repeatingGroup": []},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][2]["data"]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][3]["values"],
            [{"label": "", "value": ""}],
        )

    def test_variable_options_multiple_component(self):
        configuration = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "multiple": True,
                },
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "textField"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "dataSrc": "variable",
                        "itemsPath": {"var": "textField"},
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "textField"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"textField": ["Test1", "Test2"]},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )
        self.assertEqual(
            configuration["components"][2]["data"]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )
        self.assertEqual(
            configuration["components"][3]["values"],
            [
                {"label": "Test1", "value": "Test1"},
                {"label": "Test2", "value": "Test2"},
            ],
        )

    def test_variable_options_multiple_empty_data(self):
        configuration = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "multiple": True,
                },
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "textField"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "dataSrc": "variable",
                        "itemsPath": {"var": "textField"},
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "textField"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"textField": []},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][2]["data"]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][3]["values"],
            [{"label": "", "value": ""}],
        )

    def test_variable_options_repeating_group_missing_value_path(self):
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [{"type": "textfield", "key": "name"}],
                },
                {
                    "label": "Select Boxes",
                    "key": "selectBoxes",
                    "type": "selectboxes",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        # Missing valuePath
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                        "dataSrc": "variable",
                        "itemsPath": {"var": "repeatingGroup"},
                        # Missing valuePath
                    },
                    "type": "select",
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": "variable",
                    "data": {
                        "itemsPath": {"var": "repeatingGroup"},
                        # Missing valuePath
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"repeatingGroup": [{"name": "Test1"}, {"name": "Test2"}]},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][2]["data"]["values"],
            [{"label": "", "value": ""}],
        )
        self.assertEqual(
            configuration["components"][3]["values"],
            [{"label": "", "value": ""}],
        )
