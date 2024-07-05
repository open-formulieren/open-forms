from rest_framework import serializers
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.drf.serializers import APIModelSerializer

from ....api.serializers import CatalogusDomainSerializer


class ZaakTypeSerializer(APIModelSerializer):
    class Meta:
        model = ZaakType
        fields = (
            "url",
            "omschrijving",
        )


class ZaakTypeChoiceSerializer(serializers.Serializer):
    zaaktype = ZaakTypeSerializer()
    catalogus = CatalogusDomainSerializer()
