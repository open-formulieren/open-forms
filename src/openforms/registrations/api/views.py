from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType

from openforms.api.views import ListMixin

from ..constants import RegistrationAttribute
from ..registry import register
from .filters import ListInformatieObjectTypenQueryParamsSerializer
from .serializers import (
    ChoiceWrapper,
    InformatieObjectTypeChoiceSerializer,
    RegistrationAttributeSerializer,
    RegistrationPluginSerializer,
)


@extend_schema_view(
    get=extend_schema(summary=_("List available registration plugins")),
)
class PluginListView(ListMixin, APIView):
    """
    List all available registration plugins.

    Registration plugins are responsible for the implementation details to register the form submission
    with various backends, such as "API's voor zaakgericht werken", StUF-ZDS and others.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegistrationPluginSerializer

    def get_objects(self):
        return list(register.iter_enabled_plugins())


@extend_schema_view(
    get=extend_schema(summary=_("List available registration attributes")),
)
class AllAttributesListView(ListMixin, APIView):
    """
    List the available registration attributes.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = RegistrationAttributeSerializer

    def get_objects(self):
        choices = RegistrationAttribute.choices

        return [ChoiceWrapper(choice) for choice in choices]


@extend_schema_view(
    get=extend_schema(
        summary=_("List available InformatieObjectTypen"),
        parameters=[ListInformatieObjectTypenQueryParamsSerializer],
    ),
)
class InformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen based on the configured registration backend and ZGW APIs services.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeChoiceSerializer

    def get_objects(self):
        filter_serializer = ListInformatieObjectTypenQueryParamsSerializer(
            data=self.request.query_params
        )
        filter_serializer.is_valid(raise_exception=True)

        client = filter_serializer.get_ztc_client()
        if not client:
            return []

        catalogus_data = client.get_all_catalogi()
        catalogus_mapping = {
            catalogus["url"]: catalogus for catalogus in catalogus_data
        }

        iotypen_data = client.get_all_informatieobjecttypen()
        iotypen = [
            {
                "informatieobjecttype": factory(InformatieObjectType, iotype),
                "catalogus": factory(Catalogus, catalogus_mapping[iotype["catalogus"]]),
            }
            for iotype in iotypen_data
        ]

        return iotypen
