from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from ..base import AppointmentProduct


class ProductIDField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label", _("product ID"))
        super().__init__(*args, **kwargs)

    def run_validation(self, data) -> AppointmentProduct:
        """
        Normalize to dataclass instance.
        """
        value = super().run_validation(data)
        return AppointmentProduct(identifier=value, code="", name="")
