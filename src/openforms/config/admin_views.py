from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView

from openforms.utils.mixins import UserIsStaffMixin

from .forms import ThemePreviewAdminForm
from .models import Theme


class ThemePreviewView(UserIsStaffMixin, PermissionRequiredMixin, FormView):
    permission_required = "config.view_theme"
    form_class = ThemePreviewAdminForm
    template_name = "admin/config/theme/preview.html"

    def form_valid(self, form):
        return redirect(
            "forms:theme-preview",
            theme_pk=self.kwargs["object_id"],
            slug=form.cleaned_data["form"].slug,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["theme"] = get_object_or_404(Theme, pk=self.kwargs["object_id"])
        return context
