from django.contrib import admin

from ...registry import register
from .models import WorldlineMerchant, WorldlineWebhookEntry


@admin.register(WorldlineMerchant)
class WorldlineMerchantAdmin(admin.ModelAdmin):
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
        "feedback_url",
    )
    search_fields = (
        "label",
        "pspid",
        "api_key",
    )

    def feedback_url(self, obj: WorldlineMerchant | None = None) -> str:
        if not obj:
            return ""
        return register["worldline"].get_webhook_url(None)


@admin.register(WorldlineWebhookEntry)
class WorldlineWebhookEntryAdmin(admin.ModelAdmin):
    fields = (
        "webhook_key_id",
        "webhook_key_secret",
    )

    list_display = ("webhook_key_id",)
    search_fields = ("webhook_key_id",)
