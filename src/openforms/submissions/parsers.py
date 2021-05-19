from djangorestframework_camel_case.parser import CamelCaseJSONParser


class IgnoreDataFieldCamelCaseJSONParser(CamelCaseJSONParser):
    json_underscoreize = {"ignore_fields": ("data",)}
