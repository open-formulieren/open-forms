from string import ascii_letters

from django.core.exceptions import ValidationError

from hypothesis import strategies as st

from openforms.forms.models.form_variable import variable_key_validator
from openforms.typing import JSONPrimitive, JSONValue


def json_numbers(min_value=None, max_value=None) -> st.SearchStrategy[JSONPrimitive]:
    return st.one_of(
        st.integers(min_value=min_value, max_value=max_value),
        st.floats(
            min_value=min_value,
            max_value=max_value,
            allow_infinity=False,
            allow_nan=False,
        ),
    )


def json_primitives(text_strategy=st.text()) -> st.SearchStrategy[JSONPrimitive]:
    return st.one_of(
        st.none(),
        st.booleans(),
        json_numbers(),
        text_strategy,
    )


def json_collections(
    values,
    keys_strategy=st.text(),
) -> st.SearchStrategy[dict[str, JSONValue] | list[JSONValue]]:
    return st.one_of(
        st.dictionaries(keys=keys_strategy, values=values),
        st.lists(values),
    )


def json_values(*, max_leaves: int = 15) -> st.SearchStrategy[JSONValue]:
    return st.recursive(json_primitives(), json_collections, max_leaves=max_leaves)


def jsonb_text() -> st.SearchStrategy[str]:
    return st.text().filter(lambda s: "\x00" not in s)


def jsonb_primitives() -> st.SearchStrategy[JSONPrimitive]:
    return json_primitives(text_strategy=jsonb_text())


def jsonb_values(*, max_leaves: int = 15) -> st.SearchStrategy[JSONValue]:
    return st.recursive(
        jsonb_primitives(),
        lambda values: json_collections(values, keys_strategy=jsonb_text()),
        max_leaves=max_leaves,
    )


def valid_key(key: str) -> bool:
    try:
        variable_key_validator(key)
    except ValidationError:
        return False
    return True


def formio_component_key() -> st.SearchStrategy[str]:
    return st.text(min_size=1, alphabet=".-" + ascii_letters).filter(valid_key)
