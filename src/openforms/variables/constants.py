from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class FormVariableSources(DjangoChoices):
    component = ChoiceItem("component", _("Component"))
    user_defined = ChoiceItem("user_defined", _("User defined"))


class FormVariableDataTypes(DjangoChoices):
    string = ChoiceItem("string", _("String"))
    boolean = ChoiceItem("boolean", _("Boolean"))
    object = ChoiceItem("object", _("Object"))
    array = ChoiceItem("array", _("Array"))
    int = ChoiceItem("int", _("Integer"))
    float = ChoiceItem("float", _("Float"))
    datetime = ChoiceItem("datetime", _("Datetime"))
    time = ChoiceItem("time", _("Time"))
