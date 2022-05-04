from django.utils.translation import gettext as _

from openforms.emails.templatetags.form_summary import display_value
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ...utils import iter_components
from ..printable import filter_printable
from ..service import format_value
from .mixins import BaseFormatterTestCase
from .utils import load_json


def _get_printable_data(submission):
    printable_data = []
    for key, (
        component,
        value,
    ) in submission.get_ordered_data_with_component_type().items():
        printable_data.append(
            (component["label"], format_value(component, value, as_html=False))
        )
    return printable_data


class KitchensinkFormatterTestCase(BaseFormatterTestCase):
    def test_kitchensink_formio(self):
        self.run_kitchensink_test("kitchensink_data", "kitchensink_printable_text")

    def test_kitchensink_formio_with_hidden(self):
        # when hidden fields are submitted with their defaults
        self.run_kitchensink_test(
            "kitchensink_data_with_hidden", "kitchensink_printable_text_with_hidden"
        )

    def run_kitchensink_test(self, name_data, name_printable):
        configuration = load_json("kitchensink_components.json")
        data = load_json(f"{name_data}.json")
        text_printed = load_json(f"{name_printable}.json")

        # for sanity
        self.assertFlatConfiguration(configuration)

        # upfix some bugs/issues:

        # empty map should send no coordinates
        # TODO update data fixture when #1346 is fixed
        data["mapEmpty"] = []
        data["mapHidden"] = []

        # translated string
        assert "Signature" in text_printed
        text_printed["Signature"] = _("signature added")

        expected_labels = set(
            c["label"] for c in filter_printable(iter_components(configuration))
        )
        expected_keys = set(
            c["key"] for c in filter_printable(iter_components(configuration))
        )

        expected_keys.remove("numberEmpty")
        expected_keys.remove("currencyEmpty")

        # self.assertEqual(set(text_printed.keys()), expected_labels)
        # self.assertEqual(set(data.keys()), expected_keys)

        submission = SubmissionFactory.from_components(
            configuration["components"], submitted_data=data, completed=True
        )
        submission_step = submission.submissionstep_set.get()

        # these must match the components
        self.assertComponentKeyExists(configuration, "file")
        SubmissionFileAttachmentFactory.create(
            form_key="file",
            file_name="blank.doc",
            original_name="blank.doc",
            submission_step=submission_step,
        )
        self.assertComponentKeyExists(configuration, "fileUploadMulti")
        SubmissionFileAttachmentFactory.create(
            form_key="fileUploadMulti",
            file_name="blank.doc",
            original_name="blank.doc",
            submission_step=submission_step,
        )
        SubmissionFileAttachmentFactory.create(
            form_key="fileUploadMulti",
            file_name="dummy.doc",
            original_name="dummy.doc",
            submission_step=submission_step,
        )

        printable_data = _get_printable_data(submission)

        # check if we have something for all components
        self.assertEqual(set(d[0] for d in printable_data), expected_labels)

        text_values = dict()
        for label, value in printable_data:
            text_values[label] = display_value({"rendering_text": True}, value)

        html_values = dict()
        for label, value in printable_data:
            html_values[label] = display_value({"rendering_text": False}, value)

        # check if text and html values are same
        self.assertEqual(text_values, html_values)

        for label, value in text_printed.items():
            with self.subTest(f"{label} -> '{value}'"):
                self.assertEqual(value, text_values[label])

    def test_appointments_formio(self):
        configuration = load_json("appointments_components.json")
        data = load_json("appointments_data.json")
        text_printed = load_json("appointments_printable_text.json")

        # for sanity
        self.assertFlatConfiguration(configuration)

        self.assertEqual(len(text_printed), len(data))

        submission = SubmissionFactory.from_components(
            configuration["components"], submitted_data=data, completed=True
        )

        printable_data = _get_printable_data(submission)

        text_values = dict()
        for label, value in printable_data:
            text_values[label] = display_value({"rendering_text": True}, value)

        html_values = dict()
        for label, value in printable_data:
            html_values[label] = display_value({"rendering_text": False}, value)

        # check if text and html values are same
        self.assertEqual(text_values, html_values)

        for label, value in text_printed.items():
            with self.subTest(f"{label} -> '{value}'"):
                self.assertEqual(value, text_values[label])
