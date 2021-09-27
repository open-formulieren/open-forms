from typing import Union

from ..api_models.base import get_model_fields


def get_field_kwargs(field_name, model_field):
    """
    Creates a default instance of a basic non-relational field.
    """
    kwargs = {}

    return kwargs


def extract_model_field_type(model_class, field_name):
    model_field = get_model_fields(model_class)[field_name]
    typehint = model_field.type

    if typehint is None:
        typehint = type(None)

    # support for Optional / List
    if hasattr(typehint, "__origin__"):
        if typehint.__origin__ is list and typehint.__args__:
            subtypehint = typehint.__args__[0]
            raise NotImplementedError("TODO: support collections")

        if typehint.__origin__ is Union:
            typehint = typehint.__args__
            # Optional is ONE type combined with None
            typehint = next(t for t in typehint if t is not None)
    return typehint
