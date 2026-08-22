from django.test import TestCase, override_settings, tag
from django.urls import reverse

from pyquery import PyQuery as pq
from rest_framework.test import APITestCase

from formio_types import Option, Radio, Select, Selectboxes
from openforms.accounts.tests.factories import SuperUserFactory
from openforms.forms.tests.factories import (
    FormDefinitionFactory,
    FormFactory,
    FormStepFactory,
)
from openforms.logging.models import TimelineLogProxy
from openforms.submissions.tests.factories import SubmissionFactory
from openforms.submissions.tests.mixins import SubmissionsMixin

from ...constants import DataSrcOptions
from ...datastructures import FormioConfig, FormioData
from ...dynamic_config import rewrite_formio_components
from ...typing import (
    Component,
    ContentComponent,
    EditGridComponent,
    RadioComponent,
    SelectBoxesComponent,
    SelectComponent,
)


@override_settings(LANGUAGE_CODE="en")
class TestDynamicConfigAddingOptions(TestCase):
    def test_manual_options_not_updated(self):
        components: list[RadioComponent | SelectBoxesComponent | SelectComponent] = [
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "A", "value": "a"},
                    {"label": "B", "value": "b"},
                ],
            },
            {
                "label": "Select",
                "key": "select",
                "data": {
                    "values": [
                        {"label": "A", "value": "a"},
                        {"label": "B", "value": "b"},
                    ],
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
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(config, submission, FormioData({"some": "data"}))

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [Option(value="a", label="A"), Option(value="b", label="B")]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

    def test_variable_options_repeating_group(self):
        components: list[
            RadioComponent | SelectBoxesComponent | SelectComponent | EditGridComponent
        ] = [
            {
                "label": "repeatingGroup",
                "key": "repeatingGroup",
                "type": "editgrid",
                "groupLabel": "Item",
                "components": [{"type": "textfield", "key": "name", "label": "name"}],
            },
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                        "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                    },
                    "dataSrc": DataSrcOptions.variable,
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"repeatingGroup": [{"name": "Test1"}, {"name": "Test2"}]}),
        )

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [
            Option(value="Test1", label="Test1"),
            Option(value="Test2", label="Test2"),
        ]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

    def test_variable_options_repeating_group_empty_data(self):
        components: list[
            RadioComponent | SelectBoxesComponent | SelectComponent | EditGridComponent
        ] = [
            {
                "label": "repeatingGroup",
                "key": "repeatingGroup",
                "type": "editgrid",
                "groupLabel": "Item",
                "components": [{"type": "textfield", "key": "name", "label": "name"}],
            },
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "", "value": ""},
                ],
                "dataSrc": DataSrcOptions.variable,
                "data": {
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                "dataSrc": DataSrcOptions.variable,
                "data": {
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                        "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                    },
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"repeatingGroup": []}),
        )

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [Option(value="", label="")]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

    def test_variable_options_multiple_component(self):
        components: list[
            RadioComponent | SelectBoxesComponent | SelectComponent | Component
        ] = [
            {
                "label": "textField",
                "key": "textField",
                "type": "textfield",
                "multiple": True,
                "defaultValue": [],
            },
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"textField": ["Test1", "Test2"]}),
        )

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [
            Option(value="Test1", label="Test1"),
            Option(value="Test2", label="Test2"),
        ]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

    def test_variable_options_multiple_empty_data(self):
        components: list[
            RadioComponent | SelectBoxesComponent | SelectComponent | Component
        ] = [
            {
                "label": "textField",
                "key": "textField",
                "type": "textfield",
                "multiple": True,
                "defaultValue": [],
            },
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "", "value": ""},
                ],
                "dataSrc": DataSrcOptions.variable,
                "data": {
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
            {
                "label": "Select",
                "key": "select",
                "data": {
                    "values": [
                        {"label": "", "value": ""},
                    ],
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
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
                "dataSrc": DataSrcOptions.variable,
                "data": {
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"textField": []}),
        )

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [Option(value="", label="")]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

    def test_variable_options_repeating_group_missing_map(self):
        components: list[
            RadioComponent | SelectBoxesComponent | SelectComponent | EditGridComponent
        ] = [
            {
                "label": "repeatingGroup",
                "key": "repeatingGroup",
                "type": "editgrid",
                "groupLabel": "Item",
                "components": [{"type": "textfield", "key": "name", "label": "name"}],
            },
            {
                "label": "Select Boxes",
                "key": "selectBoxes",
                "type": "selectboxes",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
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
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                        "var": "repeatingGroup"
                    },  # No map operation to transform dict into str
                    "dataSrc": DataSrcOptions.variable,
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"repeatingGroup": [{"name": "Test1"}, {"name": "Test2"}]}),
        )

        selectboxes, select, radio = (
            config["selectBoxes"],
            config["select"],
            config["radio"],
        )
        expected_options = [Option(value="", label="")]
        assert isinstance(selectboxes, Selectboxes)
        self.assertEqual(selectboxes.values, expected_options)
        assert isinstance(select, Select)
        self.assertEqual(select.data.values, expected_options)
        assert isinstance(radio, Radio)
        self.assertEqual(radio.values, expected_options)

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
        components: list[RadioComponent | Component] = [
            {
                "label": "textField",
                "key": "textField",
                "type": "textfield",
                "multiple": True,
                "defaultValue": [],
            },
            {
                "label": "Radio",
                "key": "radio",
                "type": "radio",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"textField": ['Some data <IMG src="/test" />']}),
        )

        radio = config["radio"]
        assert isinstance(radio, Radio)
        expected_options = [
            Option(
                value="Some data &lt;IMG src=&quot;/test&quot; /&gt;",
                label="Some data &lt;IMG src=&quot;/test&quot; /&gt;",
            )
        ]
        self.assertEqual(radio.values, expected_options)

    def test_wrong_type_variable(self):
        components: list[RadioComponent | Component] = [
            {
                "label": "textField",
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"textField": "Some test data!"}),
        )

        radio = config["radio"]
        assert isinstance(radio, Radio)
        expected_options = [Option(value="", label="")]
        self.assertEqual(radio.values, expected_options)

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
        components: list[RadioComponent | Component] = [
            {
                "label": "textField",
                "key": "textField",
                "type": "textfield",
                "multiple": True,
                "defaultValue": [],
            },
            {
                "label": "Radio",
                "key": "radio",
                "type": "radio",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {"var": "textField"},  # pyright: ignore[reportAssignmentType]
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData({"textField": ["duplicate", "duplicate", "duplicate"]}),
        )

        radio = config["radio"]
        assert isinstance(radio, Radio)
        expected_options = [Option(value="duplicate", label="duplicate")]
        self.assertEqual(radio.values, expected_options)

    def test_duplicate_options_with_repeating_group(self):
        components: list[RadioComponent | EditGridComponent] = [
            {
                "label": "repeatingGroup",
                "key": "repeatingGroup",
                "type": "editgrid",
                "groupLabel": "Item",
                "components": [{"type": "textfield", "key": "name", "label": "name"}],
            },
            {
                "label": "Radio",
                "key": "radio",
                "type": "radio",
                "values": [
                    {"label": "", "value": ""},
                ],
                "openForms": {
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                        "map": [{"var": "repeatingGroup"}, {"var": "name"}]
                    },
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData(
                {"repeatingGroup": [{"name": "duplicate"}, {"name": "duplicate"}]}
            ),
        )

        radio = config["radio"]
        assert isinstance(radio, Radio)
        expected_options = [Option(value="duplicate", label="duplicate")]
        self.assertEqual(radio.values, expected_options)

    def test_badly_formatted_items(self):
        component: RadioComponent = {
            "label": "Radio",
            "key": "radio",
            "type": "radio",
            "values": [
                {"label": "", "value": ""},
            ],
            "openForms": {
                "dataSrc": DataSrcOptions.variable,
                "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                    "map": [{"var": "externalData"}, {"var": "id"}]
                },
            },
        }
        config = FormioConfig(name="<test>", components=[component])

        submission = SubmissionFactory.create()

        rewrite_formio_components(
            config,
            submission,
            # Only the first object has the property "id"
            FormioData(
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
                }
            ),
        )

        radio = config["radio"]
        assert isinstance(radio, Radio)
        expected_options = [
            Option(value="111", label="111"),
            Option(value="key", label="label"),
        ]
        self.assertEqual(radio.values, expected_options)

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
        components: list[EditGridComponent | SelectBoxesComponent] = [
            {
                "label": "repeatingGroup",
                "key": "repeatingGroup",
                "type": "editgrid",
                "groupLabel": "Item",
                "components": [
                    {"type": "textfield", "key": "name", "label": "name"},
                    {"type": "textfield", "key": "bsn", "label": "bsn"},
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
                    "dataSrc": DataSrcOptions.variable,
                    "itemsExpression": {  # pyright: ignore[reportAssignmentType]
                        "map": [
                            {"var": "repeatingGroup"},
                            [{"var": "bsn"}, {"var": "name"}],
                        ]
                    },
                },
            },
        ]
        submission = SubmissionFactory.create()
        config = FormioConfig(name="<test>", components=components)

        rewrite_formio_components(
            config,
            submission,
            FormioData(
                {
                    "repeatingGroup": [
                        {"name": "Test1", "bsn": "123456789"},
                        {"name": "Test2", "bsn": "987654321"},
                    ]
                }
            ),
        )

        selectboxes = config["selectBoxes"]
        assert isinstance(selectboxes, Selectboxes)
        expected_options = [
            Option(value="123456789", label="Test1"),
            Option(value="987654321", label="Test2"),
        ]
        self.assertEqual(selectboxes.values, expected_options)


