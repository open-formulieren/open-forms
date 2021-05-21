from django import forms
from django.contrib import admin
from django.forms import PasswordInput

from solo.admin import SingletonModelAdmin

from .models import SoapService, StufZDSConfig


@admin.register(StufZDSConfig)
class StufZDSConfigAdmin(SingletonModelAdmin):
    pass


class SoapServiceAdminAdminForm(forms.ModelForm):
    class Meta:
        model = SoapService
        widgets = {
            "password": PasswordInput(),
        }
        fields = "__all__"


@admin.register(SoapService)
class SoapServiceAdmin(admin.ModelAdmin):
    form = SoapServiceAdminAdminForm
