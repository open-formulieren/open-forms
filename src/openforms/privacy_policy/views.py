from django.utils.safestring import mark_safe
from django.views.generic.base import TemplateView

from openforms.config.models import GlobalConfiguration
from openforms.emails.utils import sanitize_content


class PrivacyPolicyView(TemplateView):

    template_name = "privacy_policy.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        config = GlobalConfiguration.get_solo()
        sanitized = sanitize_content(config.privacy_policy_content)
        context["body"] = mark_safe(sanitized)
        return context
