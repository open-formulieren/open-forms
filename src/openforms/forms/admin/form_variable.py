from django.contrib import admin

from ..models import FormVariable


@admin.register(FormVariable)
class FormVariableAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "form__name", "source")
    list_filter = ("name", "slug", "form", "form_definition")
    search_fields = ("name",)
