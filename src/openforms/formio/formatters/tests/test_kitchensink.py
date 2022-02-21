from unittest.mock import patch

from django.utils.translation import gettext as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.templatetags.form_summary import display_value
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from .mixins import BaseFormatterTestCase, load_json


class KitchensinkFormatterTestCase(BaseFormatterTestCase):
    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_legacy(self, mock_get_solo):
        self.run_kitchensink_test(mock_get_solo, False)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_formio(self, mock_get_solo):
        self.run_kitchensink_test(mock_get_solo, True)

    def run_kitchensink_test(self, mock_get_solo, formio_enabled):
        mock_get_solo.return_value = GlobalConfiguration(
            enable_formio_formatters=formio_enabled
        )

        configuration = load_json("kitchensink_components.json")
        data = load_json("kitchensink_data.json")
        text_printed = load_json("kitchensink_printable_text.json")

        # for sanity
        self.assertFlatConfiguration(configuration)

        # upfix some bugs/issues:

        # these should not be in .data
        # TODO remove from data fixture once #1354 is fixed
        del data["textAreaHidden"]
        del data["signatureHidden"]

        # empty map should send no coordinates
        # TODO update data fixture when #1346 is fixed
        data["mapEmpty"] = []

        # translated string
        assert "Signature" in text_printed
        text_printed["Signature"] = _("signature added")

        # check if we have something for every data element
        # TODO does this make sense? do we ALWAYS have a printable for every data?
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
            with self.subTest(f"{label} -> '{value}'"):
                self.assertEqual(value, text_values[label])

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_appointments_legacy(self, mock_get_solo):
        self.run_appointments_test(mock_get_solo, False)

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_appointments_formio(self, mock_get_solo):
        self.run_appointments_test(mock_get_solo, True)

    def run_appointments_test(self, mock_get_solo, formio_enabled):
        mock_get_solo.return_value = GlobalConfiguration(
            enable_formio_formatters=formio_enabled
        )

        configuration = load_json("appointments_components.json")
        data = load_json("appointments_data.json")
        text_printed = load_json("appointments_printable_text.json")

        # for sanity
        self.assertFlatConfiguration(configuration)

        self.assertEqual(len(text_printed), len(data))

        submission = SubmissionFactory.from_components(
            configuration["components"], submitted_data=data, completed=True
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
            with self.subTest(f"{label} -> '{value}'"):
                self.assertEqual(value, text_values[label])
