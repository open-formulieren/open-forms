from django import forms
from django.contrib import admin

from solo.admin import SingletonModelAdmin

from openforms.utils.form_fields import (
    CheckboxChoicesArrayField,
    get_arrayfield_choices,
)

from .models import QmaticConfig


class RequiredCustomerFieldsField(CheckboxChoicesArrayField):
    @staticmethod
    def get_field_choices():
        return get_arrayfield_choices(QmaticConfig, "required_customer_fields")


class QmaticConfigForm(forms.ModelForm):
    class Meta:
        model = QmaticConfig
        fields = "__all__"  # noqa: DJ007
        field_classes = {
            "required_customer_fields": RequiredCustomerFieldsField,
        }


@admin.register(QmaticConfig)
class QmaticConfigAdmin(SingletonModelAdmin):
    form = QmaticConfigForm
