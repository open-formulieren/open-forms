from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from soap.models import SoapService


@admin.register(SoapService)
class SoapServiceAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "url",
    )
    search_fields = (
        "label",
        "url",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ("label", "url", "soap_version"),
            },
        ),
        (
            _("Authentication"),
            {
                "fields": [
                    "endpoint_security",
                    "user",
                    "password",
                    "client_certificate",
                    "server_certificate",
                ]
            },
        ),
    )

    class Meta:
        model = SoapService
        fields = "__all__"
