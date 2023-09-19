from django.test import TransactionTestCase, override_settings

from openforms.forms.tests.factories import FormFactory
from openforms.registrations.constants import RegistrationAttribute
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.template import openforms_backend, render_from_string


class JsonSummeryTests(TransactionTestCase):
    def setUp(self):
        self.form = FormFactory.create()
        self.submission = SubmissionFactory.create(
            form=self.form, completed=True, form_url="http://maykinmedia.nl/myform/"
        )

    def test_render_json_summary(self):
        SubmissionStepFactory.create(
            form_step__form=self.form,
            form_step__form_definition__slug="json-summery-step",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "voornaam",
                        "type": "textfield",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    },
                    {
                        "key": "achternaam",
                        "type": "textfield",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_geslachtsnaam,
                        },
                    },
                    {
                        "key": "tussenvoegsel",
                        "type": "textfield",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_tussenvoegsel,
                        },
                    },
                ],
            },
            submission=self.submission,
            data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
            },
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": self.submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"json-summery-step": {"voornaam": "Foo", "achternaam": "Bar", "tussenvoegsel": "de"}}'

        self.assertEqual(rendered, expected)

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=False)
    def test_render_json_summary_doesnt_escape_html_when_disabled(self):
        SubmissionStepFactory.create(
            form_step__form=self.form,
            form_step__form_definition__slug="json-summery-step",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "voornaam",
                        "type": "textfield",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    }
                ],
            },
            submission=self.submission,
            data={
                "voornaam": "<script>alert();</script>",
            },
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": self.submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"json-summery-step": {"voornaam": "<script>alert();</script>"}}'

        self.assertEqual(rendered, expected)

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=True)
    def test_render_json_summary_escapes_html_when_enabled(self):
        SubmissionStepFactory.create(
            form_step__form=self.form,
            form_step__form_definition__slug="json-summery-step",
            form_step__form_definition__configuration={
                "display": "form",
                "components": [
                    {
                        "key": "voornaam",
                        "type": "textfield",
                        "registration": {
                            "attribute": RegistrationAttribute.initiator_voornamen,
                        },
                    }
                ],
            },
            submission=self.submission,
            data={
                "voornaam": "<script>alert();</script>",
            },
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": self.submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"json-summery-step": {"voornaam": "&lt;script&gt;alert();&lt;/script&gt;"}}'

        self.assertEqual(rendered, expected)

    def test_render_json_summary_no_submission(self):
        # Loads template tag and uses template tag

        rendered = render_from_string(
            "{% json_summary %}",
            context={},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        self.assertEqual(rendered, "{}")
