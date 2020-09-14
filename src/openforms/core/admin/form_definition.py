from django.contrib import admin

from openforms.core.forms import FormDefinitionForm
from openforms.core.models import FormDefinition


class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(FormDefinition, FormDefinitionAdmin)
