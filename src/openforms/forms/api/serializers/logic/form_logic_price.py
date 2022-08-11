from openforms.api.serializers import ListWithChildSerializer
from openforms.forms.api.serializers.logic.form_logic import FormLogicBaseSerializer
from openforms.forms.models import FormPriceLogic


class FormPriceLogicSerializer(FormLogicBaseSerializer):
    class Meta(FormLogicBaseSerializer.Meta):
        model = FormPriceLogic
        fields = FormLogicBaseSerializer.Meta.fields + ("price",)
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:form-price-logic-rules",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
        }


class FormPriceLogicListSerializer(ListWithChildSerializer):
    child_serializer_class = FormPriceLogicSerializer
