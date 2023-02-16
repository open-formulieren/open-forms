from django.db import models
from django.utils.translation import gettext_lazy as _


class Attributes(models.TextChoices):
    random_number = "random_number", _("Random number")
    random_string = "random_string", _("Random string")
