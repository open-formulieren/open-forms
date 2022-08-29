from typing import Optional

from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission

from ..base import BaseStaticVariable
from ..constants import FormVariableDataTypes
from ..registry import register_static_variable


@register_static_variable("now")
class Now(BaseStaticVariable):
    name = _("Now")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, submission: Optional[Submission] = None):
        return timezone.now()
