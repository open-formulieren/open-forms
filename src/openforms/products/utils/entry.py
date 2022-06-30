import json

from .factory import FieldFactory


def convert_json_schema_to_py(json_schema: dict) -> dict:
    """
    reads json schema in json format and return dict of fields objects
    """
    final_result = {"components": []}
    properties = json_schema.get("properties", {})
    for key, content in properties.items():
        type_flag = content.get("type")
        if type_flag != "object":
            # check if attr "required" exists
            if json_schema.get("required") is not None:
                required = key in json_schema.get("required")
            else:
                required = None
            single_field = FieldFactory.create(key, required=required, content=content)
        else:
            single_field = FieldFactory.create(key, content=content)
        elem = json.dumps(single_field.dict_repr)
        final_result["components"].append(json.loads(elem))

    return final_result
