from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class LogicActionTypes(DjangoChoices):
    step_not_applicable = ChoiceItem(
        "step-not-applicable", _("Mark the form step as not-applicable")
    )
    disable_next = ChoiceItem("disable-next", _("Disable the next step"))
    property = ChoiceItem("property", _("Modify a component property"))
    value = ChoiceItem("value", _("Set the value of a component"))

    requires_component = {property.value, value.value}


class PropertyTypes(DjangoChoices):
    bool = ChoiceItem("bool", _("Boolean"))
    json = ChoiceItem("json", _("JSON"))


class ConfirmationEmailOptions(DjangoChoices):
    form_specific_email = ChoiceItem("form_specific_email", _("Form specific email"))
    global_email = ChoiceItem("global_email", _("Global email"))
    no_email = ChoiceItem("no_email", _("No email"))


class SubmissionAllowedChoices(DjangoChoices):
    yes = ChoiceItem("yes", _("Yes"))
    no_with_overview = ChoiceItem("no_with_overview", _("No (with overview page)"))
    no_without_overview = ChoiceItem(
        "no_without_overview", _("No (without overview page)")
    )
