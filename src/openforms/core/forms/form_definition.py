from django import forms

from ..models import FormDefinition
from ..widgets import FormBuilderWidget


class FormDefinitionForm(forms.ModelForm):
    configuration = forms.CharField(widget=FormBuilderWidget)

    class Meta:
        model = FormDefinition
        fields = ('name', 'slug', 'login_required', 'configuration',)
