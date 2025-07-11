from django import forms
from django.utils.translation import gettext_lazy as _

from tinymce.widgets import TinyMCE

from .models import ConfirmationEmailTemplate


class ConfirmationEmailTemplateForm(forms.ModelForm):
    class Meta:
        model = ConfirmationEmailTemplate
        fields = "__all__"  # noqa: DJ007

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            # Set the widget for all language variants of `content`
            if field_name.startswith("content_"):
                field.widget = TinyMCE(attrs={"cols": 80, "rows": 30})


class EmailTestForm(forms.Form):
    recipient = forms.EmailField(label=_("Email address"), required=True)
