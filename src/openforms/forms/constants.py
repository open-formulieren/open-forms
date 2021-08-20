from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AvailabilityOptions(DjangoChoices):
    always = ChoiceItem("always", _("Always"))
    after_previous_step = ChoiceItem(
        "after_previous_step", _("If previous step is completed")
    )


class LogicActionTypes(DjangoChoices):
    disable_next = ChoiceItem("disable-next", _("Disable the next step"))
    property = ChoiceItem("property", _("Modify a component property"))
    value = ChoiceItem("value", _("Set the value of a component"))

    requires_component = {property, value}
