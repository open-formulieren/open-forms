from django.contrib import admin

from .models import AttributeGroup


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    fields = [
        "name",
        "description",
        "attributes",
    ]
    list_display = [
        "name",
        "description",
        "attributes",
    ]
