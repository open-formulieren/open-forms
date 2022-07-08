from .formio_classes import (
    DateField,
    DateTimeField,
    EmailField,
    FieldSet,
    NumberField,
    RadioField,
    SelectBoxesField,
    TextAreaField,
    TextField,
    TimeField,
)


class StringTypeFactory:
    """create instances matching form io classes based on JSON schema type==string"""

    CLASS_TYPES = {
        "date": DateField,
        "time": TimeField,
        "date-time": DateTimeField,
        "email": EmailField,
    }

    @classmethod
    def create(cls, key, required, content):
        """make distinction for string format fields"""
        type_format = content.get("format", None)
        _class = cls.CLASS_TYPES.get(type_format, None)
        if type_format is not None:
            return _class(key, required, content)
        else:
            if content.get("maxLength", None) is not None:
                return TextField(key, required, content)
            else:
                return TextAreaField(key, required, content)


class FieldFactory:
    """create instances matching form io classes based on different JSON schema types"""

    CLASS_TYPES = {
        "string": StringTypeFactory,
        "number": NumberField,
        "integer": NumberField,
        "array": SelectBoxesField,
        "boolean": RadioField,
        "object": FieldSet,
    }

    @classmethod
    def create(cls, key, required, content):
        # here try/except?
        _type = content.get("type", "")
        _class = cls.CLASS_TYPES.get(_type, "class not found")
        if _type == "string":
            obj = StringTypeFactory.create(key, required, content)
        else:
            obj = _class(key, required, content)
        return obj
