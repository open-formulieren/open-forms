from django.core.exceptions import ValidationError

from hypothesis import strategies as st

from openforms.formio.validators import variable_key_validator
from openforms.typing import JSONPrimitive, JSONValue

language_code = st.sampled_from(["nl", "en", "fy"])


def no_null_byte_characters(**kwargs):
    return st.characters(codec="utf-8", blacklist_characters="\x00", **kwargs)


def json_primitives(text_strategy=st.text()) -> st.SearchStrategy[JSONPrimitive]:
    return st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_infinity=False, allow_nan=False),
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
    return st.text(alphabet=no_null_byte_characters())


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
