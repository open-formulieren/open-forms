from string import ascii_letters
from typing import Any, Literal

from django.test import SimpleTestCase
from django.utils.translation import gettext as _

from hypothesis import given, strategies as st

from openforms.tests.search_strategies import json_values
from openforms.typing import JSONValue

from ..validators import HeaderValidator, QueryParameterValidator, ValidationError

FIELD_NAME_ALPHABET = "!#$%&'*+-.^_`|~0123456789" + ascii_letters
VCHAR = "".join(chr(i) for i in range(0x21, 0x7F))
OBS_TEXT = "".join(chr(i) for i in range(0x80, 0x100))
SP = "\x20"
HTAB = "\x09"
CR = "\x0d"
LF = "\x0a"
NUL = "\x00"
FIELD_VALUE_ALPHABET = "".join((VCHAR, OBS_TEXT, SP, HTAB))


def field_names() -> st.SearchStrategy[str]:
    """Returns a string that is a valid RFC 9110 Field Name

    > field-name     = token
    > token          = 1*tchar
    > tchar          = "!" / "#" / "$" / "%" / "&" / "'" / "*"
    >                / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~"
    >                / DIGIT / ALPHA
    >                ; any VCHAR, except delimiters
    """
    return st.text(min_size=1, alphabet=FIELD_NAME_ALPHABET)


def field_values() -> st.SearchStrategy[str]:
    """Returns a string that is valid RFC 9110 Field Value

    > field-value    = *field-content
    > field-content  = field-vchar
    >                  [ 1*( SP / HTAB / field-vchar ) field-vchar ]
    > field-vchar    = VCHAR / obs-text
    > obs-text       = %x80-FF
    """
    return st.text(alphabet=FIELD_VALUE_ALPHABET).map(lambda s: s.strip(SP + HTAB))


def whitespace() -> st.SearchStrategy[str]:
    return st.one_of(st.just(SP), st.just(HTAB))


