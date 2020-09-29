import logging

from django.db.models import Max
from django.utils import timezone
from rest_framework import permissions, status, views
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from openforms.core.models import Form

from .serializers import SubmissionSerializer
from ..models import Submission, SubmissionStep

logger = logging.getLogger(__name__)


class SubmissionView(views.APIView):
    """
    Submission API endpoint that handles requests as follows:

    POST: With the Form UUID given, check if the session contains a submission for that form.
    IF not create a new submission for that form and store the UUID in the session. After that we
    continue to save the posted data to the submission
    """
    http_method_names = ('post',)
    # TODO: Authentication is simple at the moment, needs to be token based probably.
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = None

    def dispatch(self, request, *args, **kwargs):
        self.form = get_object_or_404(Form, uuid=kwargs['form_uuid'])
        return super().dispatch(request, *args, **kwargs)

    def create_new_submission(self, request):
        data = {
            "form": self.form
        }
        # TODO: Check if the user has existing incomplete submission under their BSN.
        bsn = request.session.get('bsn')
        if bsn:
            data["bsn"] = bsn
        submission = Submission.objects.create(**data)
        request.session[self.form.uuid] = str(submission.uuid)
        return submission

    @staticmethod
    def validate_data(request, last_step):
        errors = []

        data = request.data.get('data')
        step_index = request.data.get('step_index')
        next_step_index = request.data.get('next_step_index')
        if not data:
            errors.append('No data supplied')

        if step_index:
            if step_index > last_step:
                errors.append('`step_index` not an existing form step.')
        if next_step_index:
            if next_step_index > last_step:
                errors.append('`next_step_index` not an existing form step.')

        return {
            'data': data,
            'step_index': step_index,
            'next_step_index': next_step_index
        }, errors

    def post(self, request, *args, **kwargs):
        # TODO: Rate limit/throttle this, since someone can just keep hitting this
        # with different sessions and fill up the DB.
        submission_uuid = request.session.get(self.form.uuid)
        if not submission_uuid:
            submission = self.create_new_submission(request)
        else:
            try:
                submission = Submission.objects.get(uuid=submission_uuid)
            except Submission.DoesNotExist:
                logger.info('Session Submission does not exist. Recreating...')
                submission = self.create_new_submission(request)

        last_step = submission.form.formstep_set.aggregate(Max("order"))["order__max"]

        if submission.completed_on:
            return Response(
                data={"reason": "Submission completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # TODO: Validate data that is posted and saved at the current step.
        data, errors = self.validate_data(request, last_step)
        if not errors:
            current_step = data["step_index"] or submission.current_step
            SubmissionStep.objects.create(
                submission=submission,
                form_step=submission.form.formstep_set.get(order=current_step),
                data=data['data']
            )
            if data["next_step_index"]:
                submission.current_step = data["next_step_index"]
            else:
                submission.current_step = current_step + 1
            if submission.current_step > last_step:
                submission.completed_on = timezone.now()
            submission.save()

            serializer = SubmissionSerializer(instance=submission, context={"request": request})

            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data={"reason": errors}, status=status.HTTP_400_BAD_REQUEST)
