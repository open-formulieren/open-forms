from django.test import TestCase, override_settings

from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.dynamic_config import rewrite_formio_components
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory


@override_settings(LANGUAGE_CODE="en")
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
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                    },
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
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
                    "openForms": {
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
                        "dataSrc": "variable",
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
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
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
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
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
                        "itemsExpression": {"var": "repeatingGroup"},
                        "valueExpression": {"var": "name"},
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
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "textField"},
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                    },
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "textField"},
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
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "textField"},
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
                        "itemsExpression": {"var": "textField"},
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
                        "itemsExpression": {"var": "textField"},
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
                        "itemsExpression": {"var": "textField"},
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
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "repeatingGroup"},
                        # Missing valueExpression
                    },
                },
                {
                    "label": "Select",
                    "key": "select",
                    "data": {
                        "values": [
                            {"label": "", "value": ""},
                        ],
                    },
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "repeatingGroup"},
                        # Missing valueExpression
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
                    "openForms": {
                        "itemsExpression": {"var": "repeatingGroup"},
                        "dataSrc": "variable",
                        # Missing valueExpression
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

        logs = TimelineLogProxy.objects.filter(
            object_id=submission.form.id,
            template="logging/events/form_configuration_error.txt",
        )

        self.assertEqual(len(logs), 3)
        self.assertEqual(
            logs[0].extra_data["error"],
            "The choices for component Select Boxes (selectBoxes) are improperly configured. "
            "The JSON logic expression to retrieve the items is configured, but no expression for the items "
            "values was configured.",
        )
        self.assertEqual(
            logs[1].extra_data["error"],
            "The choices for component Select (select) are improperly configured. "
            "The JSON logic expression to retrieve the items is configured, but no expression for the items "
            "values was configured.",
        )
        self.assertEqual(
            logs[2].extra_data["error"],
            "The choices for component Radio (radio) are improperly configured. "
            "The JSON logic expression to retrieve the items is configured, but no expression for the items "
            "values was configured.",
        )

    def test_escaped_html(self):
        configuration = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "multiple": True,
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "textField"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"textField": ['Some data <IMG src="/test" />']},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [
                {
                    "label": "Some data &lt;IMG src=&quot;/test&quot; /&gt;",
                    "value": "Some data &lt;IMG src=&quot;/test&quot; /&gt;",
                }
            ],
        )

    def test_wrong_type_variable(self):
        configuration = {
            "components": [
                {
                    "key": "textField",
                    "type": "textfield",
                    "multiple": False,  # Not an array!
                },
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {"var": "textField"},
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"textField": "Some test data!"},
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "", "value": ""}],
        )

        logs = TimelineLogProxy.objects.filter(
            object_id=submission.form.id,
            template="logging/events/form_configuration_error.txt",
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].extra_data["error"],
            'Variable obtained with expression {"var": "textField"} for dynamic options is not an array.',
        )
