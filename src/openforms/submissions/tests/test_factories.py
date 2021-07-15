from django.test import TestCase

from privates.test import temp_private_root

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
                "type": "text",
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

        actual = submission.get_merged_data()
        expected = {
            "foo": 1,
            "bar": 2,
        }
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

        self.assertEqual(submission.bsn, "111222333")
        self.assertEqual(submission.form.name, "MyForm")

    def test_from_data__simple(self):
        submission = SubmissionFactory.from_data(
            {
                "foo": 1,
                "bar": 2,
            }
        )

        actual = submission.get_merged_data()
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
            bsn="111222333",
        )

        actual = submission.get_merged_data()
        expected = {
            "foo": 1,
            "bar": 2,
        }
        self.assertEqual(actual, expected)
        self.assertEqual(submission.form.name, "MyForm")
        self.assertEqual(submission.bsn, "111222333")
