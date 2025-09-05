from django.contrib import admin
from django.db.models import Model

from solo.admin import SingletonModelAdmin

from ...registry import register
from .models import WorldlineMerchant, WorldlineWebhookConfiguration


class FeedbackUrlMixin:
    def feedback_url(self, obj: Model | None = None) -> str:
        if not obj:
            return ""
        return register["worldline"].get_webhook_url(None)


@admin.register(WorldlineMerchant)
class WorldlineMerchantAdmin(admin.ModelAdmin, FeedbackUrlMixin):
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


@admin.register(WorldlineWebhookConfiguration)
class WorldlineWebhookConfigurationAdmin(SingletonModelAdmin, FeedbackUrlMixin):
    fields = (
        "webhook_key_id",
        "webhook_key_secret",
        "feedback_url",
    )

    readonly_fields = ("feedback_url",)
    list_display = ("webhook_key_id",)
    search_fields = ("webhook_key_id",)
