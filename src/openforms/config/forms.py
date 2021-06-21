from django import forms
from django.utils.translation import gettext as _

from tinymce.widgets import TinyMCE

from openforms.config.models import GlobalConfiguration


class GlobalConfigurationForm(forms.ModelForm):
    submission_confirmation_template = forms.CharField(
        required=False,
        widget=TinyMCE(attrs={"cols": 80, "rows": 30}),
        help_text=_(
            "The content of the submission confirmation page. It can contain variables that will be "
            "templated from the submitted form data."
        ),
    )

    class Meta:
        model = GlobalConfiguration
        fields = "__all__"
