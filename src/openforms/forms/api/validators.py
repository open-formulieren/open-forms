from openforms.utils.json_logic import JsonLogicTest


class JsonLogicValidator:
    """Validates that a json object is a valid jsonLogic expression"""

    def __call__(self, value: dict):
        JsonLogicTest.is_valid(value, raise_exception=True)
