from .factory import FieldFactory


def convert_json_schema_to_py(json_schema: dict) -> dict:
    """
    reads json schema  and return dict of formio objects
    """
    final_result = {"components": []}
    properties = json_schema.get("properties", {})
    for key, content in properties.items():
        required = key in json_schema.get("required", [])
        single_field = FieldFactory.create(key, required, content)
        final_result["components"].append(single_field.render())

    return final_result
