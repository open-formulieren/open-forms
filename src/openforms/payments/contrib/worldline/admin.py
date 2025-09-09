from django.contrib import admin

from solo.admin import SingletonModelAdmin

from ...registry import register
from .models import WorldlineMerchant, WorldlineWebhookConfiguration


@admin.register(WorldlineMerchant)
class WorldlineMerchantAdmin(admin.ModelAdmin):
    fields = (
        "label",
        "pspid",
        "api_key",
        "api_secret",
        "endpoint",
        "feedback_url",
    )
    list_display = (
        "label",
        "pspid",
        "endpoint",
    )
    search_fields = (
        "label",
        "pspid",
        "api_key",
    )
    readonly_fields = ("feedback_url",)

    def feedback_url(self, obj: WorldlineMerchant | None = None) -> str:
        return register["worldline"].get_webhook_url(None)


@admin.register(WorldlineWebhookConfiguration)
class WorldlineWebhookConfigurationAdmin(SingletonModelAdmin):
    fields = (
        "webhook_key_id",
        "webhook_key_secret",
        "feedback_url",
    )

    list_display = ("webhook_key_id",)
    search_fields = ("webhook_key_id",)
    readonly_fields = ("feedback_url",)

    def feedback_url(self, obj: WorldlineWebhookConfiguration | None = None) -> str:
        return register["worldline"].get_webhook_url(None)
