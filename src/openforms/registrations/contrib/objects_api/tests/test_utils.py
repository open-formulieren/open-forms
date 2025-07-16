import textwrap

from django.test import TestCase

from openforms.contrib.objects_api.rendering import render_to_json
from openforms.payments.constants import PaymentStatus
from openforms.payments.tests.factories import SubmissionPaymentFactory
from openforms.submissions.tests.factories import SubmissionFactory

from ..handlers.v1 import get_payment_context_data
from ..utils import recursively_escape_html_strings


class EscapeHTMLTests(TestCase):
    def test_given_dicts_values_are_escaped(self):
        dict_sample = {
            "test1": "normal value",
            "test2": """<>'"&""",
            "nested_dict": {
                "nested_dict1": {"nested_dict2": {"escape": """<>'"&"""}},
            },
            "nested_list": [
                "escape < me",
                {"leave > me": "escape & me"},
            ],
        }

        expected_dict = {
            "test1": "normal value",
            "test2": "&lt;&gt;&#x27;&quot;&amp;",
            "nested_dict": {
                "nested_dict1": {
                    "nested_dict2": {"escape": "&lt;&gt;&#x27;&quot;&amp;"}
                },
            },
            "nested_list": [
                "escape &lt; me",
                {"leave > me": "escape &amp; me"},
            ],
        }

        dict_result = recursively_escape_html_strings(dict_sample)

        self.assertEqual(expected_dict, dict_result)

    def test_given_lists_values_are_escaped(self):
        list_sample = [
            "test",
            """<>'"&""",
            "escape < me",
            ["escape < me"],
            [{"nested_dict": "escape < me"}],
        ]
        expected_list = [
            "test",
            "&lt;&gt;&#x27;&quot;&amp;",
            "escape &lt; me",
            ["escape &lt; me"],
            [{"nested_dict": "escape &lt; me"}],
        ]

        list_result = recursively_escape_html_strings(list_sample)

        self.assertEqual(expected_list, list_result)

    def test_different_input(self):
        samples = [5, 5.9, None, True]

        for sample in samples:
            with self.subTest(sample=sample):
                result = recursively_escape_html_strings(sample)

                self.assertIs(result, sample)

    def test_render_to_json_large_numbers(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__payment_backend="demo",
            form__product__price=1_000,
        )
        assert submission.price == 1_000

        context_data = get_payment_context_data(submission)

        self.assertEqual("1000.00", context_data["amount"])

    def test_render_to_json_many_decimal_places(self):
        submission = SubmissionFactory.create(
            completed=True,
            form__payment_backend="demo",
            form__product__price=3.1415926535,
        )
        assert submission.price == 3.1415926535

        context_data = get_payment_context_data(submission)

        self.assertEqual("3.14", context_data["amount"])

    def test_multiple_public_order_ids(self):
        submission = SubmissionFactory.create(
            with_public_registration_reference=True,
            form__payment_backend="demo",
            form__product__price=20,
        )
        payment1, payment2 = SubmissionPaymentFactory.create_batch(
            2, submission=submission, status=PaymentStatus.completed, amount=10
        )

        template = textwrap.dedent(
            """{"payment": {
            "completed": {% if payment.completed %}true{% else %}false{% endif %},
            "amount": {{ payment.amount }},
            "public_order_ids": [{% for order_id in payment.public_order_ids%}"{{ order_id|escapejs }}"{% if not forloop.last %},{% endif %}{% endfor %}]
        }}"""
        )

        rendered_json = render_to_json(
            template,
            context={"payment": get_payment_context_data(submission)},
        )
        assert isinstance(rendered_json, dict)

        self.assertEqual(
            rendered_json["payment"],
            {
                "public_order_ids": [
                    payment1.public_order_id,
                    payment2.public_order_id,
                ],
                "amount": 20,
                "completed": True,
            },
        )