def insert_string(chars: str, s: str, at: Literal[0, 1, 2]) -> str:
    """
    Return string `s` with `chars` inserted at `at`:
     - 0 the start
     - 1 the end
     - 2 the middle
    """
    return chars.join((s[: len(s) // at], s[len(s) // at :])) if at else chars + s


def unquoted_repr(v: Any) -> str:
    "Return the repr without enclosing quotes"
    return repr(v).strip("'\"")


class HeaderValidatorTests(SimpleTestCase):
    validate = HeaderValidator()

    @given(json_values())
    def test_it_doesnot_break_on_arbitrary_json_input(self, userinput: JSONValue):
        # any userinput
        try:
            return_value = self.validate(userinput)
        except ValidationError:
            pass  # should raise ValidationError
        except Exception as e:
            raise self.failureException("Unexpected exception") from e
        else:
            # or be valid
            self.assertEqual(return_value, None)

    @given(st.dictionaries(keys=field_names(), values=field_values()))
    def test_it_validates_well_formed_rfc_9110_headers(self, userinput: dict[str, str]):
        try:
            return_value = self.validate(userinput)
        except ValidationError as e:
            raise self.failureException("Failed valid input") from e
        except Exception as e:
            raise self.failureException("Unexpected exception") from e
        else:
            self.assertEqual(return_value, None)

    @given(
        st.dictionaries(keys=field_names(), values=field_values(), min_size=1),
        whitespace(),
        whitespace(),
        st.booleans(),
    )
    def test_it_invalidates_unstripped_values(
        self, userinput: dict[str, str], whitespace, whitespace2, first_elem
    ):
        """
        > A field value does not include leading or trailing whitespace. When a
        > specific version of HTTP allows such whitespace to appear in a message, a
        > field parsing implementation MUST exclude such whitespace prior to
        > evaluating the field value.

        https://www.rfc-editor.org/rfc/rfc9110#section-5.6.3
        "whitespace" is difined as SP / HTAB
        """
        # take the first or last key of the dict
        key = list(userinput.keys())[0 if first_elem else -1]

        # trailing
        faulty_input = userinput.copy()
        faulty_input[key] = userinput[key] + whitespace
        with self.assertRaisesMessage(ValidationError, "whitespace"):
            self.validate(faulty_input)

        # leading
        faulty_input = userinput.copy()
        faulty_input[key] = whitespace + userinput[key]
        with self.assertRaisesMessage(ValidationError, "whitespace"):
            self.validate(faulty_input)

        # both
        faulty_input = userinput.copy()
        faulty_input[key] = whitespace + userinput[key] + whitespace2
        with self.assertRaisesMessage(ValidationError, "whitespace"):
            self.validate(faulty_input)

    @given(
        name=field_names(),
        value=field_values(),
        control_char=st.sampled_from([CR, LF, NUL]),
        at=st.integers(0, 2),
    )
    def test_it_invalidates_CR_LF_AND_NUL(self, name, value, control_char, at):
        faulty_input = {name: insert_string(control_char, value, at)}

        with self.assertRaisesMessage(ValidationError, unquoted_repr(control_char)):
            self.validate(faulty_input)

    @given(
        name=field_names(),
        value=field_values(),
        invalid_char=st.characters(
            blacklist_characters=FIELD_VALUE_ALPHABET
        ),  # only chars outside the alphabet
        at=st.integers(0, 2),
    )
    def test_it_invalidates_invalid_characters(self, name, value, invalid_char, at):
        faulty_value = insert_string(invalid_char, name, at)
        faulty_input = {name: faulty_value}

        with self.assertRaisesMessage(ValidationError, unquoted_repr(faulty_value)):
            self.validate(faulty_input)

    @given(field_names(), field_values(), whitespace(), st.integers(0, 2))
    def test_it_invalidates_field_names_with_whitespace(
        self, name, value, whitespace, at
    ):
        faulty_name = insert_string(whitespace, name, at)
        faulty_input = {faulty_name: value}

        with self.assertRaisesMessage(ValidationError, unquoted_repr(whitespace)):
            self.validate(faulty_input)

    @given(
        name=field_names(),
        value=field_values(),
        invalid_char=st.characters(
            blacklist_characters=FIELD_NAME_ALPHABET
        ),  # only chars outside the alphabet
        at=st.integers(0, 2),
    )
    def test_it_invalidates_field_names_invalid_characters(
        self, name, value, invalid_char, at
    ):
        faulty_name = insert_string(invalid_char, name, at)
        faulty_input = {faulty_name: value}

        with self.assertRaisesMessage(ValidationError, unquoted_repr(faulty_name)):
            self.validate(faulty_input)


class QueryParameterValidatorTests(SimpleTestCase):
    validate = QueryParameterValidator()

    def test_validate_none_success(self):
        value = None

        self.validate(value)

    def test_validate_success(self):
        value = {
            "foo": ["bar"],
            "bar": ["baz", "qux"],
        }

        try:
            self.validate(value)
        except ValidationError:
            self.fail("Unexpected ValidationError raised")

    def test_validate_is_mapping(self):
        value = "not_a_mapping"

        with self.assertRaisesMessage(
            ValidationError,
            _(
                'Query parameters should have the form {"parameter": ["my", "parameter", "values"]}'
            ),
        ):
            self.validate(value)

    def test_validate_keys_are_strings(self):
        value = {
            "foo": ["bar"],
            1: ["baz"],
        }
        with self.assertRaisesMessage(
            ValidationError,
            _(
                "query parameter key '{parameter!s}' should be a string, but isn't."
            ).format(parameter=1),
        ):
            self.validate(value)

    def test_validate_values_are_lists(self):
        value = {
            "foo": ["bar"],
            "bar": "baz",
        }
        with self.assertRaisesMessage(
            ValidationError,
            _("{parameter!s}: value '{value!s}' should be a list, but isn't.").format(
                parameter="bar",
                value="baz",
            ),
        ):
            self.validate(value)

    def test_validate_values_are_lists_of_strings(self):
        value = {
            "foo": ["bar"],
            "bar": ["baz", 1],
        }
        with self.assertRaisesMessage(
            ValidationError,
            _(
                "{parameter!s}: value '{value!s}' should be a list of strings, but isn't."
            ).format(parameter="bar", value=["baz", 1]),
        ):
            self.validate(value)
