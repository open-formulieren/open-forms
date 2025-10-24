from django.db import models
from django.utils.translation import gettext_lazy as _


class DigitalAddressTypes(models.TextChoices):
    email = ("email", _("Email"))
    telefoonnummer = ("telefoonnummer", _("Telefoonnummer"))
    overig = ("overig", _("Overig"))


class Attributes(models.TextChoices):
    email = ("email", _("email"))
    email_preferred = ("email_preferred", _("email preferred"))
    phone = ("phone", _("phone"))
    phone_preferred = ("phone_preferred", _("phone preferred"))
