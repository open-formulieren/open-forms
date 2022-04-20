import os
import zipfile
from pathlib import Path
from uuid import uuid4

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.forms import SimpleArrayField
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from rest_framework.exceptions import ValidationError

from openforms.logging import logevent

from ..forms.form import FormImportForm
from ..models.form import Form, FormsExport
from ..utils import import_form
from .tasks import process_forms_export, process_forms_import


class ExportFormsForm(forms.Form):
    forms_uuids = SimpleArrayField(forms.UUIDField(), widget=forms.HiddenInput)

    def clean_forms_uuids(self):
        if not Form.objects.filter(uuid__in=self.cleaned_data["forms_uuids"]).exists():
            raise forms.ValidationError(_("Invalid form uuids."), code="invalid")
        return self.cleaned_data["forms_uuids"]


class ExportImportPermissionMixin(LoginRequiredMixin, PermissionRequiredMixin):
    pass


class ExportFormsView(ExportImportPermissionMixin, SuccessMessageMixin, FormView):
    template_name = "admin/forms/form/export.html"
    form_class = ExportFormsForm
    permission_required = "forms.add_formsexport"
    success_url = reverse_lazy("admin:forms_form_changelist")
    success_message = _("Success! You will receive an email when your export is ready.")

    def form_valid(self, form):
        process_forms_export.delay(
            forms_uuids=form.cleaned_data["forms_uuids"],
            user_id=self.request.user.id,
        )
        return super().form_valid(form)


class DownloadExportedFormsView(ExportImportPermissionMixin, View):
    permission_required = "forms.view_formsexport"

    def get(self, request, *args, **kwargs):
        forms_export = get_object_or_404(
            FormsExport, uuid=kwargs["uuid"], user=request.user
        )

        logevent.forms_bulk_export_downloaded(forms_export, request.user)

        return FileResponse(open(forms_export.export_content.path, "rb"))


class ImportFormsView(ExportImportPermissionMixin, SuccessMessageMixin, FormView):
    template_name = "admin/forms/form/import_form.html"
    form_class = FormImportForm
    permission_required = "forms.add_form"
    success_url = reverse_lazy("admin:forms_form_changelist")

    def get_is_bulk_import(self, import_file):
        with zipfile.ZipFile(import_file, "r") as file:
            names_list = file.namelist()
        return all([name.endswith(".zip") for name in names_list])

    def form_valid(self, form):
        import_file = form.cleaned_data["file"]
        is_bulk_import = self.get_is_bulk_import(import_file)

        if not is_bulk_import:
            try:
                self._import_single_form(import_file)
            except ValidationError as exc:
                messages.error(
                    self.request,
                    _("Something went wrong while importing form: {}").format(exc),
                )
                return super().form_invalid(form)
        else:
            self._bulk_import_forms(import_file)

        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        import_file = cleaned_data["file"]
        is_bulk_import = self.get_is_bulk_import(import_file)

        if not is_bulk_import:
            return _("Form successfully imported!")
        return _(
            "The bulk import is being processed! The imported forms will soon be available."
        )

    def _import_single_form(self, import_file):
        created_fds = import_form(import_file)
        if created_fds:
            messages.warning(
                self.request,
                _("Form definitions were created with the following slugs: {}").format(
                    created_fds
                ),
            )

    def _bulk_import_forms(self, import_file):
        imports_dir = Path(settings.PRIVATE_MEDIA_ROOT, "imports")
        if not imports_dir.exists():
            os.mkdir(imports_dir)
        imports_file = Path(imports_dir, f"import_forms_{uuid4()}.zip")
        with open(imports_file, "wb") as f_private:
            for chunk in import_file.chunks():
                f_private.write(chunk)

        process_forms_import.delay(str(imports_file), self.request.user.id)
