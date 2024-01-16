from rest_framework import serializers

from ..models import BRPPersonenRequestOptions


class BRPPersonenRequestOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BRPPersonenRequestOptions
        fields = (
            "brp_personen_purpose_limitation_header_value",
            "brp_personen_processing_header_value",
        )
