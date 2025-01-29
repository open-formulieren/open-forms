"""
Implementation details for the v2 registration handler.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import cast

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
    attachment_urls: dict[str, list[str]] | None = None,
) -> AssignmentSpec | Sequence[AssignmentSpec]:
    """
    Apply post-processing to a mapped variable.

    A mapped variable may have additional options that specify the behaviour of how the
    values are translated before they end up in the Objects API record. Often, these
    transformations are dependent on the component type being processed.

    :arg mapping: The mapping of form variable to destination path, including possible
      component-specific configuration options that influence the mapping behaviour.
    :arg value: The raw value of the form variable for the submission being processed.
      The type/shape of the value depends on the variable/component data type being
      processed and even the component configuration (such as multiple True/False).
    :arg component: If the variable corresponds to a Formio component, the component
      definition is provided, otherwise ``None``.
    :arg attachment_urls: The registration plugin uploads attachments to a Documents API
      and provides the API resource URL for each attachment. Keys are the data paths in
      the (Formio) submission data, e.g. `myAttachment` or ``repeatingGroups.2.file``.

    :returns: A single assignment spec or collection of assignment specs that specify
      which value needs to be written to which "object path" for the record data, for
      possible deep assignments.
    """

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

        case {"type": "file", **rest}:
            assert attachment_urls is not None
            multiple = rest.get("multiple", False)
            upload_urls = attachment_urls[mapping["variable_key"]]

            transformed_value = str | list[str]

            # for multiple uploads, replace the Formio file dicts with our upload URLs
            if multiple:
                transformed_value = upload_urls
            # single file - return only one element *if* there are uploads
            else:
                transformed_value = upload_urls[0] if upload_urls else ""
            value = cast(JSONValue, transformed_value)

        case {"type": "map"}:
            assert isinstance(value, dict)

        # not a component or standard behaviour where no transformation is necessary
        case None | _:
            pass

    assert target_path is not None
    return AssignmentSpec(destination=target_path, value=value)
