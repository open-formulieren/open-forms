from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import ngettext, ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline
from rest_framework.exceptions import ValidationError

from openforms.config.models import GlobalConfiguration
from openforms.registrations.admin import RegistrationBackendFieldMixin

from ...payments.admin import PaymentBackendChoiceFieldMixin
from ...utils.expressions import FirstNotBlank
from ..forms.form import FormImportForm
from ..models import Form, FormStep
from ..utils import export_form, import_form


class FormStepInline(OrderedTabularInline):
    model = FormStep
    fk_name = "form"
    fields = (
        "order",
        "move_up_down_links",
        "form_definition",
        "optional",
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


@admin.register(Form)
class FormAdmin(
    RegistrationBackendFieldMixin,
    PaymentBackendChoiceFieldMixin,
    OrderedInlineModelAdminMixin,
    admin.ModelAdmin,
):
    list_display = (
        "anno_name",
        "active",
        "maintenance_mode",
        "get_authentication_backends_display",
        "get_payment_backend_display",
        "get_registration_backend_display",
    )
    inlines = (FormStepInline,)
    prepopulated_fields = {"slug": ("name",)}
    actions = ["make_copies", "set_to_maintenance_mode", "remove_from_maintenance_mode"]
    list_filter = ("active", "maintenance_mode")
    search_fields = ("name", "internal_name")

    change_list_template = "admin/forms/form/change_list.html"

    def use_react(self, request):
        if not hasattr(request, "_use_react_form_crud"):
            config = GlobalConfiguration.get_solo()
            request._use_react_form_crud = config.enable_react_form
        return request._use_react_form_crud

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        context.update({"use_react": self.use_react(request)})
        return super().render_change_form(request, context, add, change, form_url, obj)

    def changelist_view(self, request, extra_context=None):
        context = {
            "has_change_permission": self.has_change_permission(request),
        }
        context.update(extra_context or {})
        return super().changelist_view(request, context)

    def get_queryset(self, request):
        # annotate .name
        return (
            super()
            .get_queryset(request)
            .annotate(anno_name=FirstNotBlank("internal_name", "name"))
        )

    def anno_name(self, obj):
        return obj.admin_name

    anno_name.admin_order_field = "anno_name"
    anno_name.short_description = _("name")

    def get_inline_instances(self, request, *args, **kwargs):
        if self.use_react(request):
            return []
        return super().get_inline_instances(request, *args, **kwargs)

    def get_form(self, request, *args, **kwargs):
        if self.use_react(request):
            # no actual changes to the fields are triggered, we're only ending up here
            # because of the copy/export actions.
            kwargs["fields"] = ()
        return super().get_form(request, *args, **kwargs)

    def get_prepopulated_fields(self, request, obj=None):
        if self.use_react(request):
            return {}
        return super().get_prepopulated_fields(request, obj=obj)

    def response_post_save_change(self, request, obj):
        if "_copy" in request.POST:
            # Clear messages
            storage = messages.get_messages(request)
            for i in storage:
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
            for i in storage:
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
                self.admin_site.admin_view(self.import_view),
                name="forms_import",
            )
        ]
        return my_urls + urls

    def import_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        if "_import" in request.POST:
            form = FormImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    import_file = form.cleaned_data["file"]
                    created_fds = import_form(import_file)
                    if created_fds:
                        self.message_user(
                            request,
                            _(
                                "Form definitions were created with the following slugs: {}"
                            ).format(created_fds),
                            level=messages.WARNING,
                        )
                    self.message_user(
                        request,
                        _("Form successfully imported"),
                        level=messages.SUCCESS,
                    )
                    return HttpResponseRedirect(reverse("admin:forms_form_changelist"))
                except ValidationError as exc:
                    self.message_user(
                        request,
                        _("Something went wrong while importing form: {}").format(exc),
                        level=messages.ERROR,
                    )
        else:
            form = FormImportForm()

        context = dict(self.admin_site.each_context(request), form=form)

        return TemplateResponse(request, "admin/forms/form/import_form.html", context)

    def make_copies(self, request, queryset):
        for instance in queryset:
            instance.copy()

        messages.success(
            request,
            ngettext(
                "Copied {count} {verbose_name}",
                "Copied {count} {verbose_name_plural}",
                len(queryset),
            ).format(
                count=len(queryset),
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )

    make_copies.short_description = _("Copy selected %(verbose_name_plural)s")

    def set_to_maintenance_mode(self, request, queryset):
        count = queryset.filter(maintenance_mode=False).update(maintenance_mode=True)
        messages.success(
            request,
            ngettext(
                "Set {count} {verbose_name} to maintenance mode",
                "Set {count} {verbose_name_plural} to maintenance mode",
                count,
            ).format(
                count=count,
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )

    set_to_maintenance_mode.short_description = _(
        "Set selected %(verbose_name_plural)s to maintenance mode"
    )

    def remove_from_maintenance_mode(self, request, queryset):
        count = queryset.filter(maintenance_mode=True).update(maintenance_mode=False)
        messages.success(
            request,
            ngettext(
                "Removed {count} {verbose_name} from maintenance mode",
                "Removed {count} {verbose_name_plural} from maintenance mode",
                count,
            ).format(
                count=count,
                verbose_name=queryset.model._meta.verbose_name,
                verbose_name_plural=queryset.model._meta.verbose_name_plural,
            ),
        )

    remove_from_maintenance_mode.short_description = _(
        "Remove %(verbose_name_plural)s from maintenance mode"
    )
