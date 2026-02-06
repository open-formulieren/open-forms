from django import forms

from openforms.formio.validators import validate_formio_js_schema

from ..models import FormDefinition
from ..widgets import FormBuilderWidget


class FormDefinitionForm(forms.ModelForm):
    configuration = forms.JSONField(
        widget=FormBuilderWidget, validators=[validate_formio_js_schema]
    )

    class Meta:
        model = FormDefinition
        fields = (
            "uuid",
            "name",
            "internal_name",
            "slug",
            "login_required",
            "is_reusable",
            "configuration",
        )
        widgets = {"uuid": forms.TextInput(attrs={"readonly": True})}
