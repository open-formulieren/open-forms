from django.contrib import admin

from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.registry import register


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

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)

    def feedback_url(self, obj=None):
        if not obj:
            return ""
        return register["ogone-legacy"].get_webhook_url(self.request)