class TestDynamicConfigAddingOptionsForRequest(SubmissionsMixin, APITestCase):
    @tag("gh-2895")
    def test_overwrite_html_in_content_component(self):
        """Assert that inline style is converted to style tag and nonce is added to content component

        Sanity checks:
            - Malicious HTML is changed
            - HTML with style tag + correct nonce attribute is not changed
            - HTML without style tag or attribute is not changed
            - Empty HTML does not cause error and remains unchanged
        """
        components: list[ContentComponent] = [
            {
                "type": "content",
                "key": "content1",
                "label": "content1",
                "html": '<p><span style="color:#e64c4c;">Test nonce</span></p>',
            },
            {
                "type": "content",
                "key": "content2",
                "label": "content2",
                "html": """
                    <div>
                        <style nonce="my-malicious-and-bad-nonce"></style>
                        <script>alert('xss')</script>
                    </div>
                    """,
            },
            {
                "type": "content",
                "key": "content3",
                "label": "content3",
                "html": "<p><span>Test nonce</span></p>",
            },
            {
                "type": "content",
                "key": "content4",
                "label": "content4",
                "html": "",
            },
        ]
        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(
            configuration={"components": components}, login_required=False
        )
        step1 = FormStepFactory.create(form=form, form_definition=form_definition)
        submission = SubmissionFactory.create(form=form)

        self._add_submission_to_session(submission)
        endpoint = reverse(
            "api:submission-steps-detail",
            kwargs={
                "submission_uuid": submission.uuid,
                "step_uuid": step1.uuid,
            },
        )
        user = SuperUserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(endpoint, HTTP_X_CSP_NONCE="dGvsa==")
        formio_components = response.json()["configuration"]["components"]

        with self.subTest("HTML of content component with inline style"):
            component1 = next(
                (item for item in formio_components if item["key"] == "content1"), None
            )
            assert component1 is not None
            doc = pq(component1["html"])
            style = doc.find("style")
            id = doc.find("span").attr("id")

            self.assertIn("color:#e64c4c", style.html())
            self.assertIsNotNone(style.attr("nonce"))
            self.assertIn("nonce", id)

        with self.subTest("Malicious HTML with html_nonce != request_nonce"):
            component2 = next(
                (item for item in formio_components if item["key"] == "content2"), None
            )
            assert component2 is not None
            doc = pq(component2["html"])
            scripts = doc.find("script")

            self.assertEqual(scripts, [])

        with self.subTest("HTML of content component without style tag/attribute "):
            component3 = next(
                (item for item in formio_components if item["key"] == "content3"), None
            )
            assert component3 is not None
            self.assertEqual(component3["html"], "<p><span>Test nonce</span></p>\n")

        with self.subTest("Empty HTML"):
            component4 = next(
                (item for item in formio_components if item["key"] == "content4"), None
            )
            assert component4 is not None
            self.assertEqual(component4["html"], "")
