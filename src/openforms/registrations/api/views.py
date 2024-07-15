from typing import ClassVar

from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import authentication, permissions
from rest_framework.views import APIView
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType

from openforms.api.views import ListMixin

from ..constants import RegistrationAttribute
from ..registry import register
from .filters import BaseAPIGroupQueryParamsSerializer
from .serializers import (
    CatalogusSerializer,
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


class BaseCatalogiListView(ListMixin, APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = CatalogusSerializer
    filter_serializer_class: ClassVar[type[BaseAPIGroupQueryParamsSerializer]]

    def get_objects(self):
        filter_serializer = self.filter_serializer_class(
            data=self.request.query_params,
        )
        filter_serializer.is_valid(raise_exception=True)

        client = filter_serializer.get_ztc_client()
        catalogus_data = client.get_all_catalogi()
        return factory(Catalogus, catalogus_data)


class BaseInformatieObjectTypenListView(ListMixin, APIView):
    """
    List the available InformatieObjectTypen.

    Each InformatieObjectType is uniquely identified by its 'omschrijving', 'catalogus',
    and beginning and end date. If multiple same InformatieObjectTypen exist for different dates,
    only one entry is returned.
    """

    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAdminUser,)
    serializer_class = InformatieObjectTypeChoiceSerializer
    filter_serializer_class: ClassVar[type[BaseAPIGroupQueryParamsSerializer]]

    def get_objects(self):
        filter_serializer = self.filter_serializer_class(data=self.request.query_params)
        filter_serializer.is_valid(raise_exception=True)

        client = filter_serializer.get_ztc_client()

        catalogus_data = client.get_all_catalogi()
        catalogus_mapping = {
            catalogus["url"]: catalogus for catalogus in catalogus_data
        }

        if "catalogus_domein" in filter_serializer.validated_data:
            domein = filter_serializer.validated_data["catalogus_domein"]
            # `catalogus_rsin` is guaranteed to be present if `catalogus_domein` is:
            rsin = filter_serializer.validated_data["catalogus_rsin"]

            matching_catalogus: str | None = next(
                (
                    catalogus["url"]
                    for catalogus in catalogus_data
                    if catalogus["domein"] == domein and catalogus["rsin"] == rsin
                ),
                None,
            )

            if matching_catalogus is None:
                return []

            iotypen_data = client.get_all_informatieobjecttypen(
                catalogus=matching_catalogus
            )
        else:
            iotypen_data = client.get_all_informatieobjecttypen()

        iotypen = []

        for iotype in iotypen_data:
            # fmt: off
            exists = any(
                existing_iotype["informatieobjecttype"].omschrijving == iotype["omschrijving"]
                and existing_iotype["informatieobjecttype"].catalogus == iotype["catalogus"]
                for existing_iotype in iotypen
            )
            # fmt: on

            if not exists:
                iotypen.append(
                    {
                        "informatieobjecttype": factory(InformatieObjectType, iotype),
                        "catalogus": factory(
                            Catalogus, catalogus_mapping[iotype["catalogus"]]
                        ),
                    }
                )

        return iotypen
