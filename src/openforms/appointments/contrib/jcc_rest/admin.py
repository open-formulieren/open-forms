from typing import Any

from django.contrib import admin

from solo.admin import SingletonModelAdmin

from .forms import JccRestConfigForm
from .models import JccRestConfig


@admin.register(JccRestConfig)
class JccRestConfigAdmin(SingletonModelAdmin):
    form = JccRestConfigForm
    change_form_template = "admin/jcc_rest/jccrestconfig/change_form.html"

    def render_change_form(
        self,
        request,
        context: dict[str, Any],
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        context.update({"form_mode": "appointment"})

        return super().render_change_form(request, context, add, change, form_url, obj)
