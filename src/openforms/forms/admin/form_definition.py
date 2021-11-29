from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected as _delete_selected
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from ...utils.expressions import FirstNotBlank
from ..forms import FormDefinitionForm
from ..models import FormDefinition, FormStep


def delete_selected(modeladmin, request, queryset):
    actively_used = queryset.filter(formstep__isnull=False)
    for name in actively_used.annotate(
        admin_name=FirstNotBlank("internal_name", "name")
    ).values_list("admin_name", flat=True):
        messages.error(
            request,
            _(
                "{name} cannot be removed because it is used in one or more forms."
            ).format(name=name),
        )
    safe_to_delete = queryset.exclude(id__in=actively_used.values_list("id", flat=True))
    return _delete_selected(modeladmin, request, safe_to_delete)


delete_selected.allowed_permissions = ("delete",)
delete_selected.short_description = _("Delete selected %(verbose_name_plural)s")


@admin.register(FormDefinition)
class FormDefinitionAdmin(admin.ModelAdmin):
    form = FormDefinitionForm
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("anno_name", "used_in_forms", "is_reusable")
    actions = ["overridden_delete_selected", "make_copies"]
    list_filter = ["is_reusable"]
    search_fields = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request=request)
        used_in_forms = Prefetch(
            "formstep_set",
            queryset=FormStep.objects.select_related("form").distinct(
                "form", "form_definition"
            ),
            to_attr="used_in_steps",
        )
        qs = qs.prefetch_related(used_in_forms)
        # annotate .name
        qs = qs.annotate(anno_name=FirstNotBlank("internal_name", "name"))
        return qs

    def anno_name(self, obj):
        return obj.admin_name

    anno_name.admin_order_field = "anno_name"
    anno_name.short_description = _("name")

    def get_actions(self, request):
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            (old_func, name, short_description) = actions["delete_selected"]
            actions["delete_selected"] = (delete_selected, name, short_description)
        return actions

    def make_copies(self, request, queryset):
        for instance in queryset:
            instance.copy()

    make_copies.short_description = _("Copy selected %(verbose_name_plural)s")

    def used_in_forms(self, obj) -> str:
        forms = [step.form for step in obj.used_in_steps]
        ret = format_html_join(
            "\n",
            '<li><a href="{}">{}</a></li>',
            (
                (
                    reverse(
                        "admin:forms_form_change",
                        kwargs={"object_id": form.pk},
                    ),
                    form.admin_name,
                )
                for form in forms
            ),
        )

        return format_html("<ul>{}</ul>", ret)

    used_in_forms.short_description = _("used in")
