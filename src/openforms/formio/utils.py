from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import structlog
from glom import Coalesce, Path, glom
from opentelemetry import trace
from typing_extensions import TypeIs

from openforms.typing import JSONObject

from .typing import Column, ColumnsComponent, Component, FormioConfiguration

logger = structlog.stdlib.get_logger(__name__)
tracer = trace.get_tracer("openforms.formio.utils")

# XXX: we should probably be able to narrow this in Python 3.11 with non-total typed
# dicts.
type ComponentLike = (
    FormioConfiguration | JSONObject | Component | ColumnsComponent | Column
)


def _is_column_component(component: ComponentLike) -> TypeIs[ColumnsComponent]:
    return component.get("type") == "columns"


@tracer.start_as_current_span(
    name="iter-components",
    attributes={
        "span.type": "app",
        "span.subtype": "formio",
        "span.action": "configuration",
    },
)
def iter_components(
    configuration: ComponentLike,
    *,
    recursive=True,
    _is_root=True,
    _mark_root=False,
    recurse_into_editgrid: bool = True,
) -> Iterator[Component]:
    components = configuration.get("components", [])
    if _is_column_component(configuration) and recursive:
        assert not components, "Both nested components and columns found"
        for column in configuration["columns"]:
            yield from iter_components(
                configuration=column,
                recursive=recursive,
                _is_root=False,
                recurse_into_editgrid=recurse_into_editgrid,
            )

    for component in components:
        if _mark_root:
            component["_is_root"] = _is_root
        yield component
        if recursive:
            # TODO: find a cleaner solution - currently just not yielding these is not
            # an option because we have some special treatment for editgrid data which
            # 'copies' the nested components for further processing.
            # Ideally, with should be able to delegate this behaviour to the registered
            # component classes, but that's a refactor too big for the current task(s).
            if component.get("type") == "editgrid" and not recurse_into_editgrid:
                continue
            yield from iter_components(
                configuration=component,
                recursive=recursive,
                _is_root=False,
                recurse_into_editgrid=recurse_into_editgrid,
            )


def _iterate_components_with_configuration_path(
    configuration: ComponentLike, prefix: str = "components", recursive=True
) -> Iterator[tuple[str, Component]]:
    for index, component in enumerate(iter_components(configuration, recursive=False)):
        full_path = f"{prefix}.{index}"
        yield full_path, component

        # could be a component, could be something else
        has_components = "components" in component
        has_columns = "columns" in component

        if has_columns and recursive:
            for col_index, column in enumerate(component["columns"]):
                nested_prefix = f"{full_path}.columns.{col_index}.components"
                yield from _iterate_components_with_configuration_path(
                    column, prefix=nested_prefix
                )
        elif has_components and recursive:
            yield from _iterate_components_with_configuration_path(
                component, prefix=f"{full_path}.components"
            )


@tracer.start_as_current_span(
    name="flatten-by-path",
    attributes={
        "span.type": "app",
        "span.subtype": "formio",
        "span.action": "configuration",
    },
)
def flatten_by_path(configuration: FormioConfiguration) -> dict[str, Component]:
    """
    Flatten the formio configuration.

    Takes a (nested) Formio configuration object and flattens it, using the full
    JSON path as key and the component as value in the returned mapping.
    """

    result = dict(_iterate_components_with_configuration_path(configuration))
    return result


def get_readable_path_from_configuration_path(
    configuration: FormioConfiguration, path: str, prefix: str | None = ""
) -> str:
    """
    Get a readable version of the configuration path.

    For example, for a path ``components.0.components.1`` and a configuration:

        .. code:: json

            {
              "components": [
                {
                  "key": "repeatingGroup",
                  "label": "Repeating Group",
                  "components": [
                    {
                      "key": "item1",
                      "label": "Item 1",
                    },
                    {
                      "key": "item2"
                      "label": "Item 2",
                    }
                  ]
                }
              ]
            }

    it returns ``Repeating Group > Item 1``.
    """
    keys_path = []
    if prefix:
        keys_path.append(prefix)

    previous_path_bit = Path()
    for path_bit in Path.from_text(path).values():
        label_or_key = glom(
            configuration,
            Coalesce(
                Path(previous_path_bit, path_bit, "label"),
                Path(previous_path_bit, path_bit, "key"),
            ),
            default=None,
        )

        if label_or_key:
            keys_path.append(label_or_key)

        previous_path_bit = Path(previous_path_bit, path_bit)

    return " > ".join(keys_path)


