from django.contrib import admin

from solo.admin import SingletonModelAdmin

from ...registry import register
from .models import OgoneMerchant, OgoneWebhookConfiguration


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
        "feedback_url",
        "api_key",
        "api_secret",
    )
    readonly_fields = (
        "endpoint",
        "feedback_url",
    )
    list_display = (
        "label",
        "pspid",
        "endpoint",
    )

    def feedback_url(self, obj=None):
        if not obj:
            return ""
        return register["ogone-legacy"].get_webhook_url(None)


@admin.register(OgoneWebhookConfiguration)
class OgoneWebhookAdmin(SingletonModelAdmin):
    pass
