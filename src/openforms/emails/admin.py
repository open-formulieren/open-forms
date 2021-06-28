from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from .connection_check import check_smtp_settings
from .forms import ConfirmationEmailTemplateForm, EmailTestForm
from .models import ConfirmationEmailTemplate


@admin.register(ConfirmationEmailTemplate)
class ConfirmationEmailTemplateAdmin(admin.ModelAdmin):
    form = ConfirmationEmailTemplateForm


class EmailTestAdminView(FormView):
    form_class = EmailTestForm
    template_name = "emails/admin_connection_check.html"
    title = _("Email connection test")

    def get_context_data(self, **kwargs):
        kwargs.setdefault("title", self.title)
        context = super().get_context_data(**kwargs)
        context.update(admin.site.each_context(self.request))
        return context

    def form_valid(self, form):
        recipient = form.cleaned_data["recipient"]
        result = check_smtp_settings([recipient])
        context = self.get_context_data(form=form, result=result)
        return self.render_to_response(context)
