from django.contrib import admin

from solo.admin import SingletonModelAdmin

from openforms.utils.urls import reverse_plus

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
    fields = (
        "webhook_key_id",
        "webhook_key_secret",
        "feedback_url",
    )

    readonly_fields = ("feedback_url",)

    def feedback_url(self, obj: OgoneWebhookConfiguration | None = None) -> str:
        return reverse_plus(
            "payments:webhook",
            kwargs={"plugin_id": "worldline"},
            request=None,
        )
