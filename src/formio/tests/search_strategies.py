from string import ascii_letters, digits

from hypothesis import strategies as st


def formio_key():
    """
    A search strategy that produces valid Formio.js key values.

    Formio.js keys must start and end with an alphanumeric character. Dashes and dots
    as separators are allowed. A value like ``foo..bar`` is valid, in the resulting
    data structure empty strings are used as keys:
    ``{"foo": {"": {"": {"bar": $value}}}}``

    See :func:`openforms.formio.validators.variable_key_validator` for the
    validator implementation.

    This strategy differs slightly from the validator - it will generate keys with a
    maximum length of 100 chars.
    """
    alphabet = ".-" + ascii_letters + digits
    return st.from_regex(r"\A(\w|\w[\w.\-]{0,98}\w)\Z", alphabet=alphabet)
