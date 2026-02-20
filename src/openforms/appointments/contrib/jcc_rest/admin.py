from typing import Any

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from solo.admin import SingletonModelAdmin

from .constants import CustomerFields
from .forms import JccRestConfigForm
from .models import JccRestConfig


class FormioConfigMixin(ModelAdmin):
    def render_change_form(
        self,
        request,
        context: dict[str, Any],
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        context.update(
            {
                "available_components": ", ".join(CustomerFields.values),
                "form_mode": "appointment",
            }
        )

        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(JccRestConfig)
class JccRestConfigAdmin(FormioConfigMixin, SingletonModelAdmin):
    form = JccRestConfigForm
    change_form_template = "admin/jcc_rest/jccrestconfig/change_form.html"
