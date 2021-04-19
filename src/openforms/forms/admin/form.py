from django import forms
from django.contrib import admin

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from ..backends import registry
from ..models import Form, FormStep
from .registry import inline_registry


class FormStepInline(OrderedTabularInline):
    model = FormStep
    fk_name = "form"
    fields = (
        "order",
        "move_up_down_links",
        "form_definition",
        "optional",
        "availability_strategy",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    ordering = ("order",)
    extra = 1


@admin.register(Form)
class FormAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    list_display = ("name", "backend")
    inlines = (FormStepInline,)
    prepopulated_fields = {"slug": ("name",)}

    change_form_template = "admin/forms/form_change_form.html"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        inline_mapping = {}

        obj = self.get_object(request, object_id)

        for name, inline in inline_registry.items():
            inline_mapping[name] = inline.model._meta.model_name

        context = {"inline_mapping": inline_mapping}
        return super().change_view(
            request, object_id, form_url=form_url, extra_context=context
        )

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj=obj)
        for _, config_inline in inline_registry.items():
            inlines += [config_inline(self.model, self.admin_site)]
        return inlines

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "backend":
            choices = [(path, path.split(".")[-1]) for path in registry]
            choices.insert(0, ("", "---------"))

            return forms.ChoiceField(
                label=db_field.verbose_name.capitalize(),
                choices=choices,
                required=False,
                help_text=db_field.help_text,
            )

        return super().formfield_for_dbfield(db_field, request, **kwargs)
