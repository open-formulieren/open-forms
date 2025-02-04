"""
Expose hypothesis derived strategies to work with Formio.js data structures.

.. tip:: Use hypothesis strategies to generate random Formio form configurations to
   test implementation robustness.

All the formio component definitions must be JSON-serializable. JSON in itself can
handle NULL bytes inside strings (they turn into \u0000), but JSONB as used by
postgresql and Django's model.JSONField - where we persist these component definitions -
cannot handle NULL bytes. That's why we opt for jsonb_text rather than the plain st.text
strategy.

The component definitions are by no means complete and it is possible hypothesis
generates some combinations with optional fields that semantically make little sense
(like setting both ``deriveStreetName`` and ``deriveCity`` to ``true`` in the textfield
component). This shall have to be iterated on.
"""

from string import ascii_letters, digits

from hypothesis import strategies as st

from openforms.formio.constants import DataSrcOptions
from openforms.tests.search_strategies import jsonb_text


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


def _minimal_component_mapping(component_type: str):
    # some boilerplate with properties that (nearly) all component types have or should
    # have.
    return {
        "type": st.just(component_type),
        "key": formio_key(),
        "label": jsonb_text(),
    }


def textfield_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": jsonb_text(),
        "placeholder": jsonb_text(),
        "multiple": st.booleans(),
        "showCharCount": st.booleans(),
        "autocomplete": st.sampled_from(["email", "givenName"]),
        "deriveStreetName": st.booleans(),
        "deriveCity": st.booleans(),
        "derivePostcode": formio_key(),
        "deriveHouseNumber": formio_key(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("textfield"), optional=optional
    )


def email_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": jsonb_text(),
        "multiple": st.booleans(),
        "autocomplete": st.just("email"),
        "confirmationRecipient": st.booleans(),
    }
    return st.fixed_dictionaries(_minimal_component_mapping("email"), optional=optional)


def date_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        # "defaultValue": st.just("2024-01-01"),  # TODO
    }
    return st.fixed_dictionaries(_minimal_component_mapping("date"), optional=optional)


def datetime_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        # "defaultValue": st.just("2024-01-01"),  # TODO
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("datetime"), optional=optional
    )


def time_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        # "defaultValue": st.just("2024-01-01"),  # TODO
    }
    return st.fixed_dictionaries(_minimal_component_mapping("time"), optional=optional)


def phone_number_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        # "defaultValue": st.just("2024-01-01"),  # TODO
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("phoneNumber"), optional=optional
    )


def file_component():
    mapping = {
        **_minimal_component_mapping("file"),
        "maxNumberOfFiles": st.one_of(
            st.just(None),
            st.integers(min_value=0, max_value=20),
        ),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "multiple": st.booleans(),
        "storage": st.just("url"),
        "url": st.just("https://example.com/api/v2/formio/upload"),
        "file": st.fixed_dictionaries(
            {
                "name": jsonb_text(),
                "type": st.lists(
                    st.sampled_from(["image/png", "application/pdf", "image/jpeg"])
                ),
            }
        ),
        "of": st.fixed_dictionaries(
            {},
            optional={
                "image": st.fixed_dictionaries(
                    {},
                    optional={
                        "resize": st.fixed_dictionaries(
                            {},
                            optional={
                                "apply": st.booleans(),
                                "width": st.integers(min_value=1, max_value=4000),
                                "height": st.integers(min_value=1, max_value=4000),
                            },
                        )
                    },
                )
            },
        ),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def textarea_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": jsonb_text(),
        "multiple": st.booleans(),
        "showCharCount": st.booleans(),
        "rows": st.integers(min_value=1, max_value=300),
        "autoExpand": st.booleans(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("textarea"), optional=optional
    )


def number_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "suffix": jsonb_text(),
        "defaultValue": st.one_of(st.just(None), st.integers(), st.floats()),
        "decimalLimit": st.integers(min_value=0, max_value=10),
        "allowNegative": st.booleans(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("number"), optional=optional
    )


def option():
    return st.fixed_dictionaries(
        {
            "value": jsonb_text(),
            "label": jsonb_text(),
        }
    )


def data_sources():
    return st.sampled_from(
        [
            DataSrcOptions.manual,
            DataSrcOptions.variable,
            DataSrcOptions.referentielijsten,
        ]
    )


def select_component():
    mapping = {
        **_minimal_component_mapping("select"),
        "data": st.fixed_dictionaries(
            {
                "values": st.lists(option(), min_size=0),
            }
        ),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": jsonb_text(),
        "dataSrc": st.just("values"),
        "openForms": st.fixed_dictionaries(
            {},
            optional={
                "dataSrc": data_sources(),
                # TODO: add itemsExpression but only if dataSrc is variable
            },
        ),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def checkbox_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": st.booleans(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("checkbox"), optional=optional
    )


def selectboxes_component():
    mapping = {
        **_minimal_component_mapping("selectboxes"),
        "values": st.lists(option(), min_size=0),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": st.just({}),
        "openForms": st.fixed_dictionaries(
            {},
            optional={
                "dataSrc": data_sources(),
                # TODO: add itemsExpression but only if dataSrc is variable
            },
        ),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def currency_component():
    mapping = {
        **_minimal_component_mapping("currency"),
        "currency": st.just("EUR"),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": st.one_of(st.just(None), st.integers(), st.floats()),
        "decimalLimit": st.integers(min_value=0, max_value=10),
        "allowNegative": st.booleans(),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def radio_component():
    mapping = {
        **_minimal_component_mapping("radio"),
        "values": st.lists(option(), min_size=0),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "defaultValue": jsonb_text(),
        "openForms": st.fixed_dictionaries(
            {},
            optional={
                "dataSrc": data_sources(),
                # TODO: add itemsExpression but only if dataSrc is variable
            },
        ),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def iban_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(_minimal_component_mapping("iban"), optional=optional)


def license_plate_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("licenseplate"), optional=optional
    )


def bsn_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "inputMask": st.just("999999999"),
    }
    return st.fixed_dictionaries(_minimal_component_mapping("bsn"), optional=optional)


def address_nl_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("addressNL"), optional=optional
    )


def np_family_members_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("npFamilyMembers"), optional=optional
    )


