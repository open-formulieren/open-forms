from django.forms import Widget

from openforms.media_assets import get_custom_assets


class FormBuilderWidget(Widget):
    template_name = "forms/widgets/form_builder.html"

    @property
    def media(self):
        return get_custom_assets(include_bootstrap=True)
