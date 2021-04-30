from django import forms
from django.contrib import admin

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from openforms.registrations.admin import BackendChoiceFieldMixin

from ..backends import registry
from ..models import Form, FormStep


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
class FormAdmin(
    BackendChoiceFieldMixin, OrderedInlineModelAdminMixin, admin.ModelAdmin
):
    list_display = ("name", "registration_backend", "registration_backend_options")
    inlines = (FormStepInline,)
    prepopulated_fields = {"slug": ("name",)}

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
