from rest_framework import serializers

from openforms.api.utils import get_from_serializer_data_or_instance
from openforms.payments.registry import register as payment_register

from ....models import Form
from ..typing import PaymentData


def get_payment_backend_choices():
    return [("", "")] + payment_register.get_choices()


class FormPaymentSerializer(serializers.ModelSerializer):
    backend = serializers.ChoiceField(source="payment_backend", choices=[])
    options = serializers.DictField(source="payment_backend_options")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_fields(self):
        fields = super().get_fields()
        backend_field = fields["backend"]
        assert isinstance(backend_field, serializers.ChoiceField)
        backend_field.choices = get_payment_backend_choices()
        return fields

    def validate(self, attrs: PaymentData) -> PaymentData:
        plugin_id = get_from_serializer_data_or_instance(
            "payment_backend", data=attrs, serializer=self
        )
        options = get_from_serializer_data_or_instance(
            "payment_backend_options", data=attrs, serializer=self
        )
        if not plugin_id:
            return attrs
        plugin = payment_register[plugin_id]
        serializer = plugin.configuration_options(data=options)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # wrap detail in dict so we can attach it to the field
            # DRF will create the .invalidParams with a dotted path to nested fields
            # like registrationBackends.0.options.toEmails.0 if the first email was invalid
            detail = {"options": e.detail}
            raise serializers.ValidationError(detail) from e
        # serializer does some normalization, so make sure to update the data
        attrs["payment_backend_options"] = serializer.data
        return attrs

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = Form
        fields = ("backend", "options")
