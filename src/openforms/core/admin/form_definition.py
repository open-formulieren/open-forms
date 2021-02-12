from django.contrib import admin

from ..forms import FormDefinitionForm
from ..models import FormDefinition


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {"slug": ("name",)}
