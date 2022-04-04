from django import forms
from django.contrib import admin
from django.forms import PasswordInput
from django.utils.translation import gettext_lazy as _

from .models import SoapService, StufService


class StufServiceAdminAdminForm(forms.ModelForm):
    class Meta:
        model = StufService
        widgets = {
            "password": PasswordInput(),
        }
        fields = "__all__"


@admin.register(StufService)
class StufServiceAdmin(admin.ModelAdmin):
    form = StufServiceAdminAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": ("soap_service",),
            },
        ),
        (
            _("StUF parameters"),
            {
                "fields": [
                    "ontvanger_organisatie",
                    "ontvanger_applicatie",
                    "ontvanger_administratie",
                    "ontvanger_gebruiker",
                    "zender_organisatie",
                    "zender_applicatie",
                    "zender_administratie",
                    "zender_gebruiker",
                ]
            },
        ),
        (
            _("Connection"),
            {
                "fields": [
                    "endpoint_beantwoord_vraag",
                    "endpoint_vrije_berichten",
                    "endpoint_ontvang_asynchroon",
                ]
            },
        ),
    )


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
