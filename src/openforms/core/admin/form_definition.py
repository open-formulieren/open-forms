from django.contrib import admin

from openforms.core.forms import FormDefinitionForm


class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {'slug': ('name',)}
