from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..clients import CatalogiClient


class ProvidesCatalogiClientQueryParamsSerializer(serializers.Serializer):

    def get_ztc_client(self) -> CatalogiClient:
        raise NotImplementedError()


class DocumentTypesFilter(serializers.Serializer):
    catalogus_url = serializers.URLField(
        label=_("catalogus URL"),
        help_text=_("Filter informatieobjecttypen against this catalogus URL."),
        required=False,
        default="",
    )

    def get_ztc_client(self) -> CatalogiClient:
        raise NotImplementedError()
