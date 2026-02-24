from typing import Any

from django import forms
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
        user_set = {component["key"] for component in components}

        unknown_keys = user_set - initial_set
        missing_keys = initial_set - user_set

        if unknown_keys:
            self.add_error(
                "configuration",
                _("Unknown component keys: {keys}.").format(
                    keys=", ".join(sorted(unknown_keys))
                ),
            )

        if missing_keys:
            self.add_error(
                "configuration",
                _("Required keys are missing: {keys}.").format(
                    keys=", ".join(sorted(missing_keys))
                ),
            )

        return self.cleaned_data
