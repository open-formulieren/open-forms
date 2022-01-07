from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from furl import furl
from rest_framework import authentication, permissions
from rest_framework.views import APIView

from openforms.registrations.contrib.zgw_apis.models import ZgwConfig
from openforms.utils.api.views import ListMixin

from ..constants import RegistrationAttribute
from ..registry import register
from .serializers import (
    ChoiceWrapper,
    InformatieObjectTypeSerializer,
    InformatieObjectTypeWrapper,
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
    get=extend_schema(summary=_("List available InformatieObjectTypen")),
)
class InformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeSerializer

    def get_objects(self):
        config = ZgwConfig().get_solo()

        if not config.ztc_service:
            return []

        client = config.ztc_service.build_client()

        catalogus_mapping = {}
        query_params = {}
        while True:
            catalogi_data = client.list("catalogus", query_params=query_params)
            catalogus_mapping.update(
                {c["url"]: c["domein"] for c in catalogi_data["results"]}
            )

            if catalogi_data["next"]:
                url = furl(catalogi_data["next"])
                query_params = url.query.params
            else:
                break

        iotypen = []
        query_params = {}
        while True:
            iotypen_data = client.list(
                "informatieobjecttype", query_params=query_params
            )
            iotypen += [
                InformatieObjectTypeWrapper(
                    (
                        iotype["omschrijving"],
                        iotype["url"],
                        catalogus_mapping[iotype["catalogus"]],
                    )
                )
                for iotype in iotypen_data["results"]
            ]

            if iotypen_data["next"]:
                url = furl(iotypen_data["next"])
                query_params = url.query.params
            else:
                break
        return iotypen
