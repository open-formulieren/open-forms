from django import forms

from openforms.utils.form_fields import (
    CheckboxChoicesArrayField,
    get_arrayfield_choices,
)

from .models import JccConfig


class RequiredCustomerFieldsField(CheckboxChoicesArrayField):
    @staticmethod
    def get_field_choices():
        return get_arrayfield_choices(JccConfig, "required_customer_fields")


class JccConfigForm(forms.ModelForm):
    class Meta:
        model = JccConfig
        fields = "__all__"
        field_classes = {
            "required_customer_fields": RequiredCustomerFieldsField,
        }