def get_component_default_value(component: Component) -> Any | None:
    # Formio has a getter for the:
    # - emptyValue: https://github.com/formio/formio.js/blob/4.13.x/src/components/textfield/TextField.js#L58
    # - defaultValue:
    #    https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/Component.js#L2302
    # If the defaultValue is empty, then the field will be populated with the emptyValue in the form data.
    default_value = component.get("defaultValue")
    if component.get("multiple") and default_value is None:
        return []
    return default_value


# See https://help.form.io/userguide/forms/form-components#input-mask for the
# semantics, and FormioUtils.getInputMask for the implementation.
def conform_to_mask(value: str, mask: str) -> str:
    """
    Given an input and a Formio mask, try to conform the value to the mask.

    If the value is not compatible with the mask, a ``ValueError`` is raised.
    """
    # loop through all the characters of the value and test them against the mask. Note
    # that the value and mask may have different lengths due to non-input characters
    # such as spaces/dashes... Formio only recognizes alphanumeric inputs as variable
    # user input, the rest is part of the mask.
    # NOTE: we don't check for numeric masks or not, let that be handled by Formio itself

    # the final result characters, build from the value and mask
    result: list[str] = []
    char_index, mask_index = 0, 0
    LOOP_GUARD, iterations = 1000, 0

    # maps the formio mask characters to rules to test for alphanumeric chars etc.
    TEST_RULES = {
        "9": lambda c: c.isnumeric(),
        "A": lambda c: c.isalpha(),
        "a": lambda c: c.isalpha(),
        "*": lambda c: c.isalnum(),
    }

    # the loop indices are reset within an iteration, but in the end either a ValueError
    # is raised because of mismatch with the mask, or the value has been re-formatted
    # conforming to the mask and thus has the same length.
    while len(result) != len(mask):
        if iterations > LOOP_GUARD:  # pragma: nocover
            raise RuntimeError("Infinite while-loop detected!")
        iterations += 1

        try:
            char, mask_char = value[char_index], mask[mask_index]
        except IndexError as exc:
            raise ValueError("Ran out of mask or value characters to process") from exc

        test = TEST_RULES.get(mask_char)

        # check if the character matches the mask - if it does, post-process and put
        # it in the result list
        if test and test(char) is True:
            # check if we need to allow uppercase
            if mask_char.islower() and char.isupper():
                char = char.lower()
            result.append(char)
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            mask_index += 1
            continue
        elif char == mask_char:  # literal match -> good to go
            result.append(char)
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            mask_index += 1
            continue
        elif test is not None:  # there is a test, but it didn't pass
            # there was a test, meaning this is an alphanumeric mask of some form. We
            # may potentially skip some separator/formatting chars but ONLY if the
            # current char is not alphanumeric at all. If it is, it doesn't match
            # the expected pattern and we raise a ValueError.
            if char.isalnum():
                raise ValueError(
                    f"Character {char} did not match expected pattern {mask_char}"
                )
            elif mask_char == "*":
                raise ValueError(f"Character {char} was expected to be alphanumeric")
            # at the end of processing a character, advance the indices for the next
            # character
            char_index += 1
            continue
        elif test is None:  # no test -> it's a formatting character
            # if we encounter a formatting character that isn't the current input character,
            # check if the current character is possibly an input (by checking if it's
            # alphanumeric). If it's not, then we have a mismatch, otherwise we insert
            # the formatting character in the result list and process the char again
            # against the next mask char.
            if not char.isalnum():
                raise ValueError(
                    f"Character {char} did not match expected formatting character {mask_char}"
                )

            # the character is probably input, so add the formatter to the result list and
            # keep the current char_index so that we process it again
            result.append(mask_char)
            mask_index += 1
            continue

        else:  # pragma: nocover
            raise RuntimeError(
                f"Unexpected situation! Mask: {mask}, input value: {value}"
            )

    return "".join(result)
