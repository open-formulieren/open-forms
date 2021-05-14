from django import forms

from tinymce.widgets import TinyMCE

from .models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = ConfirmationEmailTemplate
        fields = "__all__"
