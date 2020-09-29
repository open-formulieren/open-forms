from django.utils import timezone

from rest_framework import permissions, status, viewsets, views
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Submission, SubmissionStep
from .serializers import SubmissionSerializer, SubmissionStepSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def completed(self, request, uuid=None):
        # TODO: Maybe check if all steps are done?
        submission = self.get_object()
        submission.completed_on = timezone.now()
        submission.save()
        # TODO: Also prevent changes to the submission after completing.
        serializer = self.get_serializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubmissionStepViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = SubmissionStep.objects.all()
    serializer_class = SubmissionStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(submission__uuid=self.kwargs['submission_uuid'])
