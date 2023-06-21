from unittest import TestCase

from django.template import Context, Template

from openforms.registrations.constants import RegistrationAttribute
from openforms.submissions.tests.factories import SubmissionFactory


class JsonSummeryTests(TestCase):
    def test_render_json_summary(self):
        submission = SubmissionFactory.from_components(
            [
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
            submitted_data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
            },
            language_code="en",
        )
        submission_step = submission.steps[0]
        step_slug = submission_step.form_step.form_definition.slug

        # Loads template tag and uses template tag
        template = Template(
            """{% load registrations.contrib.objects_api.json_summary %}{% json_summary %}"""
        )

        rendered = template.render(Context({"_submission": submission}))

        expected = (
            '{"%s": {"voornaam": "Foo", "achternaam": "Bar", "tussenvoegsel": "de"}}'
            % step_slug
        )

        self.assertEqual(rendered, expected)

    def test_render_json_summary_no_submission(self):
        # Loads template tag and uses template tag
        template = Template(
            """{% load registrations.contrib.objects_api.json_summary %}{% json_summary %}"""
        )

        rendered = template.render(Context())
        expected = "{}"

        self.assertEqual(rendered, expected)
