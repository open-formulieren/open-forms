from rest_framework import serializers

from ..registry import register as payment_register
from .serializers import PaymentOptionSerializer


class PaymentOptionsReadOnlyField(serializers.ListField):
    """
    the read-mode of the payment information shows detailed options instead of plugin-ids

    there is no write-mode support because this data is not writable
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("child", PaymentOptionSerializer())
        kwargs["read_only"] = True
        kwargs["source"] = "*"
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        raise NotImplementedError("read only")

    def to_representation(self, form):
        request = self.context["request"]
        temp = payment_register.get_options(request, form)
        return super().to_representation(temp)
