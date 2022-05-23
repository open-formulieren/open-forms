from rest_framework import serializers
from zgw_consumers.api_models.catalogi import Catalogus, InformatieObjectType
from zgw_consumers.drf.serializers import APIModelSerializer


class InformatieObjectTypeSerializer(APIModelSerializer):
    class Meta:
        model = InformatieObjectType
        fields = (
            "url",
            "omschrijving",
        )


class CatalogusDomainSerializer(APIModelSerializer):
    class Meta:
        model = Catalogus
        fields = ("domein",)


class InformatieObjectTypeChoiceSerializer(serializers.Serializer):
    informatieobjecttype = InformatieObjectTypeSerializer()
    catalogus = CatalogusDomainSerializer()
