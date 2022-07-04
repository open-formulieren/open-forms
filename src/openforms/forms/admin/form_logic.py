from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from ordered_model.admin import OrderedModelAdmin

from ..models import FormLogic


@admin.register(FormLogic)
class FormLogicAdmin(OrderedModelAdmin):
    list_display = ("uuid", "form_admin_name", "is_advanced", "move_up_down_links")
    list_select_related = ("form",)
    list_filter = (
        "is_advanced",
        "form",
    )
    search_fields = ("uuid", "json_logic_trigger")
    raw_id_fields = ("form",)

    @admin.display(description=_("form"))
    def form_admin_name(self, obj):
        return obj.form.admin_name
