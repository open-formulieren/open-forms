from copy import deepcopy


class BaseField:
    template = {
        "label": "",
        "tableView": None,
        "validate": {},
        "key": "",
        "type": "",
        "input": None,
    }

    def __init__(self, key):
        self.instance = deepcopy(self.template)
        self.instance["key"] = key

    def render(self):
        return self.instance


class Field(BaseField):
    """parent class with basic attributes for a single field(form io)"""

    input = True

    def __init__(self, key: str, required: bool, content: dict) -> None:
        super().__init__(key)
        self.instance.update(
            {
                "description": content.get("description"),
                "defaultValue": content.get("default"),
                "input": self.input,
                "label": content.get("title"),
                "type": self.type,
            }
        )

        self.instance["validate"] = {
            "required": required,
            "pattern": content.get("pattern"),
        }


class FieldSetBase(BaseField):
    """parent class with basic attributes for a fieldset(form io) OR panel (form io) -currently NOT implemented"""

    input = False

    def __init__(self, key: str):
        super().__init__(key)
        self.instance.update({"input": self.input, "type": self.type})


class FieldSet(FieldSetBase):

    label = "Field Set"
    type = "fieldset"

    def __init__(self, key: str, required: bool, content: dict) -> None:
        from .entry import convert_json_schema_to_py

        super().__init__(key)
        self.components = convert_json_schema_to_py(content)["components"]
        self.instance.update({"label": self.label, "components": self.components})


class TextField(Field):
    type = "textfield"

    def __init__(self, key: str, required: bool, content: dict) -> None:
        super().__init__(key, required, content)
        self.instance["validate"].update(
            {
                "maxLength": content.get("maxLength"),
                "minLength": content.get("minLength"),
            }
        )

    def render(self):
        return self.instance


class TextAreaField(Field):
    type = "textarea"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)

        self.instance["validate"].update(
            {
                "minWords": None,
                "maxWords": None,
            }
        )


class DateField(Field):
    type = "date"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class TimeField(Field):
    type = "time"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class DateTimeField(Field):
    type = "datetime"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class EmailField(Field):
    type = "email"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class NumberField(Field):
    type = "number"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)

        self.instance["validate"].update(
            {
                "max": content.get("maximum"),
                "min": content.get("minimum"),
                "step": "any",
            }
        )

        is_int = content.get("type")
        if is_int == "integer":
            self.instance["decimalLimit"] = 0


class SelectBoxesField(Field):
    # note: extension of Radio component
    type = "selectboxes"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)
        self.intance["validate"].update(
            {
                "onlyAvailableItems": None,
                # "minSelectedCount": None,
                # "maxSelectedCount": None,
            }
        )


class RadioField(Field):
    type = "radio"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)

        self.intsance["validate"].update(
            {
                "onlyAvailableItems": False,
            }
        )


class SelectField(Field):
    type = "select"

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)

        self.instance["validate"].update(
            {
                "onlyAvailableItems": False,
            }
        )
