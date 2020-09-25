from django.contrib import admin

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from openforms.core.models import Form, FormStep


class FormStepInline(OrderedTabularInline):
    model = FormStep
    fk_name = 'form'
    fields = ('order', 'move_up_down_links', 'form_definition', )
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)
    extra = 1


class FormAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'backend')
    inlines = (FormStepInline,)
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Form, FormAdmin)
