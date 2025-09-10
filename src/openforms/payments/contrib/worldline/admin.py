from django.contrib import admin
from django.utils.html import format_html

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
        url = register["worldline"].get_webhook_url(None)
        return format_html(
            '<a href="{url}" target="_blank" rel="noopener nofollower">{url}</a>',
            url=url,
        )
