from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class LogicActionTypes(DjangoChoices):
    step_not_applicable = ChoiceItem(
        "step-not-applicable", _("Mark the form step as not-applicable")
    )
    disable_next = ChoiceItem("disable-next", _("Disable the next step"))
    property = ChoiceItem("property", _("Modify a component property"))
    value = ChoiceItem("value", _("Set the value of a component"))

    requires_component = {property, value}


class PropertyTypes(DjangoChoices):
    bool = ChoiceItem("bool", _("Boolean"))
    json = ChoiceItem("json", _("JSON"))
