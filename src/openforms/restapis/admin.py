from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import RestAPI


@admin.register(RestAPI)
class RestAPIAdmin(admin.ModelAdmin):
    list_display = ("label", "api_root", "auth_type")
    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "label",
                    "api_root",
                    "auth_type",
                ),
            },
        ),
        (
            _("Basic authentication"),
            {
                "fields": ("basic_auth_username", "basic_auth_password"),
                "classes": ("collapse",),
            },
        ),
        (
            _("API key"),
            {"fields": ("api_key",), "classes": ("collapse",)},
        ),
        (
            _("JWT"),
            {"fields": ("jwt_payload", "jwt_secret"), "classes": ("collapse",)},
        ),
        (
            _("Custom header"),
            {
                "fields": ("custom_header_key", "custom_header_value"),
                "classes": ("collapse",),
            },
        ),
    )
