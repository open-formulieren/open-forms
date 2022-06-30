class BaseField:
    def __init__(self, *args):
        self.key = args[0]

    @property
    def dict_repr(self):
        return self.__dict__

    def __str__(self) -> str:
        return self.key


class Field(BaseField):
    """parent class with basic attributes for a single field(form io)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        content_dict = kwargs.get("content")
        self.description = content_dict.get("description")
        self.validate = {
            "required": content_dict.get("required", kwargs.get("required")),
            "pattern": content_dict.get("pattern"),
        }
        self.defaultValue = content_dict.get("default")
        self.input = True


class FieldSetBase(BaseField):
    """parent class with basic attributes for a fieldset or panel (form io)"""

    def __init__(self, *args):
        super().__init__(*args)
        self.input = False


class FieldSet(FieldSetBase):
    def __init__(self, *args, **kwargs):
        from .entry import convert_json_schema_to_py

        super().__init__(*args)
        self.label = "Field Set"  # docs
        self.type = "fieldset"
        self.components = convert_json_schema_to_py(kwargs["content"])["components"]


class TextField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "textfield"
        self.validate.update(
            {
                "maxLength": kwargs.get("maxLength"),
                "minLength": kwargs.get("minLength"),
            }
        )


class TextAreaField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "textarea"
        self.validate.update(
            {
                "minWords": None,
                "maxWords": None,
            }
        )


class DayField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "day"


class TimeField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "time"


class DateTimeField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "datetime"


class EmailField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "email"


class NumberField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "number"
        self.validate.update(
            {
                "max": kwargs["content"].get("maximum"),
                "min": kwargs["content"].get("minimum"),
                "step": "any",
            }
        )
        is_int = kwargs["content"].get("type")
        if is_int == "integer":
            self.decimalLimit = 0


class SelectBoxesField(Field):
    # note: extension of Radio component
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "selectboxes"
        self.validate.update(
            {
                "onlyAvailableItems": None,
                # "minSelectedCount": None,
                # "maxSelectedCount": None,
            }
        )


class RadioField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "radio"
        self.validate.update(
            {
                "onlyAvailableItems": False,
            }
        )


class SelectField(Field):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = "select"
        self.validate.update(
            {
                "onlyAvailableItems": False,
            }
        )
