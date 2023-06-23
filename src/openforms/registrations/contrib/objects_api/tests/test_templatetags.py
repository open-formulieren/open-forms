from django.test import TransactionTestCase

from openforms.forms.tests.factories import FormFactory
from openforms.registrations.constants import RegistrationAttribute
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)
from openforms.template import openforms_backend, render_from_string


class JsonSummeryTests(TransactionTestCase):
    def test_render_json_summary(self):
        form = FormFactory.create()
        submission = SubmissionFactory.create(
            form=form, completed=True, form_url="http://maykinmedia.nl/myform/"
        )
        SubmissionStepFactory.create(
            form_step__form=form,
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
            submission=submission,
            data={
                "voornaam": "Foo",
                "achternaam": "Bar",
                "tussenvoegsel": "de",
            },
        )

        rendered = render_from_string(
            "{% json_summary %}",
            context={"_submission": submission},
            backend=openforms_backend,
            disable_autoescape=True,
        )

        expected = '{"json-summery-step": {"voornaam": "Foo", "achternaam": "Bar", "tussenvoegsel": "de"}}'

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
