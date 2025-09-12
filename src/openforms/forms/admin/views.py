import zipfile
from datetime import date
from uuid import uuid4

from django import forms
from django.contrib import messages
from django.contrib.admin.helpers import AdminField
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.forms import SimpleArrayField
from django.db import transaction
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import content_disposition_header
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import FormView

from import_export.formats.base_formats import XLSX
from privates.storages import private_media_storage
from rest_framework.exceptions import ValidationError

from openforms.logging import logevent
from openforms.payments.contrib.ogone.constants import OgoneEndpoints
from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.contrib.worldline.constants import WorldlineEndpoints
from openforms.payments.contrib.worldline.models import WorldlineMerchant

from ..forms import ExportStatisticsForm
from ..forms.form import FormImportForm
from ..models import Form, FormsExport, FormSubmissionStatistics
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
                import_form(import_file)
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

    def _bulk_import_forms(self, import_file):
        name = f"imports/import_forms_{uuid4()}.zip"
        filename = private_media_storage.save(name, import_file)

        process_forms_import.delay(filename, self.request.user.id)


@method_decorator(staff_member_required, name="dispatch")
class ExportSubmissionStatisticsView(
    LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    permission_required = "forms.view_formsubmissionstatistics"
    template_name = "admin/forms/formsubmissionstatistics/export_form.html"
    form_class = ExportStatisticsForm

    # must be set by the ModelAdmin
    media: forms.Media | None = None

    def form_valid(self, form: ExportStatisticsForm) -> HttpResponse:
        start_date: date = form.cleaned_data["start_date"]
        end_date: date = form.cleaned_data["end_date"]
        dataset = form.export()
        format = XLSX()
        filename = f"submissions_{start_date.isoformat()}_{end_date.isoformat()}.xlsx"
        return HttpResponse(
            format.export_data(dataset),
            content_type=format.get_content_type(),
            headers={
                "Content-Disposition": content_disposition_header(
                    as_attachment=True,
                    filename=filename,
                ),
            },
        )

    def get_context_data(self, **kwargs):
        assert self.media is not None, (
            "You must pass media=self.media in the model admin"
        )
        context = super().get_context_data(**kwargs)

        form = context["form"]

        def form_fields():
            for name in form.fields:
                yield AdminField(form, name, is_first=False)

        context.update(
            {
                "opts": FormSubmissionStatistics._meta,
                "media": self.media + form.media,
                "form_fields": form_fields,
            }
        )
        return context


class FormsField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.name


class PaymentMigrationForm(forms.Form):
    forms_to_migrate = FormsField(
        queryset=Form.objects.filter(payment_backend="ogone-legacy"),
        error_messages={
            "invalid_choice": _(
                "The selected form(s) cannot be migrated to the Worldline payment backend."
                " Please verify the selected forms have the ogone-legacy payment backend"
                " configured."
            ),
        },
        label=_("Forms"),
    )

    def clean(self) -> dict:
        cleaned_data = super().clean()
        forms_to_migrate = cleaned_data.get("forms_to_migrate", [])

        merchants: dict[int, Form] = {
            form.payment_backend_options["merchant_id"]: form
            for form in forms_to_migrate
            if "merchant_id" in form.payment_backend_options
        }

        found_merchants: dict[int, OgoneMerchant] = {
            merchant.pk: merchant
            for merchant in OgoneMerchant.objects.filter(id__in=list(merchants.keys()))
        }
        outdated_forms: list[Form] = []

        for merchant_id in merchants:
            if merchant_id not in found_merchants:
                outdated_forms.append(merchants[merchant_id])

        if outdated_forms:
            raise forms.ValidationError(
                _(
                    "The following forms reference a merchant that is non-existent: %s"
                    "Please select a new merchant for these forms."
                )
                % ",".join(str(form.uuid) for form in outdated_forms)
            )

        cleaned_data["merchant_mapping"] = {
            form.id: found_merchants[form.payment_backend_options["merchant_id"]]
            for form in forms_to_migrate
        }

        return cleaned_data

    def save(self, **kwargs) -> None:
        with transaction.atomic():
            for form in self.cleaned_data["forms_to_migrate"]:
                ogone_merchant = self.cleaned_data["merchant_mapping"][form.id]
                worldine_merchant, __ = WorldlineMerchant.objects.get_or_create(
                    pspid=ogone_merchant.pspid,
                )

                worldine_merchant.label = ogone_merchant.label
                worldine_merchant.endpoint = (
                    WorldlineEndpoints.live
                    if ogone_merchant.endpoint == OgoneEndpoints.live
                    else WorldlineEndpoints.test
                )
                worldine_merchant.api_key = ogone_merchant.api_key
                worldine_merchant.api_secret = ogone_merchant.api_secret
                worldine_merchant.save()

                form.payment_backend = "worldline"
                form.payment_backend_options = {"merchant": worldine_merchant.pspid}
                form.save()


class PaymentMigrationView(FormView):
    form_class = PaymentMigrationForm
    template_name = "admin/forms/form/migrate-payment-backend.html"
    success_url = reverse_lazy("admin:forms_form_changelist")

    def form_valid(self, form):
        form.save()

        messages.success(
            self.request,
            _("%s forms were migrated.") % len(form.cleaned_data["forms_to_migrate"]),
        )
        return super().form_valid(form)
