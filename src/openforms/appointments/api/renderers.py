from djangorestframework_camel_case.render import CamelCaseJSONRenderer


class AppointmentCreateJSONRenderer(CamelCaseJSONRenderer):
    json_underscoreize = {"ignore_fields": ("contact_details",)}
