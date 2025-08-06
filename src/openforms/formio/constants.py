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
    "map": "object",
    "editgrid": "array",
    "datetime": "datetime",
    "partners": "array",
    "children": "array",
}


COMPONENT_DATA_SUBTYPES = {
    "file": "object",
    "editgrid": "editgrid",
    "partners": "partners",
    "children": "children",
}


class DataSrcOptions(StrEnum):
    manual = "manual"
    variable = "variable"
    reference_lists = "referenceLists"
