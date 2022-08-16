from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.forms.constants import FormVariableDataTypes

from ..base import BaseStaticVariable
from ..registry import static_variables_register


@static_variables_register("now")
class Now(BaseStaticVariable):
    name = _("Now")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, *args, **kwargs):
        return timezone.now().isoformat()
