from django import forms
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE

from .models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(attrs={"cols": 80, "rows": 30}))

    class Meta:
        model = ConfirmationEmailTemplate
        fields = "__all__"


class EmailTestForm(forms.Form):
    recipient = forms.EmailField(label=_("Email address"), required=True)
