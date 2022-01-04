from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class JSONPrimitiveVariableTypes(DjangoChoices):
    string = ChoiceItem("string", _("String"))
    number = ChoiceItem("number", _("Number"))
    boolean = ChoiceItem("boolean", _("Boolean"))
    null = ChoiceItem("null", _("Null"))


class JSONComplexVariableTypes(DjangoChoices):
    object = ChoiceItem("object", _("Object"))
    array = ChoiceItem("array", _("Array"))


class JSONVariableTypes(JSONComplexVariableTypes, JSONPrimitiveVariableTypes):
    pass


class VariableSourceChoices(DjangoChoices):
    component = ChoiceItem("component", _("Component"))
    manual = ChoiceItem("manual", _("Manual"))
