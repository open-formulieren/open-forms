"""
Dynamically build serializers for Formio component trees.

The reference implementation for the validation behaviour is the JS implementation of
Formio.js 4.13.x:
https://github.com/formio/formio.js/blob/4.13.x/src/validator/Validator.js.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from glom import assign, glom
from rest_framework import serializers

from openforms.typing import JSONObject

from .datastructures import FormioConfigurationWrapper, FormioData
from .typing import Component
from .utils import is_layout_component, iter_components

if TYPE_CHECKING:
    from .registry import ComponentRegistry

logger = structlog.stdlib.get_logger(__name__)

type FieldOrNestedFields = serializers.Field | dict[str, "FieldOrNestedFields"]


class StepDataSerializer(serializers.Serializer):
    def apply_hidden_state(
        self, configuration: JSONObject, fields: dict[str, FieldOrNestedFields]
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

        config_wrapper = FormioConfigurationWrapper(configuration)

        values = FormioData(self.initial_data)

        # loop over all components and delegate application to the registry
        for component in iter_components(configuration, recurse_into_editgrid=False):
            # XXX: is_visible_in_frontend does not understand editgrid at all yet, which
            # is a broader issue, but also manifests here.
            is_visible = config_wrapper.is_visible_in_frontend(component["key"], values)

            # we don't have to do anything when the component is visible, regular
            # validation rules apply
            if is_visible:
                continue

            # Layout components do not have serializer fields associated with them
            if is_layout_component(component):
                continue

            # when it's not visible, grab the field from the serializer and remove all
            # the validators to match Formio's behaviour.
            serializer_field = glom(fields, component["key"])
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
    fields: dict[str, FieldOrNestedFields], **kwargs
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
                # we do not pass **kwwargs to nested serializers, as this should only
                # be provided to the top-level serializer. The context/data is then
                # shared through all children by DRF.
                serializer.fields[bit] = dict_to_serializer(nested_fields)
            # treat default case as a serializer field
            case _:
                serializer.fields[bit] = field

    return serializer


def build_serializer(
    components: list[Component], register: ComponentRegistry, **kwargs
) -> StepDataSerializer:
    """
    Translate a sequence of Formio.js component definitions into a serializer.

    This recursively builds up the serializer fields for each (nested) component and
    puts them into a serializer instance ready for validation.
    """
    fields: dict[str, FieldOrNestedFields] = {}

    config: JSONObject = {"components": components}
    for component in iter_components(config, recurse_into_editgrid=False):
        if is_layout_component(component):
            continue

        field = register.build_serializer_field(component)
        assign(obj=fields, path=component["key"], val=field, missing=dict)

    serializer = dict_to_serializer(fields, **kwargs)
    serializer.apply_hidden_state(config, fields)
    return serializer
