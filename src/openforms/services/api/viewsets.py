from rest_framework import authentication, mixins, permissions, viewsets
from zgw_consumers.models import Service

from . import serializers


class ServiceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Configured Services
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = serializers.ServiceSerializer

    queryset = Service.objects.all()
