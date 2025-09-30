from uuid import UUID

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

        renderer = Renderer(submission, mode=RenderModes.summary, as_html=True)
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

    def test_children_component(self):
        component = {
            "type": "children",
            "key": "children",
            "label": "Children",
            "enableSelection": True,
        }
        submission = SubmissionFactory.create(
            form__name="public name",
            form__generate_minimal_setup=True,
            form__formstep__form_definition__configuration={"components": [component]},
        )
        step = SubmissionStepFactory.create(
            submission=submission,
            form_step=submission.form.formstep_set.get(),
            # TODO
            # Make sure this is updated (the data we get from the submission) when task
            # 2324 is completed
            # the data here is coming from the submission so that's why we have the extra
            # keys (used only for frontend operations)
            data={
                "children": [
                    {
                        "bsn": "999970409",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Pero",
                        "dateOfBirth": "2023-02-01",
                        "dateOfBirthPrecision": "date",
                        "selected": True,
                        "__addedManually": False,
                        "__id": UUID("cbf63e06-5ab8-44d1-bf18-6b786f3bb619"),
                    },
                    {
                        "bsn": "999970161",
                        "affixes": "van",
                        "initials": "P.",
                        "lastName": "Paassen",
                        "firstNames": "Peet",
                        "dateOfBirth": "2018-12-01",
                        "dateOfBirthPrecision": "date",
                        "selected": False,
                        "__addedManually": False,
                        "__id": UUID("2232657a-cb04-467d-9ded-6eb7a4819cc4"),
                    },
                ]
            },
        )

        renderer = Renderer(submission, mode=RenderModes.summary, as_html=True)
        component_node = ComponentNode.build_node(
            step_data=step.data, component=component, renderer=renderer
        )

        nodelist = list(component_node)

        # Nodes: Children, Child index x1, Child limited fields x1
        # (bsn, firstNames, date of birth)
        # There is one child since only the first one was selected
        self.assertEqual(len(nodelist), 5)

        self.assertEqual("Children: ", nodelist[0].render())

        self.assertEqual("Child 1: ", nodelist[1].render())
        self.assertEqual("BSN: 999970409", nodelist[2].render())
        self.assertEqual("Firstnames: Pero", nodelist[3].render())
        self.assertEqual("Date of birth: Feb. 1, 2023", nodelist[4].render())
