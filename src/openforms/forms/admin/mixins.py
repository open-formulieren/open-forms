from django.utils.encoding import force_str
from django.utils.translation import gettext as _

from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen

from openforms.config.constants import UploadFileType
from openforms.config.models import GlobalConfiguration, RichTextColor


def get_rich_text_colors():
    colors = list(RichTextColor.objects.values("color", "label"))
    if not colors:
        colors = [
            {"color": "red", "label": force_str(_("Red"))},
        ]
    return colors


class FormioConfigMixin:
    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        config = GlobalConfiguration.get_solo()
        context.update(
            {
                "required_default": config.form_fields_required_default,
                "rich_text_colors": get_rich_text_colors(),
                "upload_filetypes": [
                    {"label": label, "value": value}
                    for value, label in UploadFileType.choices
                ],
                "feature_flags": {
                    "react_formio_builder_enabled": config.enable_react_formio_builder,
                },
                "confidentiality_levels": [
                    {"label": label, "value": value}
                    for value, label in VertrouwelijkheidsAanduidingen.choices
                ],
            }
        )

        return super().render_change_form(request, context, add, change, form_url, obj)
