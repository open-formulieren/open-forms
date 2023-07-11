from django.db import models


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
