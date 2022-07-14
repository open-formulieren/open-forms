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
        self.instance["tableView"] = self.tableView

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
        self.instance.update(
            {"input": self.input, "type": self.type, "hideHeader": self.hideHeader}
        )


class FieldSet(FieldSetBase):

    label = ""
    type = "fieldset"
    tableView = False
    hideHeader = False

    def __init__(self, key: str, required: bool, content: dict) -> None:
        from .entry import convert_json_schema_to_py

        super().__init__(key)
        # label for a fieldset will be populated from attr 'title' of the content
        title = content.get("title")
        self.components = convert_json_schema_to_py(content)["components"]
        self.instance.update({"label": title, "components": self.components})


class TextField(Field):
    type = "textfield"
    tableView = True

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
    tableView = True

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
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class TimeField(Field):
    type = "time"
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class DateTimeField(Field):
    type = "datetime"
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class EmailField(Field):
    type = "email"
    tableView = True

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class NumberField(Field):
    type = "number"
    tableView = False

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
    """user can choose more then one item"""

    type = "selectboxes"
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)
        items = content.get("items", {})
        enum_list = items.get("enum")
        self.instance["validate"].update(
            {
                "onlyAvailableItems": None,
                "maxSelectedCount": len(enum_list),
            }
        )
        _values = [{"label": item, "value": item} for item in enum_list]
        self.instance["values"] = _values
        self.instance["inputType"] = "checkbox"


class CheckboxField(Field):
    type = "checkbox"
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)


class RadioField(Field):
    """user can choose only one item"""

    type = "radio"
    tableView = False

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)
        enum_list = content.get("enum")
        values = [{"label": item, "value": item} for item in enum_list]
        self.instance["values"] = values


class SelectField(Field):
    """user can choose only one item"""

    type = "select"
    tableView = True

    def __init__(self, key: str, required: bool, content: dict):
        super().__init__(key, required, content)
        enum_list = content.get("enum")
        values = [{"label": item, "value": item} for item in enum_list]
        self.instance["data"] = {"values": values}
        self.instance["dataType"] = content.get("type")
