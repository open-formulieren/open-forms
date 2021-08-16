from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Domain(models.Model):
    name = models.CharField(
        _("name"),
        max_length=100,
        help_text=_("The name to show in the domain switcher."),
    )
    url = models.URLField(
        _("url"),
        help_text=_(
            "The absolute URL to redirect to. Typically this starts the login process on the other domain. "
            "For example: https://open-forms.example.com/oidc/authenticate/ or "
            "https://open-forms.example.com/admin/login/"
        ),
    )
    is_current = models.BooleanField(
        _("current"),
        help_text=_(
            "Select this to show this domain as the current domain. The current domain is selected by default and "
            "will not trigger a redirect."
        ),
    )

    class Meta:
        verbose_name = _("domain")
        verbose_name_plural = _("domains")

    def __str__(self):
        return self.name
