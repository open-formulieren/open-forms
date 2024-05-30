from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class IgnoreDataAndConfigFieldCamelCaseJSONParser(CamelCaseJSONParser):
    json_underscoreize = {"ignore_fields": ("data", "configuration")}


class IgnoreValueFieldCamelCaseJSONParser(CamelCaseJSONParser):
    json_underscoreize = {"ignore_fields": ("value",)}


class IgnoreDataAndConfigJSONRenderer(CamelCaseJSONRenderer):
    # This is needed for fields in the submission step data that have keys with underscores
    json_underscoreize = {"ignore_fields": ("data", "configuration")}
