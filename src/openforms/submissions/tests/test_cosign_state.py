from django.test import TestCase

from ..cosigning import CosignState
from .factories import SubmissionFactory


class CosignStateTests(TestCase):

    def test_string_representation(self):
        submission = SubmissionFactory.build(public_registration_reference="OF-123")
        cosign = CosignState(submission=submission)

        str_repr = str(cosign)

        self.assertEqual(
            str_repr, "<CosignState submission=<Submission reference=OF-123>>"
        )

    def test_cosign_required_state(self):
        submissions = (
            (
                SubmissionFactory.create(cosigned=False),
                False,
            ),
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": False},
                        }
                    ],
                    cosigned=False,
                ),
                False,
            ),
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": True},
                        }
                    ],
                    cosigned=True,
                ),
                True,
            ),
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": False},
                        }
                    ],
                    submitted_data={"cosign": "cosigner@example.com"},
                    cosigned=False,
                ),
                True,
            ),
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": False},
                        }
                    ],
                    submitted_data={"cosign": "cosigner@example.com"},
                    cosigned=True,
                ),
                True,
            ),
        )

        for index, (submission, expected) in enumerate(submissions):
            with self.subTest(f"submission at index {index}"):
                cosign = CosignState(submission=submission)

                self.assertEqual(cosign.is_required, expected)

    def test_is_waiting(self):
        submissions = (
            # without cosign
            (
                SubmissionFactory.create(cosigned=False),
                False,
            ),
            # not signed yet
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": True},
                        }
                    ],
                    cosigned=False,
                ),
                True,
            ),
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": False},
                        }
                    ],
                    submitted_data={"cosign": "cosigner@example.com"},
                    cosigned=False,
                ),
                True,
            ),
            # signed
            (
                SubmissionFactory.from_components(
                    [
                        {
                            "type": "cosign",
                            "key": "cosign",
                            "hidden": False,
                            "validate": {"required": False},
                        }
                    ],
                    submitted_data={"cosign": "cosigner@example.com"},
                    cosigned=True,
                ),
                False,
            ),
        )

        for index, (submission, expected) in enumerate(submissions):
            with self.subTest(f"submission at index {index}"):
                cosign = CosignState(submission=submission)

                self.assertEqual(cosign.is_waiting, expected)
