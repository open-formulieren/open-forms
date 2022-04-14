from django import forms
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.forms import SimpleArrayField
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormView

from ..models.form import Form
from .tasks import process_forms_export


class FormsUUIDsForm(forms.Form):
    forms_uuids = SimpleArrayField(forms.UUIDField(), required=True)
    username = forms.CharField(max_length=150, required=True)


class ExportFormsForm(forms.Form):
    forms_uuids = SimpleArrayField(forms.UUIDField(), widget=forms.HiddenInput)
    username = forms.CharField(max_length=150, widget=forms.HiddenInput)
    email = forms.EmailField()

    def clean_forms_uuids(self):
        if not Form.objects.filter(uuid__in=self.cleaned_data["forms_uuids"]).exists():
            raise forms.ValidationError(_("Invalid form uuids."), code="invalid")
        return self.cleaned_data["forms_uuids"]


class ExportFormsView(SuccessMessageMixin, FormView):
    template_name = "admin/forms/form/export.html"
    form_class = ExportFormsForm
    success_url = reverse_lazy("admin:forms_form_changelist")
    success_message = _("Success! You will receive an email when your export is ready.")

    def get_initial(self):
        initial_data = super().get_initial()
        form = FormsUUIDsForm(
            data={
                "forms_uuids": self.request.GET.get("forms_uuids"),
                "username": self.request.user.username,
            }
        )
        if form.is_valid():
            initial_data.update(form.cleaned_data)
        return initial_data

    def form_valid(self, form):
        process_forms_export.delay(**form.cleaned_data)
        return super().form_valid(form)
