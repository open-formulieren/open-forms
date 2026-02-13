from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ordered_model.admin import OrderedModelAdmin

from ..models import FormLogic


@admin.register(FormLogic)
class FormLogicAdmin(OrderedModelAdmin):
    list_display = (
        "uuid",
        "form_admin_name",
        "description",
        "trigger_from_step",
        "is_advanced",
        "move_up_down_links",
    )
    list_select_related = ("form", "trigger_from_step")
    list_filter = (
        "is_advanced",
        "form",
    )
    search_fields = ("uuid", "description", "json_logic_trigger")
    raw_id_fields = ("form", "trigger_from_step")

    readonly_fields = ("form_steps",)

    @admin.display(description=_("form"))
    def form_admin_name(self, obj):
        return obj.form.admin_name
