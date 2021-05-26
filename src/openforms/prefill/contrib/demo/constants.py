from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class Attributes(DjangoChoices):
    random_number = ChoiceItem("random_number", _("Random number"))
    random_string = ChoiceItem("random_string", _("Random string"))
