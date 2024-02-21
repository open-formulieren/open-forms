from django.db import models
from django.utils.translation import gettext_lazy as _


class DMNTypes(models.TextChoices):
    string = "string", _("string")
    integer = "integer", _("integer")
    long = "long", _("long")
    boolean = "boolean", _("boolean")
    date = "date", _("date")
    double = "double", _("double")
