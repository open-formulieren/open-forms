from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class IgnoreDataFieldCamelCaseJSONParser(CamelCaseJSONParser):
    json_underscoreize = {"ignore_fields": ("data",)}


class IgnoreDataJSONRenderer(CamelCaseJSONRenderer):
    # This is needed for fields in the submission step data that have keys with underscores
    json_underscoreize = {"ignore_fields": ("data",)}
