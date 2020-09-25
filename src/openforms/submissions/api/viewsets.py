from rest_framework import permissions, viewsets

from .serializers import (
    SubmissionSerializer,
    SubmissionStepSerializer
)
from ..models import Submission, SubmissionStep


class SubmissionViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubmissionStepViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    queryset = SubmissionStep.objects.all()
    serializer_class = SubmissionStepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(submission__uuid=self.kwargs['submission_uuid'])
