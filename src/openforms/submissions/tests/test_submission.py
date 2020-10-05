from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.core.tests.factories import FormFactory, FormStepFactory

from ..models import Submission


class FormSubmissionAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(username="john", password="secret", email="john@example.com")

        self.request = HttpRequest()
        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        self.client.login(request=self.request, username=user.username, password="secret")

    def test_auth_required(self):
        # TODO: Replace with not using an API-token
        self.client.logout()
        form = FormFactory.create()

        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={'data': {'data'}})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_no_data(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={'step_index': 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'reason': ['No data supplied']
        })

    def test_post_invalid_step_index(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'step_index': 1,
                'data': 'something'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'reason': ['`step_index` not an existing form step.']
        })

    def test_post_invalid_next_step_index(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'next_step_index': 1,
                'data': 'something'
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'reason': ['`next_step_index` not an existing form step.']
        })

    def test_posts(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        step_2 = FormStepFactory.create(form=form)

        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'data': {
                    'more': 'something'
                }
            }
        )

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_2.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        submission_steps = submission.submissionstep_set.all()

        self.assertEqual(len(submission_steps), 1)
        self.assertEqual(submission_steps[0].form_step, step_1)
        self.assertEqual(submission_steps[0].data, {'more': 'something'})

        self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'data': {
                    'more': 'things'
                }
            }
        )

        # Same submission was used to continue saving.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_2.order + 1)
        self.assertEqual(submission.form, form)
        self.assertTrue(submission.completed_on)
        self.assertFalse(submission.bsn)

        submission_steps = submission.submissionstep_set.all()

        self.assertEqual(len(submission_steps), 2)
        self.assertEqual(submission_steps[0].form_step, step_1)
        self.assertEqual(submission_steps[0].data, {'more': 'something'})
        self.assertEqual(submission_steps[1].form_step, step_2)
        self.assertEqual(submission_steps[1].data, {'more': 'things'})

    def test_post_next_step_index(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        step_2 = FormStepFactory.create(form=form)
        step_3 = FormStepFactory.create(form=form)

        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'data': {
                    'more': 'something'
                },
                'next_step_index': step_3.order
            }
        )

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_3.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        submission_steps = submission.submissionstep_set.all()

        self.assertEqual(len(submission_steps), 1)
        self.assertEqual(submission_steps[0].form_step, step_1)
        self.assertEqual(submission_steps[0].data, {'more': 'something'})

    def test_post_step_index(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        step_2 = FormStepFactory.create(form=form)
        step_3 = FormStepFactory.create(form=form)

        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        self.client.post(
            url,
            format='json',
            secure=True,
            data={
                'data': {
                    'more': 'something'
                },
                'step_index': step_2.order
            }
        )

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_3.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        submission_steps = submission.submissionstep_set.all()

        self.assertEqual(len(submission_steps), 1)
        self.assertEqual(submission_steps[0].form_step, step_2)
        self.assertEqual(submission_steps[0].data, {'more': 'something'})
