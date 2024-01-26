from django.conf import settings
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

    def get_initial_value(self, submission: Submission | None = None):
        return timezone.now()


@register_static_variable("today")
class Today(BaseStaticVariable):
    name = _("Today")
    data_type = FormVariableDataTypes.date

    def get_initial_value(self, submission: Submission | None = None) -> str:
        now_utc = timezone.now()
        return timezone.localtime(now_utc).date()


@register_static_variable("current_year")
class CurrentYear(BaseStaticVariable):
    name = _("Current year")
    data_type = FormVariableDataTypes.int

    def get_initial_value(self, submission: Submission | None = None) -> int:
        now_utc = timezone.now()
        return timezone.localtime(now_utc).year


@register_static_variable("environment")
class Environment(BaseStaticVariable):
    name = _("Environment")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return str(settings.ENVIRONMENT)


@register_static_variable("form_name")
class FormName(BaseStaticVariable):
    name = _("Form name")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return submission.form.name if submission else ""


@register_static_variable("form_id")
class FormID(BaseStaticVariable):
    name = _("Form ID")
    data_type = FormVariableDataTypes.string

    def get_initial_value(self, submission: Submission | None = None) -> str:
        return str(submission.form.uuid) if submission else ""
