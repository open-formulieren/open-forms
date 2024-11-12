from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..clients import CatalogiClient


class ProvidesCatalogiClientQueryParamsSerializer(serializers.Serializer):

    def get_ztc_client(self) -> CatalogiClient:
        raise NotImplementedError()


class DocumentTypesFilter(serializers.Serializer):
    # TODO -> to english
    catalogus_url = serializers.URLField(
        label=_("catalogus URL"),
        help_text=_("Filter informatieobjecttypen against this catalogus URL."),
        required=False,
        default="",
    )
    case_type_identification = serializers.CharField(
        required=False,
        label=_("case type identification"),
        help_text=_(
            "Filter document types for a given case type. The identification is unique "
            "within the catalogue for a case type. Note that multiple versions of the "
            "same case type with the same identification exist. The filter returns a "
            "document type if it occurs within any version of the specified case type."
        ),
        default="",
    )

    def validate(self, attrs):
        if attrs["case_type_identification"] and not attrs["catalogus_url"]:
            raise serializers.ValidationError(
                {
                    "catalogus_url": _(
                        "A catalogue URL is required when filtering for a case type."
                    ),
                },
                code="required",
            )
        return attrs

    def get_ztc_client(self) -> CatalogiClient:
        raise NotImplementedError()
