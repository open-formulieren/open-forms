from django.test import TestCase, override_settings

from openforms.forms.tests.factories import FormFactory
from openforms.registrations.constants import RegistrationAttribute
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.template import openforms_backend, render_from_string


class JsonSummaryTests(TestCase):
    def test_render_json_summary(self):
        form = FormFactory.create()
        step = SubmissionStepFactory.create(
            submission__form=form,
            submission__form_url="https://example.com/some-form",
            submission__completed=True,
            form_step__form=form,
            form_step__form_definition__slug="formstep-slug",
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
            data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
            },
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": step.submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"formstep-slug": {"voornaam": "Foo", "achternaam": "Bar", "tussenvoegsel": "de"}}'

        self.assertEqual(rendered, expected)

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=False)
    def test_render_json_summary_doesnt_escape_html_when_disabled(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"key": "voornaam", "type": "textfield"}],
            submitted_data={
                "voornaam": '<script>alert();</script>""',
            },
            form_definition_kwargs={"slug": "formstep-slug"},
            completed=True,
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        # double quotes are escaped by json.dumps() and not by our html_escape_json function
        # that's why we expect the text not be escaped except for the double quotes
        expected = '{"formstep-slug": {"voornaam": "<script>alert();</script>\\"\\""}}'

        self.assertEqual(rendered, expected)

    @override_settings(ESCAPE_REGISTRATION_OUTPUT=True)
    def test_render_json_summary_escapes_html_when_enabled(self):
        submission = SubmissionFactory.from_components(
            components_list=[{"key": "voornaam", "type": "textfield"}],
            submitted_data={"voornaam": "<script>alert();</script>"},
            form_definition_kwargs={"slug": "formstep-slug"},
            completed=True,
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = (
            '{"formstep-slug": {"voornaam": "&lt;script&gt;alert();&lt;/script&gt;"}}'
        )

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


class AsGeoJsonTests(TestCase):
    def test_render_as_geo_json(self):
        rendered = render_from_string(
            "{% as_geo_json variables.0.value %}",
            context={"variables": [{"value": [1.0, 2.0]}]},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"type": "Point", "coordinates": [1.0, 2.0]}'

        self.assertEqual(rendered, expected)

    def test_render_as_geo_json_no_value(self):
        rendered = render_from_string(
            "{% as_geo_json variables.0.value %}",
            context={"variables": [{"value": ""}]},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = "{}"

        self.assertEqual(rendered, expected)
