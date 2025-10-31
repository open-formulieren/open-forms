from django.db import models
from django.utils.translation import gettext_lazy as _


class DigitalAddressTypes(models.TextChoices):
    email = ("email", _("Email"))
    telefoonnummer = ("telefoonnummer", _("Telefoonnummer"))
    overig = ("overig", _("Overig"))


class Attributes(models.TextChoices):
    digital_addresses = ("digital_addresses", _("Digital addresses"))
