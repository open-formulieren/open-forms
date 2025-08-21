from django.contrib import admin

from .models import AttributeGroup


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    fields = (
        "name",
        "uuid",
        "description",
        "attributes",
    )
    readonly_fields = ("uuid",)
    list_display = (
        "name",
        "uuid",
        "description",
        "attributes",
    )
    search_fields = ("uuid", "name")
