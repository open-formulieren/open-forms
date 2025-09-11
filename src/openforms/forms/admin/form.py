from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_list import result_headers
from django.db.models import BooleanField, Case, Count, F, Value, When
from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _, ngettext

from modeltranslation.manager import get_translatable_fields_for_model
from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from openforms.api.utils import underscore_to_camel
from openforms.emails.models import ConfirmationEmailTemplate
from openforms.registrations.admin import RegistrationBackendFieldMixin
from openforms.typing import StrOrPromise
from openforms.utils.expressions import FirstNotBlank

from ..models import Category, Form, FormDefinition, FormStep
from ..models.form import FormsExport
from ..utils import export_form
from .mixins import FormioConfigMixin
from .views import (
    DownloadExportedFormsView,
    ExportFormsForm,
    ExportFormsView,
    ImportFormsView,
    PaymentMigrationForm,
    PaymentMigrationView,
)


class FormStepInline(OrderedTabularInline):
    model = FormStep
    fk_name = "form"
    fields = (
        "order",
        "move_up_down_links",
        "form_definition",
        "previous_text",
        "save_text",
        "next_text",
    )
    readonly_fields = (
        "order",
        "move_up_down_links",
    )
    ordering = ("order",)
    extra = 1


class FormReachedSubmissionLimitListFilter(admin.SimpleListFilter):
    title = _("has reached submission limit")
    parameter_name = "submission_limit"

    def lookups(self, request, model_admin):
        return [
            ("available", _("Available for submission")),
            ("unavailable", _("Unavailable for submission")),
        ]

    def queryset(self, request, queryset):
        queryset = queryset.annotate(
            _submissions_limit_reached=Case(
                When(submission_limit__lte=F("submission_counter"), then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        if self.value() == "available":
            return queryset.filter(_submissions_limit_reached=False)
        elif self.value() == "unavailable":
            return queryset.filter(_submissions_limit_reached=True)


class FormDeletedListFilter(admin.ListFilter):
    title = _("is deleted")
    parameter_name = "deleted"

    def __init__(self, request, params, model, model_admin):
        super().__init__(request, params, model, model_admin)

        self.request = request

        if self.parameter_name in params:
            value = params.pop(self.parameter_name)
            self.used_parameters[self.parameter_name] = value

    def show_deleted(self):
        return self.used_parameters.get(self.parameter_name) == "deleted"

    def has_output(self):
        """
        This needs to return ``True`` to work.
        """
        return True

    def choices(self, changelist):
        result = [
            {
                "selected": not self.show_deleted(),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: "available"}
                ),
                "display": _("Available forms"),
            },
            {
                "selected": self.show_deleted(),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: "deleted"}
                ),
                "display": _("Deleted forms"),
            },
        ]
        return result

    def queryset(self, request, queryset):
        if self.show_deleted():
            return queryset.filter(_is_deleted=True)
        else:
            return queryset.filter(_is_deleted=False)

    def expected_parameters(self):
        return [self.parameter_name]


