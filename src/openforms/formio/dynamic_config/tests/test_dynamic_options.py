from django.test import TestCase, override_settings

from openforms.formio.datastructures import FormioConfigurationWrapper
from openforms.formio.dynamic_config import rewrite_formio_components
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory


@override_settings(LANGUAGE_CODE="en")
class TestDynamicConfigAddingOptions(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        TimelineLogProxy.objects.all().delete()

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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
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

    def test_variable_options_repeating_group_missing_map(self):
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
                        "itemsExpression": {
                            "var": "repeatingGroup"
                        },  # No map operation to transform dict into str
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
                        "itemsExpression": {
                            "var": "repeatingGroup"
                        },  # No map operation to transform dict into str
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
                        "itemsExpression": {
                            "var": "repeatingGroup"
                        },  # No map operation to transform dict into str
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
            'The dynamic options obtained with expression {"var": "repeatingGroup"} contain non-primitive types.',
        )
        self.assertEqual(
            logs[1].extra_data["error"],
            'The dynamic options obtained with expression {"var": "repeatingGroup"} contain non-primitive types.',
        )
        self.assertEqual(
            logs[2].extra_data["error"],
            'The dynamic options obtained with expression {"var": "repeatingGroup"} contain non-primitive types.',
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

    def test_duplicate_options_with_multiple_field(self):
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
            {"textField": ["duplicate", "duplicate", "duplicate"]},
        )
        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "duplicate", "value": "duplicate"}],
        )

    def test_duplicate_options_with_repeating_group(self):
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [{"type": "textfield", "key": "name"}],
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
                        "itemsExpression": {
                            "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                        },
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {"repeatingGroup": [{"name": "duplicate"}, {"name": "duplicate"}]},
        )
        self.assertEqual(
            configuration["components"][1]["values"],
            [{"label": "duplicate", "value": "duplicate"}],
        )

    def test_badly_formatted_items(self):
        configuration = {
            "components": [
                {
                    "label": "Radio",
                    "key": "radio",
                    "type": "radio",
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "openForms": {
                        "dataSrc": "variable",
                        "itemsExpression": {
                            "map": [{"var": "externalData"}, {"var": "id"}]
                        },
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            # Only the first object has the property "id"
            {
                "externalData": [
                    {"id": "111"},
                    {"no-id": "222"},
                    "i'm not an object!",
                    123,
                    ["im", "an", "array"],
                    {"id": ["111", None]},
                    {"id": ["key", "label"]},
                ]
            },
        )
        self.assertEqual(
            configuration["components"][0]["values"],
            [{"label": "111", "value": "111"}, {"label": "label", "value": "key"}],
        )

        logs = TimelineLogProxy.objects.filter(
            object_id=submission.form.id,
            template="logging/events/form_configuration_error.txt",
        )

        self.assertEqual(len(logs), 1)
        self.assertEqual(
            logs[0].extra_data["error"],
            'Expression {"map": [{"var": "externalData"}, {"var": "id"}]} did not return a valid option for each item.',
        )

    def test_different_label_key_options(self):
        configuration = {
            "components": [
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "components": [
                        {"type": "textfield", "key": "name"},
                        {"type": "textfield", "key": "bsn"},
                    ],
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
                        "itemsExpression": {
                            "map": [
                                {"var": "repeatingGroup"},
                                [{"var": "bsn"}, {"var": "name"}],
                            ]
                        },
                    },
                },
            ]
        }

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            FormioConfigurationWrapper(configuration),
            submission,
            {
                "repeatingGroup": [
                    {"name": "Test1", "bsn": "123456789"},
                    {"name": "Test2", "bsn": "987654321"},
                ]
            },
        )

        self.assertEqual(
            configuration["components"][1]["values"],
            [
                {"label": "Test1", "value": "123456789"},
                {"label": "Test2", "value": "987654321"},
            ],
        )
