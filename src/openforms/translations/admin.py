from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import TranslationsMetaData


@admin.register(TranslationsMetaData)
class TranslationsMetaDataAdmin(admin.ModelAdmin):
    list_display = (
        "language_code",
        "processing_status",
        "last_updated",
        "app_release",
        "default_source_messages_link",
    )
    list_filter = ("language_code", "app_release", "processing_status")
    fieldsets = (
        (
            "",
            {
                "fields": (
                    "language_code",
                    "messages_file",
                    "processing_status",
                    "debug_output",
                )
            },
        ),
        (
            _("Available files"),
            {"fields": ("default_source_messages_link", "compiled_asset")},
        ),
        (
            _("Extra information"),
            {
                "fields": (
                    "last_updated",
                    "messages_count",
                    "app_release",
                )
            },
        ),
    )
    readonly_fields = (
        "default_source_messages_link",
        "compiled_asset",
        "last_updated",
        "messages_count",
        "app_release",
    )

    def default_source_messages_link(self, obj: TranslationsMetaData) -> str:
        if not obj or not obj.language_code:
            return "-"

        # default messages are already part of the static files
        url = f"{settings.STATIC_URL}sdk/i18n/messages/{obj.language_code}.json"

        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            _("Download"),
        )

    default_source_messages_link.short_description = _("Default messages")
