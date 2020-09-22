from django import forms

from openforms.core.widgets import FormBuilderWidget
from openforms.core.models import FormDefinition


class FormDefinitionForm(forms.ModelForm):
    configuration = forms.CharField(widget=FormBuilderWidget)

    class Meta:
        model = FormDefinition
        fields = ('name', 'slug', 'login_required', 'configuration', 'scheme_url')
