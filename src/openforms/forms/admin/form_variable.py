from django.contrib import admin

from ..constants import FormVariableSources
from ..models.form_variable import FormVariable


@admin.register(FormVariable)
class FormVariableAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "form", "source")
    list_filter = ("source", "data_type", "is_sensitive_data", "form")
    search_fields = ("name", "form__slug", "form__uuid")
    raw_id_fields = ("form_definition",)

    readonly_fields = (
        "form",
        "name",
        "key",
        "source",
        "prefill_plugin",
        "prefill_attribute",
        "data_type",
        "is_sensitive_data",
        "initial_value",
    )
    fields = (
        "form",
        "form_definition",
        "name",
        "key",
        "source",
        "prefill_plugin",
        "prefill_attribute",
        "data_type",
        "data_format",
        "is_sensitive_data",
        "initial_value",
    )

    def has_delete_permission(self, request, obj=None):
        can_delete = super().has_delete_permission(request, obj)

        if can_delete and obj:
            if obj.source != FormVariableSources.user_defined:
                return False

        return can_delete
