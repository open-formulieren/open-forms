from rest_framework import authentication, permissions, serializers, views
from zgw_consumers.models import Service

from openforms.api.views import ListMixin


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = (
            "label",
            "api_root",
            "api_type",
        )


class ServiceListView(views.APIView, ListMixin):
    """
    List configured services.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = ServiceSerializer

    def get_objects(self):
        return Service.objects.all()
