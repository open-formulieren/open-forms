import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView

from openforms.config.models import GlobalConfiguration, Theme
from openforms.config.templatetags.theme import THEME_OVERRIDE_CONTEXT_VAR
from openforms.utils.decorators import conditional_search_engine_index
from openforms.utils.mixins import UserIsStaffMixin

from ..models import Form

logger = logging.getLogger(__name__)


class FormListView(ListView):
    template_name = "forms/form_list.html"
    queryset = Form.objects.live()
    extra_context = {
        "title": Form._meta.verbose_name_plural,
    }

    def get(self, request, *args, **kwargs):
        config = GlobalConfiguration.get_solo()

        if request.user.is_staff:
            return super().get(request, *args, **kwargs)
        elif not config.main_website:
            raise PermissionDenied()
        else:
            # looks like an "open redirect", but admins control the value of this and
            # we only give access to trusted users to the admin.
            return HttpResponseRedirect(config.main_website)


@method_decorator(
    conditional_search_engine_index(config_attr="allow_indexing_form_detail"),
    name="dispatch",
)
class FormDetailView(DetailView):
    template_name = "forms/form_detail.html"
    queryset = Form.objects.select_related("theme").live()

    object: Form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[THEME_OVERRIDE_CONTEXT_VAR] = self.object.theme
        return context


class ThemePreviewFormView(UserIsStaffMixin, DetailView):
    template_name = "forms/form_detail.html"
    queryset = Form.objects.filter(_is_deleted=False)
    raise_exception = True

    def get(self, request, *args, **kwargs):
        self.theme = get_object_or_404(Theme, pk=kwargs["theme_pk"])
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[THEME_OVERRIDE_CONTEXT_VAR] = self.theme
        context["base_path"] = reverse(
            "forms:theme-preview",
            kwargs={"theme_pk": self.theme.pk, "slug": self.object.slug},
        )
        return context
