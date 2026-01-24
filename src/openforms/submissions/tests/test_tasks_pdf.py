import logging  # noqa TID251 -- used only for the log level
from unittest.mock import patch

from django.test import TestCase, override_settings, tag
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time
from privates.test import temp_private_root
from pyquery import PyQuery as pq

from openforms.logging.models import TimelineLogProxy
from openforms.config.models import GlobalConfiguration
from openforms.formio.constants import DataSrcOptions
from openforms.forms.tests.factories import FormLogicFactory

from ..models import SubmissionReport
from ..tasks.pdf import generate_submission_report
from .factories import SubmissionFactory, SubmissionReportFactory


@temp_private_root()
class SubmissionReportGenerationTests(TestCase):
    def test_submission_report_metadata(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__name="Test Form",
            form__slug="test-form",
            public_registration_reference="OF-TRALALA",
        )

        generate_submission_report.request.id = "some-id"
        generate_submission_report.run(submission.id)

        report = SubmissionReport.objects.get()
        self.assertEqual(
            _("%(title)s: Submission report (%(reference)s)")
            % {"title": "Test Form", "reference": "OF-TRALALA"},
            report.title,
        )
        self.assertEqual(submission, report.submission)
        self.assertTrue(report.content.name.endswith("test-form.pdf"))
        self.assertEqual("some-id", report.task_id)

    def test_multiple_value_report_rendering_issue_990(self):
        # regression test for Github #990
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "email",
                    "label": "email",
                    "type": "email",
                    "multiple": True,
                    "defaultValue": [],
                }
            ],
            # a multiple email field with no value entered sends a [None]
            {"email": [None]},
            completed=True,
            with_report=False,
        )

        generate_submission_report.request.id = "some-id"
        generate_submission_report.run(submission.id)

        report = SubmissionReport.objects.get()
        self.assertEqual(submission, report.submission)

    def test_pdf_renders_without_errors(self):
        """
        Assert that no error logs are emitted while rendering the PDF.

        This turned up as part of #949 - the PDF restyling which now uses "external"
        stylesheets and fonts for the layout. Using STATIC_URL=/static/ led to relative
        URLs without base URI and thus making it impossible to fetch the actual
        resources. This manifested in WeasyPrint as log records with log level ERROR.
        """
        report = SubmissionReportFactory.create(content="", submission__completed=True)

        with self.assertNoLogs(level=logging.ERROR):
            report.generate_submission_report_pdf()

    def test_hidden_output_not_included(self):
        """
        Assert that hidden components are not included in the report.

        #1451 requires that components hidden (statically or) dynamically by logic
        are not included. The report functionality is also extended to add more
        structure, and step titles/headers may not be included if there's nothing
        visible in the step.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input1",
                    "label": "Input 1",
                    "type": "textfield",
                    "hidden": True,
                }
            ],
            submitted_data={},
            completed=True,
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()
        step_title = submission.submissionstep_set.get().form_step.form_definition.name

        # hidden component itself may not be visible
        self.assertNotIn("Input 1", html)
        # step has no visible children -> also not visible
        self.assertNotIn(step_title, html)

    @tag("gh-5037")
    def test_date_object_is_converted_to_str_when_it_comes_from_logic_rule(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "date",
                    "key": "date1",
                },
                {
                    "type": "date",
                    "key": "updatedDate",
                },
            ],
            submitted_data={"date1": "2025-01-01"},
            completed=True,
            with_report=True,
        )

        FormLogicFactory.create(
            form=submission.form,
            json_logic_trigger={"==": [{"var": "date1"}, "2025-01-01"]},
            actions=[
                {
                    "variable": "updatedDate",
                    "action": {
                        "type": "variable",
                        "value": {"+": [{"var": "date1"}, {"duration": "P1M"}]},
                    },
                },
            ],
        )

        html = submission.report.generate_submission_report_pdf()

        self.assertIn("1 februari 2025", html)

    def test_visible_output_included(self):
        """
        Assert that hidden components are not included in the report.

        #1451 requires that components hidden (statically or) dynamically by logic
        are not included. The report functionality is also extended to add more
        structure, and step titles/headers may not be included if there's nothing
        visible in the step.
        """
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input1",
                    "label": "Input 1",
                    "type": "textfield",
                    "hidden": True,
                },
                {
                    "key": "input2",
                    "label": "Input 2",
                    "type": "textfield",
                    "hidden": False,
                },
                {
                    "type": "fieldset",
                    "label": "Group of fields",
                    "key": "group",
                    "components": [
                        {
                            "type": "currency",
                            "label": "Money money money",
                            "key": "money",
                            "hidden": False,
                        }
                    ],
                },
                {
                    "type": "content",
                    "html": "<p>Some markup</p>",
                    "key": "content",
                },
            ],
            submitted_data={"input1": None, "input2": "Second input", "money": 1234.56},
            completed=True,
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()
        step_title = submission.submissionstep_set.get().form_step.form_definition.name

        self.assertIn(step_title, html)
        self.assertNotIn("Input 1", html)
        self.assertIn("Input 2", html)
        self.assertIn("Second input", html)
        self.assertIn("Group of fields", html)
        self.assertIn("Money money money", html)
        self.assertIn("1.234,56", html)
        self.assertInHTML("<p>Some markup</p>", html)

    def test_confirmation_page_content_included_in_pdf(self):
        """Assert that confirmation page content is included in PDF if option is
        True"""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input",
                    "label": "Input",
                    "type": "textfield",
                },
            ],
            with_report=True,
        )
        submission.form.submission_confirmation_template = (
            "<p class='inclusive'>Include me!</p>"
        )

        # include confirmation page content
        submission.form.include_confirmation_page_content_in_pdf = True

        html = submission.report.generate_submission_report_pdf()

        doc = pq(html)
        inclusive_tag = doc(".inclusive")

        self.assertEqual(inclusive_tag.text(), "Include me!")

    def test_confirmation_page_content_not_included_for_cosign_submissions(self):
        self.addCleanup(GlobalConfiguration.clear_cache)
        config = GlobalConfiguration.get_solo()
        config.submission_confirmation_template = '<p class="inclusive">Include me</p>'
        config.cosign_submission_confirmation_template = (
            '<p class="inclusive">Include me</p>'
        )
        config.save()

        submission = SubmissionFactory.from_components(
            [{"key": "cosignerEmail", "type": "cosign", "label": "Cosign component"}],
            submitted_data={"cosignerEmail": "cosign@test.nl"},
            with_report=True,
            form__include_confirmation_page_content_in_pdf=True,
        )

        html = submission.report.generate_submission_report_pdf()

        doc = pq(html)
        inclusive_tag = doc(".inclusive")
        self.assertEqual(inclusive_tag.text(), "")
        self.assertIn("cosign@test.nl", html)

    def test_confirmation_page_content_not_included_in_pdf(self):
        """Assert that confirmation page content is not included in PDF if option is
        False"""

        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input",
                    "label": "Input",
                    "type": "textfield",
                },
            ],
            with_report=True,
        )
        submission.form.submission_confirmation_template = (
            "<p class='inclusive'>Include me!</p>"
        )

        # don't include confirmation_page_content
        submission.form.include_confirmation_page_content_in_pdf = False

        html = submission.report.generate_submission_report_pdf()

        doc = pq(html)
        inclusive_tag = doc(".inclusive")

        self.assertEqual(inclusive_tag.text(), "")

    @override_settings(LANGUAGE_CODE="en")
    def test_public_reference_included(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input",
                    "label": "Input",
                    "type": "textfield",
                },
            ],
            with_report=True,
            public_registration_reference="OF-12345",
        )

        html = submission.report.generate_submission_report_pdf()

        doc = pq(html)
        reference_node = doc(".metadata").children()[2]

        self.assertEqual(reference_node.text, "Your reference is: OF-12345")

    @freeze_time("2024-01-01")
    @override_settings(LANGUAGE_CODE="en")
    def test_timestamp_included(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "input",
                    "label": "Input",
                    "type": "textfield",
                },
            ],
            public_registration_reference="OF-12345",
        )

        html = submission.report.generate_submission_report_pdf()

        doc = pq(html)
        reference_node = doc(".metadata").children()[1]

        self.assertEqual(reference_node.text, "Report created on: Jan. 1, 2024, 1 a.m.")

    def test_textfield_component_with_multiple_is_rendered_as_html(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "textfield-single",
                    "label": "Textfield single",
                    "multiple": False,
                },
                {
                    "type": "textfield",
                    "key": "textfield-multiple",
                    "label": "Textfield multiple",
                    "multiple": True,
                    "defaultValue": [],
                },
            ],
            submitted_data={
                "textfield-single": "foo",
                "textfield-multiple": ["foo", "bar"],
            },
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        expected = format_html(
            """
            <div class="submission-step-row">
                <span id="components.0.textfield-single" class="submission-step-row__label">Textfield single</span>
                <div aria-labelledby="components.0.textfield-single" class="submission-step-row__value">
                    foo
                </div>
            </div>
            <div class="submission-step-row">
                <span id="components.1.textfield-multiple" class="submission-step-row__label">Textfield multiple</span>
                <div aria-labelledby="components.1.textfield-multiple" class="submission-step-row__value">
                    <ul><li>foo</li><li>bar</li></ul>
                </div>
            </div>
            """,
        )
        self.assertInHTML(expected, html, count=1)

    def test_select_component_with_multiple_is_rendered_as_html(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "select",
                    "key": "select-single",
                    "label": "Select single",
                    "multiple": False,
                    "openForms": {
                        "dataSrc": DataSrcOptions.manual,
                    },
                    "data": {
                        "values": [
                            {"label": "Single select Option 1", "value": "option1"},
                            {"label": "Single select Option 2", "value": "option2"},
                        ]
                    },
                },
                {
                    "type": "select",
                    "key": "select-multiple",
                    "label": "Select multiple",
                    "multiple": True,
                    "defaultValue": [],
                    "openForms": {
                        "dataSrc": DataSrcOptions.manual,
                    },
                    "data": {
                        "values": [
                            {
                                "label": "Multiple select Option 1",
                                "value": "option1",
                            },
                            {
                                "label": "Multiple select Option 2",
                                "value": "option2",
                            },
                            {
                                "label": "Multiple select Option 3",
                                "value": "option3",
                            },
                        ]
                    },
                },
            ],
            submitted_data={
                "select-single": "option1",
                "select-multiple": ["option1", "option3"],
            },
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        expected = format_html(
            """
            <div class="submission-step-row">
                <span id="components.0.select-single" class="submission-step-row__label">Select single</span>
                <div aria-labelledby="components.0.select-single" class="submission-step-row__value">
                    Single select Option 1
                </div>
            </div>
            <div class="submission-step-row">
                <span id="components.1.select-multiple" class="submission-step-row__label">Select multiple</span>
                <div aria-labelledby="components.1.select-multiple" class="submission-step-row__value">
                    <ul><li>Multiple select Option 1</li><li>Multiple select Option 3</li></ul>
                </div>
            </div>
            """,
        )
        self.assertInHTML(expected, html, count=1)

    def test_selectboxes_component_is_rendered_as_html(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "label": "Selectboxes",
                    "values": [
                        {
                            "value": "option1",
                            "label": "Selectbox Option 1",
                        },
                        {
                            "value": "option2",
                            "label": "Selectbox Option 2",
                        },
                        {
                            "value": "option3",
                            "label": "Selectbox Option 3",
                        },
                    ],
                },
            ],
            submitted_data={
                "selectboxes": {
                    "option1": True,
                    "option3": True,
                },
            },
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        expected = format_html(
            """
            <div class="submission-step-row">
                <span id="components.0.selectboxes" class="submission-step-row__label">
                    Selectboxes
                </span>
                <div aria-labelledby="components.0.selectboxes" class="submission-step-row__value">
                    <ul><li>Selectbox Option 1</li><li>Selectbox Option 3</li></ul>
                </div>
            </div>
            """,
        )
        self.assertInHTML(expected, html, count=1)

    def test_radio_component_is_rendered_as_plain_text(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "radio",
                    "key": "radio",
                    "label": "Radio",
                    "values": [
                        {
                            "value": "firstradiooption",
                            "label": "First radio option",
                        },
                        {
                            "value": "secondradiooption",
                            "label": "Second radio option",
                        },
                    ],
                },
            ],
            submitted_data={
                "radio": "secondradiooption",
            },
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        expected = format_html(
            """
            <div class="submission-step-row">
                <span id="components.0.radio" class="submission-step-row__label">Radio</span>
                <div aria-labelledby="components.0.radio" class="submission-step-row__value">
                    Second radio option
                </div>
            </div>
            """,
        )
        self.assertInHTML(expected, html, count=1)

    @override_settings(LANGUAGE_CODE="en")
    def test_components_with_no_content(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "type": "textfield",
                    "key": "textfield",
                    "label": "Textfield",
                },
                {
                    "type": "selectboxes",
                    "key": "selectboxes",
                    "label": "Selectboxes",
                    "values": [
                        {
                            "value": "option1",
                            "label": "Selectbox Option 1",
                        },
                        {
                            "value": "option2",
                            "label": "Selectbox Option 2",
                        },
                        {
                            "value": "option3",
                            "label": "Selectbox Option 3",
                        },
                    ],
                },
                {
                    "type": "radio",
                    "key": "radio",
                    "label": "Radio",
                    "values": [
                        {
                            "value": "firstradiooption",
                            "label": "First radio option",
                        },
                        {
                            "value": "secondradiooption",
                            "label": "Second radio option",
                        },
                    ],
                },
                {
                    "key": "fieldset",
                    "type": "fieldset",
                    "label": "Fieldset",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "textfield1",
                            "label": "Textfield 1",
                        },
                    ],
                },
                {
                    "key": "repeatingGroup",
                    "type": "editgrid",
                    "label": "Repeating Group",
                    "components": [
                        {
                            "type": "textfield",
                            "key": "textfield2",
                            "label": "Textfield 2",
                        },
                    ],
                },
            ],
            submitted_data={"repeatingGroup": [{"textfield2": None}]},
            with_report=True,
        )
        html = submission.report.generate_submission_report_pdf()

        expected = format_html(
            """
            <div class="submission-step-row">
                <span id="components.0.textfield" class="submission-step-row__label">Textfield</span>
                <div aria-labelledby="components.0.textfield" class="submission-step-row__value submission-step-row__value--empty">
                     No information provided
                </div>
            </div>

            <div class="submission-step-row">
                <span id="components.1.selectboxes" class="submission-step-row__label">Selectboxes</span>
                <div aria-labelledby="components.1.selectboxes" class="submission-step-row__value submission-step-row__value--empty">
                     No information provided
                </div>
            </div>

            <div class="submission-step-row">
                <span id="components.2.radio" class="submission-step-row__label">Radio</span>
                <div aria-labelledby="components.2.radio" class="submission-step-row__value submission-step-row__value--empty">
                     No information provided
                </div>
            </div>

            <div class="submission-step-row submission-step-row--fieldset">
                <span class="submission-step-row__fieldset-label">Fieldset</span>
            </div>
            <div class="submission-step-row">
                <span id="components.3.components.0.textfield1" class="submission-step-row__label">
                    Textfield 1
                </span>
                <div aria-labelledby="components.3.components.0.textfield1" class="submission-step-row__value submission-step-row__value--empty">
                    No information provided
                </div>
            </div>

            <div class="submission-step-row submission-step-row--editgrid">
                <span id="components.4.repeatingGroup" class="submission-step-row__label">
                    Repeating Group
                </span>
                <div aria-labelledby="components.4.repeatingGroup" class="submission-step-row__value submission-step-row__value--empty">
                </div>
            </div>
            <div class="submission-step-row submission-step-row--editgrid-group">
                <span id="components.4.components.repeatingGroup" class="submission-step-row__label">
                    Item 1
                </span>
                <div aria-labelledby="components.4.components.repeatingGroup" class="submission-step-row__value submission-step-row__value--empty">
                </div>
            </div>
            <div class="submission-step-row">
                <span id="components.4.components.0.textfield2" class="submission-step-row__label">
                    Textfield 2
                </span>
                <div aria-labelledby="components.4.components.0.textfield2" class="submission-step-row__value submission-step-row__value--empty">
                    No information provided
                </div>
            </div>
            """,
        )
        self.assertInHTML(expected, html, count=1)

    def test_pdf_generation_failure_is_logged(self):
        submission = SubmissionFactory.create(completed=True, with_report=False)
        generate_submission_report.request.id = "some-id"

        with (
            patch(
                "openforms.submissions.tasks.pdf.SubmissionReport.generate_submission_report_pdf",
                side_effect=OSError("storage full"),
            ),
            self.assertRaises(IOError),
        ):
            generate_submission_report.run(submission.id)

        logs = TimelineLogProxy.objects.for_object(submission).filter_event(
            "pdf_generation_failure"
        )
        self.assertEqual(logs.count(), 1)


@temp_private_root()
class SubmissionReportCoSignTests(TestCase):
    def test_cosign_data_included(self):
        report = SubmissionReportFactory.create(
            content="",
            submission__completed=True,
            submission__co_sign_data={
                "version": "v1",
                "plugin": "digid",
                "identifier": "123456782",
                "co_sign_auth_attribute": "bsn",
                "fields": {
                    "voornaam": "Tina",
                    "geslachtsnaam": "Shikari",
                },
                "representation": "T. Shikari",
            },
        )
        rendered: str = report.generate_submission_report_pdf()
        report.refresh_from_db()

        self.assertTrue(report.content.name.endswith(".pdf"))

        expected = format_html(
            """
            <div class="submission-step-row">
                <div class="submission-step-row__label">{key}</div>
                <div class="submission-step-row__value">{co_sign_display}</div>
            </div>
            """,
            key=_("Co-signed by"),
            co_sign_display=_(
                "{representation} ({auth_attribute}: {identifier})"
            ).format(
                representation="T. Shikari",
                auth_attribute=_("BSN"),
                identifier="123456782",
            ),
        )
        self.assertInHTML(expected, rendered, count=1)

    def test_incomplete_cosign_data_missing_representation(self):
        report = SubmissionReportFactory.create(
            content="",
            submission__completed=True,
            submission__co_sign_data={
                "version": "v1",
                "plugin": "digid",
                "identifier": "123456782",
                "co_sign_auth_attribute": "bsn",
                "fields": {
                    "voornaam": "Tina",
                    "geslachtsnaam": "Shikari",
                },
                "representation": "",
            },
        )

        rendered: str = report.generate_submission_report_pdf()
        report.refresh_from_db()

        identifier = format_html(
            """
            <div class="submission-step-row">
                <div class="submission-step-row__label">{key}</div>
                <div class="submission-step-row__value">{co_sign_display}</div>
            </div>
            """,
            key=_("Co-signed by"),
            co_sign_display=_(
                "{representation} ({auth_attribute}: {identifier})"
            ).format(
                representation="",
                auth_attribute=_("BSN"),
                identifier="123456782",
            ),
        )
        self.assertIn(identifier, rendered)

    def test_cosign_v2_data(self):
        report = SubmissionReportFactory.create(
            content="",
            submission__completed=True,
            submission__co_sign_data={
                "version": "v2",
                "plugin": "digid",
                "attribute": "bsn",
                "value": "123456782",
                "cosign_date": "2024-01-01T17:00:00Z",
            },
        )

        html: str = report.generate_submission_report_pdf()

        self.assertNotEqual(html, "")
