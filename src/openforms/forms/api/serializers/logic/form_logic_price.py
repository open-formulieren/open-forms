from openforms.api.serializers import ListWithChildSerializer
from openforms.forms.api.serializers.logic.form_logic import FormLogicBaseSerializer
from openforms.forms.models import FormPriceLogic


class FormPriceLogicListSerializer(ListWithChildSerializer):
    child_serializer_class = "openforms.forms.api.serializers.logic.form_logic_price.FormPriceLogicSerializer"


class FormPriceLogicSerializer(FormLogicBaseSerializer):
    class Meta(FormLogicBaseSerializer.Meta):
        model = FormPriceLogic
        list_serializer_class = FormPriceLogicListSerializer
        fields = FormLogicBaseSerializer.Meta.fields + ("price",)
        extra_kwargs = {
            **FormLogicBaseSerializer.Meta.extra_kwargs,
            "url": {
                "view_name": "api:form-price-logic-rules",
                "lookup_field": "uuid",
                "lookup_url_kwarg": "uuid_or_slug",
            },
        }
