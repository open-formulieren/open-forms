"""
Dynamically build serializers for Formio component trees.

The reference implementation for the validation behaviour is the JS implementation of
Formio.js 4.13.x:
https://github.com/formio/formio.js/blob/4.13.x/src/validator/Validator.js.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING

import structlog
from glom import assign, glom
from rest_framework import serializers

from formio_types import AnyComponent, FormioConfiguration

from .datastructures import FormioConfig, FormioData
from .utils import iter_components

if TYPE_CHECKING:
    from .registry import ComponentRegistry

logger = structlog.stdlib.get_logger(__name__)

FORMIO_CONFIG_CONTEXT_KEY = "_formio_config"

type FieldOrNestedFields = serializers.Field | dict[str, "FieldOrNestedFields"]


class StepDataSerializer(serializers.Serializer):
    def apply_hidden_state(
        self,
        components_to_post_process: Collection[AnyComponent],
        fields: Mapping[str, FieldOrNestedFields],
        register: ComponentRegistry,
        parent_key_prefix: str,
    ) -> None:
        """
        Apply the hidden/visible state of the formio components to the serializer.

        Components may be hidden in a static fashing (through the 'hidden' property),
        or be hidden dynamically based on the input data via the 'conditional' property.

        Hidden fields in Formio don't run *any* validation, see the
        ``Component.shouldSkipValidation`` method for reference.
        """
        # initial_data is only set if Serializer(data=...) was used, and we can't take
        # (dynamic) hidden state into account without initial data.
        if not hasattr(self, "initial_data"):
            return

        assert self.context
        assert FORMIO_CONFIG_CONTEXT_KEY in self.context
        formio_config = self.context[FORMIO_CONFIG_CONTEXT_KEY]
        assert isinstance(formio_config, FormioConfig)

        values = FormioData(self.initial_data)
        # loop over all components and delegate application to the registry
        for component in components_to_post_process:
            # Components without submission data do not have serializer fields
            # associated with them.
            assert register.holds_submission_data(component)

            # for components inside edit grids, a lookup key is necessary
            lookup_key = component.key
            if parent_key_prefix:
                lookup_key = f"{parent_key_prefix}.{lookup_key}"

            is_hidden = formio_config.is_hidden(lookup_key, values)
            # we don't have to do anything when the component is visible, regular
            # validation rules apply
            if not is_hidden:
                continue

            # when it's not visible, grab the field from the serializer and remove all
            # the validators to match Formio's behaviour.
            serializer_field = glom(fields, component.key)
            self._remove_validations_from_field(serializer_field)

    def _remove_validations_from_field(self, field: serializers.Field) -> None:
        from .components.vanilla import EditGridField  # circular import

        # Dynamically change the properties of the field to remove validations. CAREFUL
        # when inspecting field instances with a debugger - ``str(field)`` or
        # ``repr(field)`` does *not* reflect the current state of field, only how it
        # was initialized. Mutations are not taken into account here (!!).
        field.required = False
        # note that prefilled fields are validated separately when they're read-only
        # to protect against tampering
        field.allow_null = True
        # reset the validators to the default validators, discarding any additional ones
        # added based on component['validate']
        field.validators = field.get_validators()

        # apply additional attributes depending on the field type
        match field:
            case serializers.CharField():
                field.allow_blank = True

            case serializers.ListField() | EditGridField():
                field.allow_empty = True
                field.min_length = None
                field.max_length = None

            case serializers.ChoiceField():
                field.allow_blank = True

    def _get_required(self) -> bool:
        return any(field.required for field in self.fields.values())

    def _set_required(self, value: bool) -> None:
        # we need a setter because the serializers.Field.__init__ sets the initial
        # value, but we actually derive the value via :meth:`_get_required` above
        # dynamically based on the children, so we just ignore it.
        logger.debug("disabled_setter_call")

    required = property(_get_required, _set_required)  # type:ignore


def dict_to_serializer(
    fields: Mapping[str, FieldOrNestedFields], **kwargs
) -> StepDataSerializer:
    """
    Recursively convert a mapping of field names to a serializer instance.

    Keys are the names of the serializer fields to use, while the values can be
    serializer field instances or nested mappings. Nested mappings result in nested
    serializers.
    """
    serializer = StepDataSerializer(**kwargs)

    for bit, field in fields.items():
        match field:
            case dict() as nested_fields:
                # we do not pass **kwargs to nested serializers, as this should only
                # be provided to the top-level serializer. The context/data is then
                # shared through all children by DRF.
                serializer.fields[bit] = dict_to_serializer(nested_fields)
            # treat default case as a serializer field
            case _:
                serializer.fields[bit] = field

    return serializer


def build_serializer(
    components: Sequence[AnyComponent],
    register: ComponentRegistry,
    parent_key_prefix: str = "",
    **kwargs,
) -> StepDataSerializer:
    """
    Translate a sequence of Formio.js component definitions into a serializer.

    This recursively builds up the serializer fields for each (nested) component and
    puts them into a serializer instance ready for validation.
    """
    assert "context" in kwargs
    assert FORMIO_CONFIG_CONTEXT_KEY in kwargs["context"]

    fields: dict[str, FieldOrNestedFields] = {}

    config = FormioConfiguration(components=components)
    components_to_post_process: list[AnyComponent] = []
    for component in iter_components(config, recurse_into_editgrid=False):
        # Components without submission data do not have serializer fields
        # associated with them.
        if not register.holds_submission_data(component):
            continue

        components_to_post_process.append(component)

        field = register.build_serializer_field(
            component, parent_key_prefix=parent_key_prefix
        )
        assign(obj=fields, path=component.key, val=field, missing=dict)

    serializer = dict_to_serializer(fields, **kwargs)
    serializer.apply_hidden_state(
        components_to_post_process,
        fields,
        register,
        parent_key_prefix=parent_key_prefix,
    )
    return serializer
