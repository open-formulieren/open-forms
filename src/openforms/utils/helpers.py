from collections.abc import Callable

from django.db import models

from mozilla_django_oidc_db.utils import obfuscate_claim_value as _obfuscate

from openforms.typing import JSONValue


def get_charfield_max_length(
    model_or_instance: models.Model | type[models.Model], field_name: str
) -> int:
    return model_or_instance._meta.get_field(field_name).max_length


def truncate_str_if_needed(original_str: str, new_str: str, max_length: int) -> str:
    """
    Given the original string and the new string, return either the original one if
    it doesn't exceed the given max length, or the new one truncated and by adding
    the ellipsis to the original one.
    """
    if len(new_str) <= max_length:
        return new_str

    new_str_length = len(new_str) - len(original_str)
    str_max_length = max_length - new_str_length
    return original_str[: str_max_length - 1] + "\u2026" + new_str[-new_str_length:]


def recursively_apply_function(
    input: JSONValue, func: Callable, transform_leaf: bool = False, *args, **kwargs
) -> JSONValue:
    """
    Take an input - property value and recursively apply ``func`` to it.

    The general purpose is to apply a function recursively to a JSON input.
    Furthermore, other, more specific cases, can be an example of this:

    The ``input`` may be a string to be used as template, another JSON primitive
    that we can't pass through the template engine or a complex JSON object to
    recursively render.

    Returns the same datatype as the input datatype, which should be ready for
    JSON serialization unless transform_leaf flag is set to True where func is
    applied to the nested value as well.
    """
    match input:
        # string primitive (example case: we can throw it into the template engine)
        case str():
            return func(input, *args, **kwargs)

        # collection - map every item recursively
        case list():
            return [
                recursively_apply_function(
                    nested_bit, func, transform_leaf, *args, **kwargs
                )
                for nested_bit in input
            ]

        # mapping - map every key/value pair recursively
        case dict():
            return {
                key: recursively_apply_function(
                    nested_bit, func, transform_leaf, *args, **kwargs
                )
                for key, nested_bit in input.items()
            }

        case _:
            # other primitive or complex object - we can't template this out, so return it
            # unmodified unless the transformation is explicitly requested
            return func(input, *args, **kwargs) if transform_leaf else input


def obfuscate(arg: str, /) -> str:
    """
    General purpose 'obfuscate this string' helper.

    Internally it uses the same utility from :mod:`mozilla_django_oidc_db` because we
    have it at hand anyway, but this is the public API in case we need to vendor
    something like that in here in the future.
    """
    result = _obfuscate(arg)
    assert isinstance(result, str)
    return result
