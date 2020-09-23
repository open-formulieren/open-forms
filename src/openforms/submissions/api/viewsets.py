from rest_framework import permissions, viewsets

from .serializers import (
    SubmissionSerializer
)
from ..models import Submission


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
