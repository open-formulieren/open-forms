import logging

from django.db.models import Max, Min
from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from openforms.core.backends import registry
from openforms.core.models import Form

from .serializers import SubmissionSerializer, SubmissionStepSerializer
from ..models import Submission, SubmissionStep

logger = logging.getLogger(__name__)


class FormSubmissionViewSet(viewsets.ViewSet):
    lookup_field = "uuid"
    # TODO: Handle auth correctly / remove this Auth
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def get_submission(request, form_uuid, create=True):
        """
        Looks for the submission in the session.
        If not found and create is set to True, then create a new one and add to the session.
        :param request: The Current request
        :param form_uuid: The uuid of the form passed in the URL request.
        :param create: If no submission is found in the DB, should we create one then.
        :return: A tuple of the Submission object found/created and a boolean indicating
        if a new Submission was created.
        """
        form = get_object_or_404(Form, uuid=form_uuid)
        submission_uuid = request.session.get(form.uuid, None)
        submission = None
        created = False
        try:
            submission = Submission.objects.get(uuid=submission_uuid)
        except Submission.DoesNotExist:
            if create:
                logger.info('Session Submission does not exist. Creating...')
                data = {
                    "form": form
                }
                bsn = request.session.get('bsn')
                submission = None
                if bsn:
                    data["bsn"] = bsn
                    submission = Submission.objects.filter(
                        completed_on__isnull=True,
                        **data
                    ).order_by('-created_on').first()
                if not submission:
                    submission = Submission.objects.create(**data)
                    created = True
                request.session[form.uuid] = str(submission.uuid)
        return submission, created

    @staticmethod
    def validate_data(request, last_step):
        """
        Validate request data for the 'submit' implementation.
        :param request: The current request object.
        :param last_step: The last step order value.
        :return: A tuple of the cleaned data (dict), and errors found (list).
        """
        errors = []

        data = request.data.get('data')
        next_step_index = request.data.get('next_step_index')
        if not data and not next_step_index:
            errors.append('Either `data` or `next_step_index` must be supplied.')

        if next_step_index:
            if next_step_index > last_step:
                errors.append('`next_step_index` not an existing form step.')

        return {
            'data': data,
            'next_step_index': next_step_index
        }, errors

    @staticmethod
    def serialized_response(request, submission, status_code):
        """
        Returns a response containing the serialized submission object with the status_code given.
        :param request: The current request object.
        :param submission: The current submission object.
        :param status_code: The status code of the response.
        """
        serializer = SubmissionSerializer(instance=submission, context={"request": request})
        return Response(data=serializer.data, status=status_code)

    @action(detail=True, methods=['post'])
    def start(self, request, uuid=None):
        """
        Performs the start/resuming of a session submission for a form.

        Responses:
        200 - Existing submission for the given form was found.
        201 - New submission was created for form in the session.

        :param request: The request object.
        :param uuid: The UUID of the form.
        """
        submission, created = self.get_submission(request, form_uuid=uuid)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return self.serialized_response(request, submission, status_code)

    @action(detail=True, methods=['post'])
    def submit(self, request, uuid=None):
        """
        Performs the submission of a single step data.

        Responses:
        201 - Submission was found and the form step data was submitted creating a SubmissionStep.
        400 - Request data was found to be invalid or submission has been completed already.
        428 - Submission session was not found/available anymore. /start/ must be initiated again.

        :param request: The request object.
        :param uuid: The UUID of the form.
        """
        # TODO: Rate limit/throttle this, since someone can just keep hitting this
        # with different sessions and fill up the DB.
        submission, _ = self.get_submission(request, form_uuid=uuid, create=False)

        if not submission:
            return Response(
                data={"reason": "No submission for form found in session."},
                status=status.HTTP_428_PRECONDITION_REQUIRED
            )
        first_step = submission.form.formstep_set.aggregate(Min("order"))["order__min"]
        last_step = submission.form.formstep_set.aggregate(Max("order"))["order__max"]

        if submission.completed_on:
            return Response(
                data={"reason": "Submission completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Validate data that is posted and saved at the current step.
        data, errors = self.validate_data(request, last_step)
        if not errors:
            current_step = submission.current_step
            if data['data']:
                submission_step = SubmissionStep.objects.create(
                    submission=submission,
                    form_step=submission.form.formstep_set.get(order=current_step),
                    data=data['data']
                )
                # Save step to registered backend.
                backend_func = registry.get(submission.form.backend)
                if backend_func:
                    result = backend_func(submission_step)
                    submission.backend_result = result

            if data["next_step_index"]:
                submission.current_step = data["next_step_index"]
            else:
                submission.current_step = current_step + 1
            if submission.current_step > last_step:
                submission.current_step = first_step
            submission.save()

            return self.serialized_response(request, submission, status.HTTP_201_CREATED)
        else:
            return Response(data={"reason": errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, uuid=None):
        """
        Performs the completion of a submission routine. The found submission will be checked
        if it contains a submission step for at least one of each form step.

        Responses:
        200 - Submission was found to be complete and marked with a completed_on date.
        400 - Submission did not have submission steps for each form step in the linked form.
        428 - Submission session was not found/available anymore. /start/ must be initiated again.

        :param request: The request object.
        :param uuid: The UUID of the form.
        """
        submission, _ = self.get_submission(request, form_uuid=uuid, create=False)

        if not submission:
            return Response(
                data={"reason": "No submission for form found in session."},
                status=status.HTTP_428_PRECONDITION_REQUIRED
            )

        form_steps = submission.form.formstep_set.values_list('pk', flat=True)
        submission_steps = submission.submissionstep_set.filter(
            form_step__in=form_steps
        ).values_list('form_step__pk', flat=True)

        # If all forms steps have been found in the submission steps, we are good.
        if not form_steps.difference(submission_steps):
            submission.completed_on = timezone.now()
            submission.save()
            return self.serialized_response(request, submission, status.HTTP_200_OK)
        else:
            return Response(
                data={"reason": "Not all steps have been submitted for the form."},
                status=status.HTTP_400_BAD_REQUEST
            )


class SubmissionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubmissionStepViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = "uuid"
    queryset = SubmissionStep.objects.all()
    serializer_class = SubmissionStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(submission__uuid=self.kwargs['submission_uuid'])
