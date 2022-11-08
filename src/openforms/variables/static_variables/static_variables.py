import datetime
from typing import Optional

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from openforms.submissions.models import Submission
from openforms.utils.date import get_date_in_current_timezone

from ..base import BaseStaticVariable
from ..constants import FormVariableDataTypes
from ..registry import register_static_variable


@register_static_variable("now")
class Now(BaseStaticVariable):
    name = _("Now")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, submission: Optional[Submission] = None) -> str:
        return timezone.now().isoformat()


@register_static_variable("today")
class Today(BaseStaticVariable):
    name = _("Today")
    data_type = FormVariableDataTypes.datetime

    def get_initial_value(self, submission: Optional[Submission] = None) -> str:
        naive_datetime = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return get_date_in_current_timezone(naive_datetime)


@register_static_variable("environment")
class Environment(BaseStaticVariable):
    name = _("Environment")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional[Submission] = None) -> str:
        return str(settings.ENVIRONMENT)


@register_static_variable("form_name")
class FormName(BaseStaticVariable):
    name = _("Form name")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional[Submission] = None) -> str:
        return submission.form.name if submission else ""


@register_static_variable("form_id")
class FormID(BaseStaticVariable):
    name = _("Form ID")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Optional[Submission] = None) -> str:
        return str(submission.form.uuid) if submission else ""
