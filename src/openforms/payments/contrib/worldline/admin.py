from django.contrib import admin

from ...registry import register
from .models import WorldlineMerchant


# TODO: implement feedback url
@admin.register(WorldlineMerchant)
class WorldlneMerchantAdmin(admin.ModelAdmin):
    fields = (
        "label",
        "pspid",
        "api_key",
        "api_secret",
        "endpoint_preset",
        "endpoint_custom",
        "endpoint",
    )
    readonly_fields = ("endpoint",)
    list_display = (
        "label",
        "pspid",
        "endpoint",
    )
