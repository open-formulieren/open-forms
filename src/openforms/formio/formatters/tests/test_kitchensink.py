from collections.abc import Iterable
from typing import Any

from django.utils.translation import gettext as _

from openforms.submissions.models import Submission
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionFileAttachmentFactory,
)

from ...service import format_value
from ...typing import Component
from ...utils import iter_components
from .mixins import BaseFormatterTestCase
from .utils import load_json

NON_PRINTABLE_COMPONENT_TYPES = ("content", "columns", "fieldset")


def filter_printable(components: Iterable[Component]) -> Iterable[Component]:
    return filter(lambda c: c["type"] not in NON_PRINTABLE_COMPONENT_TYPES, components)


def _get_printable_data(submission: Submission) -> list[tuple[str, Any]]:
    printable_data: list[tuple[str, Any]] = []
    merged_data = submission.data

    for component in filter_printable(submission.form.iter_components(recursive=True)):
        key = component["key"]
        value = format_value(component, merged_data.get(key), as_html=False)
        printable_data.append((component.get("label", key), value))

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
        data["mapPointEmpty"] = {}
        data["mapPointHidden"] = {}
        data["mapLineStringEmpty"] = {}
        data["mapLineStringHidden"] = {}
        data["mapPolygonEmpty"] = {}
        data["mapPolygonHidden"] = {}

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
        submission_step = submission.submissionstep_set.get()  # pyright: ignore[reportAttributeAccessIssue]

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

        text_values = dict(printable_data)

        for label, value in text_printed.items():
            with self.subTest(f"{label} -> '{value}'"):
                self.assertEqual(value, text_values[label])
