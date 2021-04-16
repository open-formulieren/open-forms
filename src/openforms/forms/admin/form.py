from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.management import CommandError, call_command
from django.db.utils import DataError, IntegrityError
from django.http.response import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import ugettext_lazy as _

from ordered_model.admin import OrderedInlineModelAdminMixin, OrderedTabularInline

from ..backends import registry
from ..forms.form import FormImportForm
from ..models import Form, FormStep
from ..utils import copy_form


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
    change_list_template = "admin/forms/form_change_list.html"

    def response_post_save_change(self, request, obj):
        if "_copy" in request.POST:
            # Clear messages
            storage = messages.get_messages(request)
            for i in storage:
                pass

            try:
                copied_form = copy_form(obj)
            except (DataError, IntegrityError) as e:
                messages.error(request, _("Error occurred while copying: {}").format(e))
                return HttpResponseRedirect(
                    reverse("admin:forms_form_change", args=(obj.pk,))
                )

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
            response["Content-Disposition"] = "attachment;filename={}".format(
                f"{obj.slug}.zip"
            )
            call_command(
                "export",
                response=response,
                form_id=obj.pk,
            )

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

        form = FormImportForm(request.POST, request.FILES)
        context = dict(self.admin_site.each_context(request), form=form)
        if "_import" in request.POST:
            form = FormImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    import_file = form.cleaned_data["file"]
                    call_command(
                        "import",
                        import_file_content=import_file.read(),
                    )
                    self.message_user(
                        request,
                        _("Catalogus successfully imported"),
                        level=messages.SUCCESS,
                    )
                    return HttpResponseRedirect(reverse("admin:forms_form_changelist"))
                except CommandError as exc:
                    self.message_user(request, exc, level=messages.ERROR)
        else:
            form = FormImportForm()

        context = dict(self.admin_site.each_context(request), form=form)

        return TemplateResponse(request, "admin/forms/import_form.html", context)

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
