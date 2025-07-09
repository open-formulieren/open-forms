from django.test import TestCase, override_settings

from openforms.submissions.rendering import Renderer, RenderModes
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)

from ..nodes import ComponentNode


@override_settings(LANGUAGE_CODE="en")
class CustomFormNodeTests(TestCase):
    def test_partners_component(self):
        component = {
            "type": "partners",
            "key": "partners",
            "label": "Partners",
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            data={
                "partners": [
                    {
                        "bsn": "999970136",
                        "firstNames": "Pia",
                        "initials": "P.",
                        "affixes": "",
                        "lastName": "Pauw",
                        "dateOfBirth": "1989-04-01",
                        "dateOfBirthPrecision": "date",
                    },
                    {
                        "bsn": "123456788",
                        "firstNames": "Vin",
                        "initials": "P.",
                        "affixes": "",
                        "lastName": "Sols",
                        "dateOfBirth": "1969-04-01",
                        "dateOfBirthPrecision": "date",
                    },
                ]
            },
        )

        renderer = Renderer(submission, mode=RenderModes.registration, as_html=True)
        component_node = ComponentNode.build_node(
            step_data=step.data, component=component, renderer=renderer
        )

        nodelist = list(component_node)

        # Nodes: Partners, Partner index x2, Partner limited fields x2
        # (bsn, initials, affixes, lastname, date of birth)
        self.assertEqual(len(nodelist), 13)

        self.assertEqual("Partners: ", nodelist[0].render())

        self.assertEqual("Partner 1: ", nodelist[1].render())
        self.assertEqual("BSN: 999970136", nodelist[2].render())
        self.assertEqual("Initials: P.", nodelist[3].render())
        self.assertEqual("Affixes: ", nodelist[4].render())
        self.assertEqual("Lastname: Pauw", nodelist[5].render())
        self.assertEqual("Date of birth: April 1, 1989", nodelist[6].render())

        self.assertEqual("Partner 2: ", nodelist[7].render())
        self.assertEqual("BSN: 123456788", nodelist[8].render())
        self.assertEqual("Initials: P.", nodelist[9].render())
        self.assertEqual("Affixes: ", nodelist[10].render())
        self.assertEqual("Lastname: Sols", nodelist[11].render())
        self.assertEqual("Date of birth: April 1, 1969", nodelist[12].render())
