from rest_framework import serializers

from openforms.forms.api.serializers.logic.form_logic import FormLogicBaseSerializer
from openforms.forms.models import FormPriceLogic


class FormPriceLogicSerializer(FormLogicBaseSerializer):
    class Meta(FormLogicBaseSerializer.Meta):
        model = FormPriceLogic
        fields = FormLogicBaseSerializer.Meta.fields + ("price",)
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:price-logics-detail",
                "lookup_field": "uuid",
            },
        }

class FormPriceLogicListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child", FormPriceLogicSerializer())
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        rules_to_create = [FormPriceLogic(**rule) for rule in validated_data]
        FormPriceLogic.objects.bulk_create(rules_to_create)
