from django.test import TestCase
from django.utils.translation import override as override_language

from privates.test import temp_private_root

from openforms.authentication.service import AuthAttribute
from openforms.submissions.tests.factories import SubmissionFactory


@temp_private_root()
class SubmissionFactoryTests(TestCase):
    def test_from_components__simple(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "foo",
                    "type": "textfield",
                    "label": "Foo Label",
                },
                {
                    "key": "bar",
                },
            ]
        )

        form = submission.form
        self.assertEqual(form.formstep_set.count(), 1)
        self.assertEqual(len(submission.steps), 1)

        actual = list(form.iter_components())
        expected = [
            {
                "key": "foo",
                "type": "textfield",
                "label": "Foo Label",
            },
            {
                "key": "bar",
                "type": "textfield",
                "label": "Bar",
            },
        ]
        self.assertEqual(actual, expected)

    def test_from_components__with_data(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "foo",
                    "type": "textfield",
                    "label": "Foo Label",
                },
                {
                    "key": "bar",
                },
                {
                    "key": "bazz",
                },
            ],
            submitted_data={
                "foo": 1,
                "bar": 2,
            },
        )

        actual = submission.data
        expected = {"foo": 1, "bar": 2}
        self.assertEqual(actual, expected)

    def test_from_components__kwargs(self):
        submission = SubmissionFactory.from_components(
            [
                {
                    "key": "foo",
                    "type": "textfield",
                    "label": "Foo Label",
                },
                {
                    "key": "bar",
                },
            ],
            form__name="MyForm",
            bsn="111222333",
        )

        self.assertEqual(submission.form.name, "MyForm")
        self.assertEqual(submission.auth_info.value, "111222333")

    def test_from_data__simple(self):
        submission = SubmissionFactory.from_data(
            {
                "foo": 1,
                "bar": 2,
            }
        )

        actual = submission.data
        expected = {
            "foo": 1,
            "bar": 2,
        }
        self.assertEqual(actual, expected)

    def test_from_data__kwargs(self):
        submission = SubmissionFactory.from_data(
            {
                "foo": 1,
                "bar": 2,
            },
            form__name="MyForm",
            kvk="111222333",
        )

        actual = submission.data
        expected = {
            "foo": 1,
            "bar": 2,
        }
        self.assertEqual(actual, expected)
        self.assertEqual(submission.form.name, "MyForm")
        self.assertEqual(submission.auth_info.attribute, AuthAttribute.kvk)
        self.assertEqual(submission.auth_info.value, "111222333")

    def test_passing_a_language_code_sets__form_translation_enabled(self):
        submission = SubmissionFactory.create(language_code="en")

        self.assertTrue(submission.form.translation_enabled)

    def test_language_code_is_set_to_active_language(self):
        with override_language("en"):
            submission = SubmissionFactory.create()

        self.assertEqual(submission.language_code, "en")
