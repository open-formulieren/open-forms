from django import forms
from django.contrib import admin
from django.forms import PasswordInput
from django.utils.translation import gettext_lazy as _

from .models import StufService


class StufServiceAdminAdminForm(forms.ModelForm):
    class Meta:
        model = StufService
        fields = "__all__"  # noqa: DJ007
        widgets = {
            # turn off autocomplete: https://stackoverflow.com/q/33113891
            "password": PasswordInput(attrs={"autocomplete": "new-password"}),
        }


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
