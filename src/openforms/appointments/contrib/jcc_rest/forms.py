from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.forms import Widget
from django.utils.translation import gettext_lazy as _

from openforms.formio.validators import validate_formio_js_schema

from .constants import CustomerFields
from .models import JccRestConfig


class FormBuilderWidget(Widget):
    template_name = "jcc_rest/widgets/form_builder.html"

    class Media:
        css = {
            "all": (
                "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css",
                "bundles/core-css.css",
            ),
        }
        js = ("bundles/core-js.js",)


class JccRestConfigForm(forms.ModelForm):
    configuration = forms.JSONField(
        widget=FormBuilderWidget, validators=[validate_formio_js_schema]
    )

    class Meta:
        model = JccRestConfig
        fields = (
            "service",
            "configuration",
        )

    def clean(self) -> dict[str, Any]:
        super().clean()

        components = self.cleaned_data["configuration"]["components"]

        initial_set = set(CustomerFields.values)
        user_set = set([component["key"] for component in components])
        modified = user_set - initial_set

        if modified:
            raise ValidationError(
                {
                    "configuration": _(
                        "Unknown component key for fields: {keys}. "
                        "Adding a component or modifying a component's key is not allowed."
                    ).format(keys=",".join(modified))
                }
            )

        return self.cleaned_data
