from django.contrib import admin

from .models import WorldlineMerchant


@admin.register(WorldlineMerchant)
class WorldlneMerchantAdmin(admin.ModelAdmin):
    fields = (
        "label",
        "pspid",
        "api_key",
        "api_secret",
        "endpoint",
    )
    list_display = (
        "label",
        "pspid",
        "endpoint",
    )
