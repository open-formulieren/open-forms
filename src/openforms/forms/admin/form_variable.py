from django.contrib import admin

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
