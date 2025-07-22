from django.db import models
from django.utils.translation import gettext_lazy as _

from openforms.typing import JSONObject

from .utils import check_date, check_time


class FormVariableSources(models.TextChoices):
    component = "component", _("Component")
    user_defined = "user_defined", _("User defined")


class FormVariableDataTypes(models.TextChoices):
    string = "string", _("String")
    boolean = "boolean", _("Boolean")
    object = "object", _("Object")
    array = "array", _("Array")
    int = "int", _("Integer")
    float = "float", _("Float")
    datetime = "datetime", _("Datetime")
    time = "time", _("Time")
    date = "date", _("Date")
    # This should only be used as a data subtype, and is a work-around to enable
    # converting the partners submission data to native Python types
    partners = "partners", _("Partners")


class ServiceFetchMethods(models.TextChoices):
    get = "GET", "GET"
    post = "POST", "POST"


class DataMappingTypes(models.TextChoices):
    json_logic = "JsonLogic", "JsonLogic"
    jq = "jq", "jq"


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


DATA_TYPE_TO_JSON_SCHEMA: dict[str, JSONObject] = {
    FormVariableDataTypes.string: {"type": "string"},
    FormVariableDataTypes.boolean: {"type": "boolean"},
    FormVariableDataTypes.object: {"type": "object"},
    FormVariableDataTypes.array: {"type": "array"},
    FormVariableDataTypes.int: {"type": "integer"},
    FormVariableDataTypes.float: {"type": "number"},
    FormVariableDataTypes.datetime: {"type": "string", "format": "date-time"},
    FormVariableDataTypes.date: {"type": "string", "format": "date"},
    FormVariableDataTypes.time: {"type": "string", "format": "time"},
}