def signature_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "footer": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("signature"), optional=optional
    )


def cosign_v2_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("cosign"), optional=optional
    )


def map_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(_minimal_component_mapping("map"), optional=optional)


def nested_components():
    return st.lists(any_component, min_size=1, max_size=5)


def edit_grid_component():
    mapping = {
        **_minimal_component_mapping("editgrid"),
        "components": nested_components(),
    }
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
        "addAnother": jsonb_text(),
        "saveRow": jsonb_text(),
        "removeRow": jsonb_text(),
        "groupLabel": jsonb_text(),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def content_component():
    mapping = {
        **_minimal_component_mapping("content"),
        "html": st.just("<p>Hi-pothesis :wave:</p>"),
    }
    return st.fixed_dictionaries(mapping)


def columns_component():
    column = st.fixed_dictionaries(
        {
            "size": st.integers(min_value=1, max_value=12),
            "sizeMobile": st.integers(min_value=1, max_value=4),
            "components": nested_components(),
        }
    )
    mapping = {
        "type": st.just("columns"),
        "key": formio_key(),
        "columns": st.lists(column),
    }
    return st.fixed_dictionaries(mapping)


def fieldset_component():
    mapping = {
        **_minimal_component_mapping("fieldset"),
        "components": nested_components(),
    }
    optional = {
        "hideHeader": st.booleans(),
    }
    return st.fixed_dictionaries(mapping, optional=optional)


def postcode_component():
    optional = {
        "description": jsonb_text(),
        "tooltip": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("postcode"), optional=optional
    )


def cosign_v1_component():
    optional = {
        "description": jsonb_text(),
    }
    return st.fixed_dictionaries(
        _minimal_component_mapping("coSign"), optional=optional
    )


any_component = st.deferred(
    lambda: st.one_of(
        # INPUTS
        textfield_component(),
        email_component(),
        date_component(),
        datetime_component(),
        time_component(),
        phone_number_component(),
        file_component(),
        textarea_component(),
        number_component(),
        select_component(),
        checkbox_component(),
        selectboxes_component(),
        currency_component(),
        radio_component(),
        # SPECIAL
        iban_component(),
        license_plate_component(),
        bsn_component(),
        address_nl_component(),
        np_family_members_component(),
        signature_component(),
        cosign_v2_component(),
        map_component(),
        edit_grid_component(),
        # LAYOUT
        content_component(),
        columns_component(),
        fieldset_component(),
        # DEPRECATED
        postcode_component(),
        cosign_v1_component(),
    )
)
"""
A search strategy returning any possible/supported Formio component dictionary.
"""
