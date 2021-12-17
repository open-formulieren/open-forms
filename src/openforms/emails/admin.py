from django.contrib import admin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from ..utils.mixins import UserIsStaffMixin
from .connection_check import check_email_backend
from .forms import ConfirmationEmailTemplateForm, EmailTestForm
from .models import ConfirmationEmailTemplate


@admin.register(ConfirmationEmailTemplate)
class ConfirmationEmailTemplateAdmin(admin.ModelAdmin):
    form = ConfirmationEmailTemplateForm


class EmailTestAdminView(UserIsStaffMixin, PermissionRequiredMixin, FormView):
    form_class = EmailTestForm
    template_name = "admin/emails/connection_check.html"
    title = _("Email connection test")
    permission_required = [
        "accounts.email_backend_test",
    ]

    def get_context_data(self, **kwargs):
        kwargs.setdefault("title", self.title)
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context

    def form_valid(self, form):
        recipient = form.cleaned_data["recipient"]
        result = check_email_backend([recipient])
        context = self.get_context_data(form=form, result=result)
        return self.render_to_response(context)
