from django.db import models
from django.utils.translation import gettext_lazy as _


class JSONPrimitiveVariableTypes(models.TextChoices):
    string = "string", _("String")
    number = "number", _("Number")
    boolean = "boolean", _("Boolean")
    null = "null", _("Null")


class JSONComplexVariableTypes(models.TextChoices):
    object = "object", _("Object")
    array = "array", _("Array")


class JSONVariableTypes(models.TextChoices):
    object = "object", _("Object")
    array = "array", _("Array")
    string = "string", _("String")
    number = "number", _("Number")
    boolean = "boolean", _("Boolean")
    null = "null", _("Null")


class VariableSourceChoices(models.TextChoices):
    component = "component", _("Component")
    manual = "manual", _("Manual")
    interpolate = "interpolate", _("Interpolation")
