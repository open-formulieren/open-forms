import json
import os

from django.test import TestCase

from openforms.emails.templatetags.form_summary import display_value
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ...utils import iter_components

FILES_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "files",
)


def load_json(filename: str):
    with open(os.path.join(FILES_DIR, filename), "r") as infile:
        return json.load(infile)


class LegacyFormatterTestCase(TestCase):
    def assertComponentKeyExists(self, components, key):
        for component in iter_components(components):
            if component.get("key") == key:
                # pass
                return

        known = ", ".join(sorted(c.get("key") for c in iter_components(components)))
        self.fail(f"cannot find component '{key}' in {known}")

    def test_printable_data(self):
        configuration = load_json("kitchensink_components.json")
        data = load_json("kitchensink_data.json")
        text_printed = load_json("kitchensink_printable_legacy_text.json")

        # upfix some bugs/issues:

        # these should not be in .data
        del data["textAreaHidden"]
        del data["signatureHidden"]

        # check if we have something for every data element
        self.assertEqual(len(text_printed), len(data))

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

        printable_data = submission.get_printable_data()

        text_values = dict()
        for label, value in printable_data:
            text_values[label] = display_value({"rendering_text": True}, value)

        html_values = dict()
        for label, value in printable_data:
            html_values[label] = display_value({"rendering_text": False}, value)

        # check if text and html values are same
        self.assertEqual(text_values, html_values)

        for label, value in text_printed.items():
            with self.subTest(f"text: {label}: {value}"):
                self.assertEqual(text_values[label], value)
