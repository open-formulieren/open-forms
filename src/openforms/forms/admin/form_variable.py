from django.contrib import admin

from openforms.forms.models.form_variable import FormVariable


@admin.register(FormVariable)
class FormVariableAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "form", "source")
    list_filter = ("name", "key", "form")
    search_fields = ("name",)
