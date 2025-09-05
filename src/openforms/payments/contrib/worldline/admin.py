from django.contrib import admin

from solo.admin import SingletonModelAdmin

from ..base import FeedbackUrlMixin
from .models import WorldlineMerchant, WorldlineWebhookConfiguration


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
