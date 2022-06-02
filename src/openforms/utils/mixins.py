from django.contrib.auth.mixins import UserPassesTestMixin

from drf_jsonschema import to_jsonschema

from openforms.api.utils import underscore_to_camel


def _camelize_required(schema: dict):
    """
    Camelize the `required` field names, which are not picked up by drf camel case.
    """
    new = {**schema}
    # recurse
    for key, value in schema.items():
        if isinstance(value, list):
            new[key] = [
                _camelize_required(nested) if isinstance(nested, dict) else nested
                for nested in value
            ]
        elif isinstance(value, dict):
            new[key] = _camelize_required(value)

    # does it look like a proper schema?
    if "type" in schema and "properties" in schema:
        if required := schema.get("required"):
            assert isinstance(required, list)
            new["required"] = [underscore_to_camel(field) for field in required]

    return new


class JsonSchemaSerializerMixin:
    @classmethod
    def display_as_jsonschema(cls):
        json_schema = to_jsonschema(cls())
        json_schema = _camelize_required(json_schema)
        return json_schema


class UserIsStaffMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff
