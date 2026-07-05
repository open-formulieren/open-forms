from openforms.config.models import Theme
from openforms.forms.models import Form

from .base import BaseResource


class ThemeResource(BaseResource):
    class Meta:
        model = Theme
        fields = (
            "uuid",
            "name",
            "organization_name",
            "main_website",
            "favicon",
            "email_logo",
            "classname",
            "stylesheet",
            "stylesheet_file",
            "design_token_values",
        )

    def export_for_form(self, form: Form):
        return self.export(queryset=[form.theme] if form.theme is not None else [])
