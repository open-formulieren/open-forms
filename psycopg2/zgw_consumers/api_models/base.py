"""
Datamodels for ZGW resources.

These are NOT django models.
"""
import uuid
from dataclasses import Field, fields
from datetime import date, datetime
from functools import partial
from typing import Any, Dict, List, Union

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from ._camel_case import underscoreize
from .compat import parse_relativedelta
from .types import JSONObject

__all__ = ["CONVERTERS", "factory", "Model", "ZGWModel"]


def noop(value: Any) -> Any:
    return value


CONVERTERS = {
    type(None): lambda x: None,
    str: noop,
    int: noop,
    float: noop,
    dict: noop,  # TODO: recurse?
    uuid.UUID: lambda value: uuid.UUID(value),
    datetime: parse,
    date: date.fromisoformat,
    relativedelta: parse_relativedelta,
    bool: noop,
}


class Model:
    def __post_init__(self):
        self._type_cast()

    def _type_cast(self):
        model_fields = get_model_fields(self)
        for attr, field in model_fields.items():
            typehint = field.type
            value = getattr(self, attr)

            if typehint is None:
                typehint = type(None)

            # support for Optional / List
            if hasattr(typehint, "__origin__"):
                if typehint.__origin__ is list and typehint.__args__:
                    subtypehint = typehint.__args__[0]
                    if issubclass(subtypehint, Model):
                        setattr(self, attr, factory(subtypehint, value))
                    else:
                        converter = CONVERTERS[subtypehint]
                        new_value = [converter(x) for x in value]
                        setattr(self, attr, new_value)
                    continue

                if typehint.__origin__ is Union:
                    typehint = typehint.__args__

                    if value is None:
                        continue

                    # Optional is ONE type combined with None
                    typehint = next(t for t in typehint if t is not None)

            if isinstance(value, typehint):
                continue

            if issubclass(typehint, Model):
                converter = partial(factory, typehint)
            else:
                converter = CONVERTERS[typehint]
            setattr(self, attr, converter(value))


class ZGWModel(Model):
    @property
    def uuid(self) -> uuid.UUID:
        """
        Because of the usage of UUID4, we can rely on the UUID as identifier.
        """
        _uuid = self.url.split("/")[-1]
        return uuid.UUID(_uuid)


def get_model_fields(model: Union[type, Model]) -> Dict[str, Field]:
    return {field.name: field for field in fields(model)}


def factory(
    model: type, data: Union[JSONObject, List[JSONObject]]
) -> Union[type, List[type]]:
    _is_collection = isinstance(data, list)

    model_fields = get_model_fields(model)
    known_kwargs = list(model_fields.keys())

    def _normalize(kwargs: dict):
        # TODO: this should be an explicit mapping, but *most* of the time with ZGW
        # API's this is fine.
        kwargs = underscoreize(kwargs)
        to_keep = {key: value for key, value in kwargs.items() if key in known_kwargs}
        return to_keep

    if not _is_collection:
        data = [data]

    instances = [model(**_normalize(_raw)) for _raw in data]

    if not _is_collection:
        instances = instances[0]
    return instances
