from django.contrib import admin

from openforms.payments.contrib.ogone.models import OgoneMerchant

# @admin.register(OgoneConfig)
# class OgoneConfigAdmin(admin.ModelAdmin):
#     pass


@admin.register(OgoneMerchant)
class OgoneMerchantAdmin(admin.ModelAdmin):
    fields = (
        "label",
        "pspid",
        "hash_algorithm",
        "sha_in_passphrase",
        "sha_out_passphrase",
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
