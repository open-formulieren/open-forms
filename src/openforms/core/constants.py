from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AvailabilityOptions(DjangoChoices):
    always = ChoiceItem("always", _("Always"))
    after_previous_step = ChoiceItem(
        "after_previous_step", _("If previous step is completed")
    )
