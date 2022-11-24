from django.utils.translation import gettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices

from .utils import check_date, check_time


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
    date = ChoiceItem("date", _("Date"))


DEFAULT_INITIAL_VALUE = {
    FormVariableDataTypes.string: "",
    FormVariableDataTypes.boolean: False,
    FormVariableDataTypes.object: {},
    FormVariableDataTypes.array: [],
    FormVariableDataTypes.int: None,
    FormVariableDataTypes.float: None,
    FormVariableDataTypes.datetime: "",
    FormVariableDataTypes.date: "",
    FormVariableDataTypes.time: "",
}

CHECK_VARIABLE_TYPE = {
    FormVariableDataTypes.string: str,
    FormVariableDataTypes.boolean: bool,
    FormVariableDataTypes.object: dict,
    FormVariableDataTypes.array: list,
    FormVariableDataTypes.int: int,
    FormVariableDataTypes.float: float,
    FormVariableDataTypes.datetime: check_date,
    FormVariableDataTypes.date: check_date,
    FormVariableDataTypes.time: check_time,
}
