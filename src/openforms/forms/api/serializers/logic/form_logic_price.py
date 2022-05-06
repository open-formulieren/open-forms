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
