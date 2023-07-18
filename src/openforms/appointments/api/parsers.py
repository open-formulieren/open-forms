from djangorestframework_camel_case.parser import CamelCaseJSONParser


class AppointmentCreateCamelCaseJSONParser(CamelCaseJSONParser):
    json_underscoreize = {"ignore_fields": ("contact_details",)}
