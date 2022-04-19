from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.forms import SimpleArrayField
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from openforms.logging import logevent

from ..models.form import Form, FormsExport
from .tasks import process_forms_export
from .tokens import exported_forms_token_generator


class ExportFormsForm(forms.Form):
    forms_uuids = SimpleArrayField(forms.UUIDField(), widget=forms.HiddenInput)
    email = forms.EmailField(widget=forms.HiddenInput)

    def clean_forms_uuids(self):
        if not Form.objects.filter(uuid__in=self.cleaned_data["forms_uuids"]).exists():
            raise forms.ValidationError(_("Invalid form uuids."), code="invalid")
        return self.cleaned_data["forms_uuids"]


class ExportFormsView(
    LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, FormView
):
    template_name = "admin/forms/form/export.html"
    form_class = ExportFormsForm
    success_url = reverse_lazy("admin:forms_form_changelist")
    success_message = _("Success! You will receive an email when your export is ready.")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        process_forms_export.delay(
            forms_uuids=form.cleaned_data["forms_uuids"],
            email=form.cleaned_data["email"],
            user_id=self.request.user.id,
        )
        return super().form_valid(form)


class DownloadExportedFormsView(LoginRequiredMixin, UserPassesTestMixin, View):
    model = FormsExport

    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        forms_export = get_object_or_404(
            FormsExport, pk=kwargs["pk"], user=request.user
        )

        token = kwargs["token"]
        valid = exported_forms_token_generator.check_token(forms_export, token)
        if not valid:
            raise PermissionDenied("URL is not valid")

        if request.user != forms_export.user:
            raise PermissionDenied("Wrong user requesting download")

        forms_export.datetime_downloaded = timezone.now()
        forms_export.save()

        logevent.forms_bulk_export_downloaded(forms_export, request.user)

        return FileResponse(open(forms_export.export_content.path, "rb"))
