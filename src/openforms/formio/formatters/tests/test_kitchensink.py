from unittest.mock import patch

from django.utils.translation import gettext as _

from openforms.config.models import GlobalConfiguration
from openforms.emails.templatetags.form_summary import display_value
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ...utils import iter_components
from ..printable import filter_printable
from .mixins import BaseFormatterTestCase, load_json


class KitchensinkFormatterTestCase(BaseFormatterTestCase):
    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_legacy(self, mock_get_solo):
        self.run_kitchensink_test(
            mock_get_solo, False, "kitchensink_data", "kitchensink_printable_text"
        )

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_formio(self, mock_get_solo):
        self.run_kitchensink_test(
            mock_get_solo, True, "kitchensink_data", "kitchensink_printable_text"
        )

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_legacy_with_hidden(self, mock_get_solo):
        # when hidden fields are submitted with their defaults
        self.run_kitchensink_test(
            mock_get_solo,
            False,
            "kitchensink_data_with_hidden",
            "kitchensink_printable_text_with_hidden",
        )

    @patch("openforms.plugins.registry.GlobalConfiguration.get_solo")
    def test_kitchensink_formio_with_hidden(self, mock_get_solo):
        # when hidden fields are submitted with their defaults
        self.run_kitchensink_test(
            mock_get_solo,
            True,
            "kitchensink_data_with_hidden",
            "kitchensink_printable_text_with_hidden",
        )

    def run_kitchensink_test(
        self, mock_get_solo, formio_enabled, name_data, name_printable
    ):
        mock_get_solo.return_value = GlobalConfiguration(
            enable_formio_formatters=formio_enabled
        )

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

        # self.assertEqual(set(text_printed.keys()), set(expected_labels))
        # self.assertEqual(set(data.keys()), set(expected_keys))

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

        # check if we have something for all components
        self.assertEqual(set(d[0] for d in printable_data), set(expected_labels))

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
