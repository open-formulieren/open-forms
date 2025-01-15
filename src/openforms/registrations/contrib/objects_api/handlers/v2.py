"""
Implementation details for the v2 registration handler.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from glom import Assign, Path, glom

from openforms.api.utils import underscore_to_camel
from openforms.formio.typing import Component
from openforms.typing import JSONObject, JSONValue

from ..typing import ObjecttypeVariableMapping


@dataclass
class AssignmentSpec:
    """
    Describes where certain values need to be assigned in a target object.
    """

    destination: Path
    """
    The target path where ``value`` shall be assigned.
    """
    value: JSONValue
    """
    The value to assign at ``destination``.
    """


@dataclass
class OutputSpec:
    assignments: Sequence[AssignmentSpec]

    def create_output_data(self) -> JSONObject:
        """
        Assigns the specified assignment configurations to the output data.
        """
        target: JSONObject = {}
        spec = tuple(
            [
                Assign(path=assignment.destination, val=assignment.value, missing=dict)
                for assignment in self.assignments
            ]
        )
        glom(target, spec)
        return target


def process_mapped_variable(
    mapping: ObjecttypeVariableMapping,
    value: (
        JSONValue | date | datetime
    ),  # can't narrow it down yet, as the type depends on the component type
    component: Component | None = None,
) -> AssignmentSpec | Sequence[AssignmentSpec]:
    target_path = Path(*bits) if (bits := mapping.get("target_path")) else None

    # normalize non-primitive date/datetime values so that they're ready for JSON
    # serialization in the proper format
    if isinstance(value, (date, datetime)):
        value = value.isoformat()

    # transform the value within the context of the component
    # TODO: convert this in a proper registry in due time so we can use better type
    # annotations
    match component:
        case {"type": "addressNL"}:
            assert isinstance(value, dict)
            value = value.copy()
            value.pop("secretStreetCity", None)

            # apply the more specific mappings rather than mapping the whole object
            if detailed_mappings := mapping.get("options"):
                return [
                    AssignmentSpec(destination=Path(*target_path_bits), value=_value)
                    for key, target_path_bits in detailed_mappings.items()
                    if target_path_bits
                    # TODO
                    # We don't want to deal with snake/camel conversions, but for
                    # that data model needs to be restructured and the frontend will
                    # be affected too (see comment in PR #4751)
                    if (_key := underscore_to_camel(key)) in value
                    # TODO: I think we should not omit data that has been explicitly
                    # mapped, even though it has falsy values - the key is present in
                    # the submission data! So the next line should be deleted.
                    if (_value := value[_key])
                ]

            # map the address NL values as a whole
            else:
                assert target_path is not None
                return AssignmentSpec(destination=target_path, value=value)

        # multiple files - return an array
        case {"type": "file", "multiple": True}:
            assert isinstance(value, list)

        # single file - return only one element
        case {"type": "file"}:
            assert isinstance(value, list)
            value = value[0] if value else ""

        case {"type": "map"}:
            assert isinstance(value, dict)

        # not a component or standard behaviour where no transformation is necessary
        case None | _:
            pass

    assert target_path is not None
    return AssignmentSpec(destination=target_path, value=value)
