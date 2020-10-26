import json
from time import sleep

from openforms.submissions.models import Submission

from .base import SeleniumStepTestBase, TEST_FORM_DEFINITION_CONFIG
from .factories import FormDefinitionFactory, FormFactory, FormStepFactory


class FormFlowTests(SeleniumStepTestBase):

    def setUp(self) -> None:
        super().setUp()
        self.form = FormFactory.create(name='TestForm1')
        self.definition_1 = FormDefinitionFactory.create(
            configuration=json.dumps(TEST_FORM_DEFINITION_CONFIG),
            login_required=False
        )
        self.definition_2 = FormDefinitionFactory.create(
            configuration=json.dumps(TEST_FORM_DEFINITION_CONFIG),
            login_required=False
        )
        self.definition_3 = FormDefinitionFactory.create(
            configuration=json.dumps(TEST_FORM_DEFINITION_CONFIG),
            login_required=False
        )
        self.step_1 = FormStepFactory.create(form=self.form, form_definition=self.definition_1)
        self.step_2 = FormStepFactory.create(form=self.form, form_definition=self.definition_2)
        self.step_3 = FormStepFactory.create(form=self.form, form_definition=self.definition_3)

    def test_submit_flow(self):
        self.selenium.get(self.live_server_url)
        self.selenium.find_element_by_xpath(
            '//a[text()="TestForm1"]'
        ).click()

        text = self.selenium.find_element_by_id('e0evwd-fieldyField')
        text.send_keys('some input')
        checkbox = self.selenium.find_element_by_id('ekyj0j-checky')
        checkbox.click()

        submit = self.selenium.find_element_by_name('next')
        submit.click()
        # Allow JS request to complete
        sleep(1)

        submission = Submission.objects.get()

        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.current_step, 1)
        submission_steps = submission.submissionstep_set.all()
        self.assertEqual(len(submission_steps), 1)
        self.assertEqual(submission_steps[0].form_step, self.step_1)
        self.assertEqual(submission_steps[0].data, {
            'fieldyField': 'some input',
            'checky': True
        })

        text = self.selenium.find_element_by_id('e0evwd-fieldyField')
        text.send_keys('some other input')
        checkbox = self.selenium.find_element_by_id('ekyj0j-checky')
        checkbox.click()

        submit = self.selenium.find_element_by_name('next')
        submit.click()
        # Allow JS request to complete
        sleep(1)

        submission = Submission.objects.get()

        self.assertEqual(submission.form, self.form)
        self.assertEqual(submission.current_step, 2)
        submission_steps = submission.submissionstep_set.all()
        self.assertEqual(len(submission_steps), 2)
        self.assertEqual(submission_steps[0].form_step, self.step_1)
        self.assertEqual(submission_steps[0].data, {
            'fieldyField': 'some input',
            'checky': True
        })
        self.assertEqual(submission_steps[1].form_step, self.step_2)
        self.assertEqual(submission_steps[1].data, {
            'fieldyField': 'some other input',
            'checky': True
        })
