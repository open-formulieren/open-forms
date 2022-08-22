from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.variables.constants import FormVariableDataTypes

from ..base import BaseStaticVariable
from ..registry import register_static_variable


@register_static_variable("now")
class Now(BaseStaticVariable):
    name = _("Now")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, *args, **kwargs):
        return timezone.now()