@admin.register(Form)
class FormAdmin(
    FormioConfigMixin,
    RegistrationBackendFieldMixin,
    OrderedInlineModelAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "anno_name",
        "is_live",
        "get_authentication_backends_display",
        "get_registration_backend_display",
        "get_object_actions",
    )
    prepopulated_fields = {"slug": ("name",)}
    actions = [
        "make_copies",
        "set_to_maintenance_mode",
        "remove_from_maintenance_mode",
        "export_forms",
        "migrate_to_worldline",
    ]
    list_filter = (
        "active",
        "maintenance_mode",
        "translation_enabled",
        FormDeletedListFilter,
        FormReachedSubmissionLimitListFilter,
    )
    search_fields = ("uuid", "name", "internal_name", "slug")

    change_list_template = "admin/forms/form/change_list.html"

    def changelist_view(self, request, extra_context=None):
        if request.GET.get("_async"):
            return self._async_changelist_view(request)

        # get the category tree and extra permission info for the custom import button
        extra_context = extra_context or {}
        categories_qs = Category.get_tree(parent=None).annotate(
            total_form_count=Count("form")
        )
        extra_context.update(
            {
                "categories": categories_qs,
                "has_change_permission": self.has_change_permission(request),
            }
        )
        # rely on the TemplateResponse not being rendered to alter the template
        # context
        response = super().changelist_view(request, extra_context)
        if not isinstance(response, TemplateResponse):
            return response

        changelist_instance = response.context_data.get("cl")
        if changelist_instance:
            changelist_queryset = changelist_instance.get_queryset(request)
            num_without_category = changelist_queryset.filter(
                category__isnull=True
            ).count()
            response.context_data.update(
                {
                    "total_count_no_category": self.get_queryset(request)
                    .filter(category__isnull=True)
                    .count(),
                    "count_no_category": num_without_category,
                    "result_headers": list(result_headers(changelist_instance)),
                    # apply filter context to count
                    "categories": categories_qs.annotate(
                        form_count=Count("form", filter=changelist_queryset.query.where)
                    ),
                }
            )

        return response

    @admin.options.csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if not extra_context:
            extra_context = {}

        # Give frontend access to proper field labels, to display in warning messages
        label_mapping = {
            underscore_to_camel(field.name): field.verbose_name
            for model in (self.model, FormStep, ConfirmationEmailTemplate)
            for field in model._meta.get_fields()
            if field.name in get_translatable_fields_for_model(model)
        }
        extra_context["label_mapping"] = label_mapping

        return super().changeform_view(
            request, object_id=object_id, form_url=form_url, extra_context=extra_context
        )

    def _async_changelist_view(self, request):
        # YOLO
        request.GET._mutable = True
        del request.GET["_async"]

        if request.GET["category"] == "":
            del request.GET["category"]
            request.GET["category__isnull"] = "1"

        opts = self.model._meta
        cl = self.get_changelist_instance(request)
        cl.formset = None
        context = {
            **self.admin_site.each_context(request),
            "module_name": str(opts.verbose_name_plural),
            "cl": cl,
            "opts": cl.opts,
        }

        return TemplateResponse(
            request,
            "admin/forms/form/category_form_list.html",
            context,
            headers={
                "X-Pagination-Count": cl.paginator.count,
                "X-Pagination-Pages": ",".join(
                    [str(p) for p in cl.paginator.page_range]
                ),
            },
        )

    def get_queryset(self, request):
        # annotate .name for ordering
        return (
            super()
            .get_queryset(request)
            .prefetch_related("category", "theme")
            .annotate(anno_name=FirstNotBlank("internal_name", "name"))
        )

    @admin.display(description=_("Actions"))
    def get_object_actions(self, obj: Form) -> str:
        links: list[tuple[str, StrOrPromise]] = []
        if obj.active:
            links.append((obj.get_absolute_url(), _("Show form")))
        return format_html_join(" | ", '<a href="{}" target="_blank">{}</a>', links)

    @admin.display(description=_("name"), ordering="anno_name")
    def anno_name(self, obj: Form) -> str:
        return obj.admin_name

    @admin.display(description=_("Live"), boolean=True)
    def is_live(self, obj: Form) -> bool:
        return obj.active and not obj._is_deleted

    def get_form(self, request, *args, **kwargs):
        # no actual changes to the fields are triggered, we're only ending up here
        # because of the copy/export actions.
        kwargs["fields"] = ()
        return super().get_form(request, *args, **kwargs)

    def get_prepopulated_fields(self, request, obj=None):
        return {}

    def response_post_save_change(self, request, obj):
        if "_copy" in request.POST:
            # Clear messages
            storage = messages.get_messages(request)
            for _msg in storage:
                pass

            copied_form = obj.copy()

            messages.success(
                request,
                _("{} {} was successfully copied").format("Form", obj),
            )
            return HttpResponseRedirect(
                reverse("admin:forms_form_change", args=(copied_form.pk,))
            )
        if "_export" in request.POST:
            # Clear messages
            storage = messages.get_messages(request)
            for _msg in storage:
                pass

            response = HttpResponse(content_type="application/zip")
            response["Content-Disposition"] = f"attachment;filename={obj.slug}.zip"
            export_form(obj.pk, response=response)

            response["Content-Length"] = len(response.content)

            self.message_user(
                request,
                _("{} {} was successfully exported").format("Form", obj),
                level=messages.SUCCESS,
            )
            return response
        else:
            return super().response_post_save_change(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "import/",
                self.admin_site.admin_view(ImportFormsView.as_view()),
                name="forms_import",
            ),
            path(
                "export/",
                self.admin_site.admin_view(ExportFormsView.as_view()),
                name="forms_export",
            ),
            path(
                "worldline-migrate/",
                self.admin_site.admin_view(PaymentMigrationView.as_view()),
                name="forms_payment_migration",
            ),
        ]
        return my_urls + urls

    @admin.action(description=_("Copy selected %(verbose_name_plural)s"))
    def make_copies(self, request, queryset):
        for instance in queryset:
            instance.copy()

        messages.success(
            request,
            ngettext(
                "Copied {count} {verbose_name} object.",
                "Copied {count} {verbose_name} objects.",
                len(queryset),
            ).format(
                count=len(queryset),
                verbose_name=queryset.model._meta.verbose_name,
            ),
        )

    @admin.action(
        description=_("Set selected %(verbose_name_plural)s to maintenance mode")
    )
    def set_to_maintenance_mode(self, request, queryset):
        count = queryset.filter(maintenance_mode=False).update(maintenance_mode=True)
        messages.success(
            request,
            ngettext(
                "Set {count} {verbose_name} object to maintenance mode",
                "Set {count} {verbose_name} objects to maintenance mode",
                count,
            ).format(
                count=count,
                verbose_name=queryset.model._meta.verbose_name,
            ),
        )

    @admin.action(description=_("Remove %(verbose_name_plural)s from maintenance mode"))
    def remove_from_maintenance_mode(self, request, queryset):
        count = queryset.filter(maintenance_mode=True).update(maintenance_mode=False)
        messages.success(
            request,
            ngettext(
                "Removed {count} {verbose_name} object from maintenance mode",
                "Removed {count} {verbose_name} objects from maintenance mode",
                count,
            ).format(
                count=count,
                verbose_name=queryset.model._meta.verbose_name,
            ),
        )

    @admin.action(description=_("Migrate form(s) to Worldline payment provider"))
    def migrate_to_worldline(self, request, queryset) -> TemplateResponse:
        form = PaymentMigrationForm(initial={"forms_to_migrate": queryset})
        context = {**self.admin_site.each_context(request), "form": form}
        return TemplateResponse(
            request, "admin/forms/form/migrate-payment-backend.html", context
        )

    def delete_model(self, request, form):
        """
        Check if we need to soft or hard delete.
        """
        if not form._is_deleted:
            # override for soft-delete
            form._is_deleted = True
            form.save(update_fields=["_is_deleted"])
        else:
            fds = list(
                FormDefinition.objects.filter(
                    formstep__form=form, is_reusable=False
                ).values_list("id", flat=True)
            )

            form.delete()
            FormDefinition.objects.filter(id__in=fds).delete()

    def delete_queryset(self, request, queryset):
        """
        Split between soft and hard deletes here.

        The admin has mutually exclusive filters, but let's not rely on that assumption.
        Hard deletes need to be performed first, otherwise non-deleted forms get
        soft-deleted and in the next steps _all_ (including the just created) soft-
        deletes get hard-deleted.
        """
        # hard deletes - ensure we cascade delete the single-use form definitions as well
        soft_deleted = queryset.filter(_is_deleted=True)
        fds = list(
            FormDefinition.objects.filter(
                formstep__form__in=soft_deleted, is_reusable=False
            ).values_list("id", flat=True)
        )
        soft_deleted.delete()
        FormDefinition.objects.filter(id__in=fds).delete()

        # soft-deletes
        queryset.filter(_is_deleted=False).update(_is_deleted=True)

    @admin.action(description=_("Export forms"))
    def export_forms(self, request, queryset):
        if not request.user.email:
            self.message_user(
                request=request,
                message=_(
                    "Please configure your email address in your admin profile before requesting a bulk export"
                ),
                level=messages.ERROR,
            )
            return

        selected_forms_uuids = queryset.values_list("uuid", flat=True)
        form = ExportFormsForm(
            initial={
                "forms_uuids": [str(form_uuid) for form_uuid in selected_forms_uuids],
            }
        )
        context = dict(self.admin_site.each_context(request), form=form)
        return TemplateResponse(request, "admin/forms/form/export.html", context)


@admin.register(FormsExport)
class FormsExportAdmin(admin.ModelAdmin):
    list_display = ("uuid", "user", "datetime_requested")
    list_filter = ("user",)
    search_fields = ("user__username",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                "download/<uuid:uuid>/",
                self.admin_site.admin_view(DownloadExportedFormsView.as_view()),
                name="download_forms_export",
            ),
        ]
        return my_urls + urls
