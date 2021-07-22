from django import forms
from django.contrib import admin
from django.forms import PasswordInput
from django.utils.translation import gettext_lazy as _

from privates.admin import PrivateMediaMixin

from .models import SoapService


class SoapServiceAdminAdminForm(forms.ModelForm):
    class Meta:
        model = SoapService
        widgets = {
            "password": PasswordInput(),
        }
        fields = "__all__"


@admin.register(SoapService)
class SoapServiceAdmin(PrivateMediaMixin, admin.ModelAdmin):
    private_media_fields = ("certificate", "certificate_key")
    private_media_view_options = {"attachment": True}

    form = SoapServiceAdminAdminForm
    fieldsets = (
        (
            None,
            {
                "fields": ("label",),
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
                    "soap_version",
                    "url",
                    "endpoint_beantwoord_vraag",
                    "endpoint_vrije_berichten",
                    "endpoint_ontvang_asynchroon",
                ]
            },
        ),
        (
            _("Authentication"),
            {
                "fields": [
                    "endpoint_security",
                    "user",
                    "password",
                    "certificate",
                    "certificate_key",
                ]
            },
        ),
    )
