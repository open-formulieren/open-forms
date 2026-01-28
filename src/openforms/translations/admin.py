from django.contrib import admin
from django.db import transaction
from django.forms import ModelForm
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from privates.admin import PrivateMediaMixin

from .models import TranslationsMetaData
from .tasks import process_custom_translation_assets


@admin.register(TranslationsMetaData)
class TranslationsMetaDataAdmin(PrivateMediaMixin, admin.ModelAdmin):
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
        "processing_status",
        "debug_output",
        "default_source_messages_link",
        "compiled_asset",
        "last_updated",
        "messages_count",
        "app_release",
    )
    private_media_fields = ("compiled_asset",)
    private_media_view_options = {"attachment": True}

    @admin.display(description=_("Default messages"))
    def default_source_messages_link(self, obj: TranslationsMetaData) -> str:
        if not obj or not obj.language_code:
            return "-"

        # default messages are already part of the static files
        url = static(f"sdk/i18n/messages/{obj.language_code}.json")
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            url,
            _("Download"),
        )

    def save_model(
        self,
        request: HttpRequest,
        obj: TranslationsMetaData,
        form: ModelForm,
        change: bool,
    ) -> None:
        super().save_model(request, obj, form, change)

        if "messages_file" in form.changed_data:
            transaction.on_commit(lambda: process_custom_translation_assets(obj.pk))
