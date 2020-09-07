from django.contrib import admin


class FormDefinitionAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
