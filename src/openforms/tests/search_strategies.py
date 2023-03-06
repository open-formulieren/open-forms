from string import ascii_letters

from django.core.exceptions import ValidationError

from hypothesis import strategies as st

from openforms.forms.models.form_variable import variable_key_validator
from openforms.typing import JSONPrimitive, JSONValue

json_primitives: st.SearchStrategy[JSONPrimitive]
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_infinity=False, allow_nan=False),
    st.text(),
)


def json_collections(
    values,
) -> st.SearchStrategy[dict[str, JSONValue] | list[JSONValue]]:
    return st.one_of(
        st.dictionaries(keys=st.text(), values=values),
        st.lists(values),
    )


def json_values(*, max_leaves: int = 15) -> st.SearchStrategy[JSONValue]:
    return st.recursive(json_primitives, json_collections, max_leaves=max_leaves)


def valid_key(key: str) -> bool:
    try:
        variable_key_validator(key)
    except ValidationError:
        return False
    return True


formio_component_key = st.text(min_size=1, alphabet=".-" + ascii_letters).filter(
    valid_key
)
