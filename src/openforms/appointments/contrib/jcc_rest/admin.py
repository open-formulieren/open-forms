from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .forms import JccRestConfigForm
from .models import JccRestConfig


@admin.register(JccRestConfig)
class JccRestConfigAdmin(SingletonModelAdmin):
    form = JccRestConfigForm
    change_form_template = "admin/jcc_rest/jccrestconfig/change_form.html"

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        # Can't use `openforms.forms.admin.FormioConfigMixin` because the appointment
        # configuration has different semantics - `required_default` is controlled by
        # the upstream API, while file uploads/map components are irrelevant.
        context.update(
            {
                "required_default": False,
                "rich_text_colors": [],
                "map_tile_layers": [],
                "wms_layers": [],
                "upload_filetypes": [],
                "feature_flags": {},
                "confidentiality_levels": [],
                "component_empty_values": [],
            }
        )
        return super().render_change_form(request, context, add, change, form_url, obj)
