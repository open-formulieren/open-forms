from .formio_classes import (
    DateTimeField,
    DayField,
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
        "date": DayField,
        "time": TimeField,
        "date-time": DateTimeField,
        "email": EmailField,
    }

    @classmethod
    def create(cls, *args, **kwargs):
        """make distinction for string format fields"""
        type_format = kwargs["content"].get("format")
        _class = cls.CLASS_TYPES.get(type_format, None)
        if type_format is not None:
            return _class(*args, **kwargs)
        else:
            if kwargs["content"].get("maxLength") is not None:
                return TextField(*args, **kwargs)
            else:
                return TextAreaField(*args, **kwargs)


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
    def create(cls, *args, **kwargs):
        _type = kwargs.get("content").get("type")
        _class = cls.CLASS_TYPES.get(_type, None)
        if _type == "string":
            obj = StringTypeFactory.create(*args, **kwargs)
        elif _type == "object":
            obj = FieldSet(*args, **kwargs)
        else:
            obj = _class(*args, **kwargs)
        return obj
