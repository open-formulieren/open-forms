from freezegun import freeze_time
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from openforms.core.tests.factories import FormFactory, FormStepFactory
from .factories import SubmissionFactory, SubmissionStepFactory

from ..models import Submission


class FormSubmissionAPITests(APITestCase):
    def setUp(self):
        # TODO: Replace with API-token
        User = get_user_model()
        user = User.objects.create_user(username="john", password="secret", email="john@example.com")

        self.request = HttpRequest()
        # TODO: Axes requires HttpRequest, should we have that in the API at all?
        self.client.login(request=self.request, username=user.username, password="secret")

    def test_auth_required_start(self):
        # TODO: Replace with not using an API-token
        self.client.logout()
        form = FormFactory.create()

        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_submit(self):
        # TODO: Replace with not using an API-token
        self.client.logout()
        form = FormFactory.create()

        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_complete(self):
        # TODO: Replace with not using an API-token
        self.client.logout()
        form = FormFactory.create()

        url = reverse('api:form-submissions-complete', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_1.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_start_existing_session(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)
        submission = SubmissionFactory.create(form=form)
        session = self.client.session
        session[str(form.uuid)] = str(submission.uuid)
        session.save()
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_1.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_start_with_bsn(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        bsn = '376034889'
        session = self.client.session
        session['bsn'] = bsn
        session.save()
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_1.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertEqual(submission.bsn, bsn)

        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_start_with_existing_submissions(self):
        form = FormFactory.create()
        form_other = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form_other)
        bsn = '376034889'
        session = self.client.session
        session['bsn'] = bsn
        session.save()
        SubmissionFactory.create(form=form, bsn=bsn, completed_on=timezone.now())
        SubmissionFactory.create(form=form, bsn=bsn, completed_on=timezone.now())
        SubmissionFactory.create(form=form, bsn=bsn)
        submission_last = SubmissionFactory.create(form=form, bsn=bsn)
        SubmissionFactory.create(form=form, bsn='376034887', completed_on=timezone.now())
        SubmissionFactory.create(form=form_other, bsn=bsn)
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # No new submission created.
        self.assertEqual(response.json()['uuid'], str(submission_last.uuid))
        self.assertEqual(Submission.objects.count(), 6)
        submission_last.refresh_from_db()
        self.assertEqual(submission_last.current_step, step_1.order)
        self.assertEqual(submission_last.form, form)
        self.assertFalse(submission_last.completed_on)
        self.assertEqual(submission_last.bsn, bsn)
        self.assertEqual(submission_last.submissionstep_set.count(), 0)

    def test_submit(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        step_2 = FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Submit first form data.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'data': {
                'more': 'something'
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

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

    def test_submit_no_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(response.json(), {
            'reason': 'No submission for form found in session.'
        })

    def test_submit_next_step_index(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)
        step_3 = FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Post to move to the third step.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'next_step_index': step_3.order
        })

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_3.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_submit_bad_next_step(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Post to move to the third step.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'next_step_index': 3
        })
        self.assertEqual(response.json(), {
            'reason': ['`next_step_index` not an existing form step.']
        })

        # Submission created on first post.
        submission = Submission.objects.get()
        # First step has been submitted so it should be at the second.
        self.assertEqual(submission.current_step, step_1.order)
        self.assertEqual(submission.form, form)
        self.assertFalse(submission.completed_on)
        self.assertFalse(submission.bsn)

        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_submit_already_completed(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        submission = Submission.objects.get()
        submission.completed_on = timezone.now()
        submission.save()

        # Try submit.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'data': {
                'more': 'something'
            }
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'reason': 'Submission completed.'})
        self.assertEqual(submission.submissionstep_set.count(), 0)

    def test_submit_nothing_supplied(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Try submit.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'reason': ['Either `data` or `next_step_index` must be supplied.']
        })

    @freeze_time("2020-01-14")
    def test_complete(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        step_2 = FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Submit 1st form.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'data': {
                'some': 'data'
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Submit 2nd form.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'data': {
                'some': 'thing'
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Complete submission
        url = reverse('api:form-submissions-complete', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        submission = Submission.objects.get()
        self.assertEqual(submission.completed_on, timezone.now())

        submission_steps = submission.submissionstep_set.all()
        self.assertEqual(len(submission_steps), 2)
        self.assertEqual(submission_steps[0].form_step, step_1)
        self.assertEqual(submission_steps[0].data, {'some': 'data'})
        self.assertEqual(submission_steps[1].form_step, step_2)
        self.assertEqual(submission_steps[1].data, {'some': 'thing'})

    def test_complete_no_submission(self):
        form = FormFactory.create()
        FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)
        # Try Complete submission
        url = reverse('api:form-submissions-complete', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertEqual(response.json(), {
            'reason': 'No submission for form found in session.'
        })

    def test_complete_incomplete(self):
        form = FormFactory.create()
        step_1 = FormStepFactory.create(form=form)
        FormStepFactory.create(form=form)

        # Start submission.
        url = reverse('api:form-submissions-start', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Submit 1st form.
        url = reverse('api:form-submissions-submit', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={
            'data': {
                'some': 'data'
            }
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Try Complete submission
        url = reverse('api:form-submissions-complete', args=(form.uuid,))
        response = self.client.post(url, format='json', secure=True, data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {
            'reason': 'Not all steps have been submitted for the form.'
        })

        submission = Submission.objects.get()
        self.assertFalse(submission.completed_on)

        submission_steps = submission.submissionstep_set.all()
        self.assertEqual(len(submission_steps), 1)
        self.assertEqual(submission_steps[0].form_step, step_1)
        self.assertEqual(submission_steps[0].data, {'some': 'data'})
