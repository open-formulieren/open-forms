from collections.abc import Set

from django.db import models
from django.utils.translation import gettext_lazy as _

EXPORT_META_KEY = "_meta"


class LogicActionTypes(models.TextChoices):
    step_not_applicable = (
        "step-not-applicable",
        _("Mark the form step as not-applicable"),
    )
    step_applicable = "step-applicable", _("Mark the form step as applicable")
    disable_next = "disable-next", _("Disable the next step")
    property = "property", _("Modify a component property")
    variable = "variable", _("Set the value of a variable")
    fetch_from_service = "fetch-from-service", _("Fetch the value from a service")
    set_registration_backend = (
        "set-registration-backend",
        _("Set the registration backend to use for the submission"),
    )
    evaluate_dmn = "evaluate-dmn", _("Evaluate DMN")
    synchronize_variables = (
        "synchronize-variables",
        _("Synchronize a variable with another one"),
    )

    @classmethod
    def get_label(cls, value: str) -> str:
        return dict(cls.choices)[value]


LOGIC_ACTION_TYPES_REQUIRING_COMPONENT: Set[str] = {LogicActionTypes.property.value}
LOGIC_ACTION_TYPES_REQUIRING_VARIABLE: Set[str] = {LogicActionTypes.variable.value}


class PropertyTypes(models.TextChoices):
    bool = "bool", _("Boolean")
    json = "json", _("JSON")


class ConfirmationEmailOptions(models.TextChoices):
    form_specific_email = "form_specific_email", _("Form specific email")
    global_email = "global_email", _("Global email")
    no_email = "no_email", _("No email")


class SubmissionAllowedChoices(models.TextChoices):
    yes = "yes", _("Yes")
    no_with_overview = "no_with_overview", _("No (with overview page)")
    no_without_overview = "no_without_overview", _("No (without overview page)")


class StatementCheckboxChoices(models.TextChoices):
    global_setting = "global_setting", _("Global setting")
    required = "required", _("Required")
    disabled = "disabled", _("Disabled")
