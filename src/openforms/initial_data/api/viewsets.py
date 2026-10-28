from typing import override

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, viewsets
from rest_framework.authentication import TokenAuthentication

from ..models import InitialSubmissionData
from .serializers import InitialSubmissionDataSerializer


@extend_schema_view(
    create=extend_schema(
        summary=_("Create initial submission data"),
        description=_(
            "Prepare initial submission data by sending the authentication details for "
            "a given form. The response contains the redirect URL for the user about "
            "to fill out the form.\n\nWe recommend keeping the TTL as low as possible "
            "to limit the duration that plain text person/company identifiers are "
            "stored in the database."
        ),
    ),
    retrieve=extend_schema(
        summary=_("Retrieve initial submission data"),
        description=_(
            "Look up existing initial submission data by UUID. The identifiers/data "
            "are not returned, only the redirect URL and metadata. Only the original "
            "creator can access the initial data."
        ),
    ),
)
class InitialSubmissionDataViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet[InitialSubmissionData],
):
    """
    Create and retrieve initial submission data records.

    List operations, updates and deletes are not supported. Given the TTL, records will
    automatically be deleted by background jobs so if a mistake was made, the incorrect
    data will automatically get wiped.

    API users who created an object can look it up again, but not objects from other
    users.
    """

    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.DjangoModelPermissions,)
    queryset = InitialSubmissionData.objects.none()
    serializer_class = InitialSubmissionDataSerializer
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_queryset(self) -> models.QuerySet[InitialSubmissionData]:
        """
        Only allow users to access records they own.
        """
        return InitialSubmissionData.objects.annotate(
            _expiry_date=models.F("created_on") + models.F("ttl")
        ).filter(owner=self.request.user, _expiry_date__gte=timezone.now())

    @override
    def perform_create(self, serializer) -> None:
        serializer.save(owner=self.request.user)
