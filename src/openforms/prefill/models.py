from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from solo.models import SingletonModel

from openforms.authentication.service import AuthAttribute

from .fields import PrefillPluginChoiceField


class PrefillConfig(SingletonModel):
    default_person_plugin = PrefillPluginChoiceField(
        _("default person plugin"),
        auth_attribute=AuthAttribute.bsn,
        help_text=_("Default prefill plugin to use for person data"),
    )
    default_company_plugin = PrefillPluginChoiceField(
        _("default company plugin"),
        auth_attribute=AuthAttribute.kvk,
        help_text=_("Default prefill plugin to use for company data"),
    )

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        verbose_name = _("global prefill configuration")

    def __str__(self):
        return force_str(self._meta.verbose_name)
