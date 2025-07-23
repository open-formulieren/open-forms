from django.test import TestCase

from openforms.forms.constants import LogicActionTypes
from openforms.forms.tests.factories import (
    FormLogicFactory,
    FormRegistrationBackendFactory,
)

from ...form_logic import evaluate_form_logic
from ..factories import SubmissionFactory


class RegistrationBackendModificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = SubmissionFactory.from_data(
            {
                "firstname": "Foo",
            },
        )
        FormRegistrationBackendFactory.create(
            form=cls.submission.form,
            backend="email",
            key="default",
            options={"to_emails": ["tome@example.com"]},
        )

    def test_single_backend_no_logic(self):
        evaluate_form_logic(self.submission, self.submission.steps[0])

        self.assertEqual(self.submission.registration_backend.key, "default")

    def test_setting_backend_with_logic(self):
        FormRegistrationBackendFactory.create(
            form=self.submission.form,
            backend="email",
            key="other",
            options={"to_emails": ["toyou@example.com"]},
        )

        FormLogicFactory.create(
            form=self.submission.form,
            json_logic_trigger={"==": [{"var": "firstname"}, "Foo"]},
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "other",
                    }
                }
            ],
        )

        evaluate_form_logic(self.submission, self.submission.steps[0])

        self.assertEqual(self.submission.registration_backend.key, "other")

    def test_not_setting_backend_with_logic(self):
        # TODO Which backend to pick from multiple, when no logic triggers?
        # Should this test fail?
        FormRegistrationBackendFactory.create(
            form=self.submission.form,
            backend="email",
            key="other",
            options={"to_emails": ["toyou@example.com"]},
        )

        FormLogicFactory.create(
            form=self.submission.form,
            json_logic_trigger=False,  # misconfigured logic
            actions=[
                {
                    "action": {
                        "type": LogicActionTypes.set_registration_backend,
                        "value": "other",
                    }
                }
            ],
        )

        evaluate_form_logic(self.submission, self.submission.steps[0])
        self.assertEqual(self.submission.registration_backend.key, "default")
