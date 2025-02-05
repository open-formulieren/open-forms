from enum import StrEnum

COMPONENT_DATATYPES = {
    "date": "date",
    "time": "time",
    "file": "array",
    "currency": "float",
    "number": "float",
    "checkbox": "boolean",
    "selectboxes": "object",
    "npFamilyMembers": "object",
    "map": "array",
    "editgrid": "array",
    "datetime": "datetime",
}


class DataSrcOptions(StrEnum):
    manual = "manual"
    variable = "variable"
    referentielijsten = "referentielijsten"
