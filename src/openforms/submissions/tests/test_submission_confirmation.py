from rest_framework.test import APITestCase

from openforms.config.models import GlobalConfiguration
from openforms.forms.tests.factories import FormFactory, FormStepFactory
from openforms.submissions.tests.factories import (
    SubmissionFactory,
    SubmissionStepFactory,
)


class SubmissionConfirmationPageTests(APITestCase):
    def test_global_template_used(self):
        config = GlobalConfiguration.get_solo()
        config.submission_confirmation_template = "Dear {{ name|title }} {{ last_name|title }}, Thank you for submitting this form."
        config.save()

        form = FormFactory.create()
        step1 = FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"name": "john", "last_name": "doe"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"favourite_icecream": "hazelnut"},
        )

        confirmation_page_content = submission.render_confirmation_page()

        self.assertEqual(
            "Dear John Doe, Thank you for submitting this form.",
            confirmation_page_content,
        )

    def test_form_template_used(self):
        config = GlobalConfiguration.get_solo()
        config.submission_confirmation_template = "Dear {{ name|title }} {{ last_name|title }}, Thank you for submitting this form."
        config.save()

        form = FormFactory.create(
            submission_confirmation_template="Dear {{ name|title }} {{ last_name|title }}, {{ favourite_icecream }} is a great ice cream choice!"
        )
        step1 = FormStepFactory.create(form=form)
        step2 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"name": "john", "last_name": "doe"},
        )
        SubmissionStepFactory.create(
            submission=submission,
            form_step=step2,
            data={"favourite_icecream": "hazelnut"},
        )

        confirmation_page_content = submission.render_confirmation_page()

        self.assertEqual(
            "Dear John Doe, hazelnut is a great ice cream choice!",
            confirmation_page_content,
        )

    def test_template_tags(self):
        config = GlobalConfiguration.get_solo()
        config.submission_confirmation_template = "Dear {{ name|title }} {{ last_name|title }}, {% product_information %} Thank you for submitting this form."
        config.save()

        form = FormFactory.create(
            product__information="<p>some product information<p/>"
        )
        step1 = FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)

        SubmissionStepFactory.create(
            submission=submission,
            form_step=step1,
            data={"name": "john", "last_name": "doe"},
        )

        confirmation_page_content = submission.render_confirmation_page()

        self.assertIn(
            "<p>some product information<p/>",
            confirmation_page_content,
        )
