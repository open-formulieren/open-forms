from openforms.utils.jsonschema.convert import to_jsonschema


class JsonSchemaSerializerMixin:
    @classmethod
    def display_as_jsonschema(cls):
        json_schema = to_jsonschema(cls())
        return json_schema
