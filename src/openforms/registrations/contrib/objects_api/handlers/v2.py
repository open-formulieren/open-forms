"""
Implementation details for the v2 registration handler.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import assert_never, cast

from glom import Assign, Path, glom

from openforms.api.utils import underscore_to_camel
from openforms.formio.service import FormioData
from openforms.formio.typing import Component, EditGridComponent
from openforms.formio.typing.vanilla import FileComponent
from openforms.typing import JSONObject, JSONValue, VariableValue

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
    value: VariableValue,  # can't narrow it down yet, as the type depends on the component type
    transform_to_list: list[str] | None = None,
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
    :arg transform_to_list: transform_to_list: Component keys in this list will be sent
      as an array of values rather than the default object-shape for selectboxes
      components.
    :arg component: If the variable corresponds to a Formio component, the component
      definition is provided, otherwise ``None``.
    :arg attachment_urls: The registration plugin uploads attachments to a Documents API
      and provides the API resource URL for each attachment. Keys are the data paths in
      the (Formio) submission data, e.g. `myAttachment` or ``repeatingGroups.2.file``.

    :returns: A single assignment spec or collection of assignment specs that specify
      which value needs to be written to which "object path" for the record data, for
      possible deep assignments.
    """
    if transform_to_list is None:
        transform_to_list = []

    variable_key = mapping["variable_key"]
    target_path = Path(*bits) if (bits := mapping.get("target_path")) else None

    # normalize non-primitive date/datetime values for non components so that they're
    # ready for JSON serialization in the proper format
    if isinstance(value, date | datetime) and not component:
        value = value.isoformat()

    # transform the value within the context of the component
    # TODO: convert this in a proper registry in due time so we can use better type
    # annotations
    match component:
        case {"type": "date" | "datetime" | "time", "multiple": True}:
            assert isinstance(value, list)
            value = [v.isoformat() if value else "" for v in value]  # pyright: ignore[reportAttributeAccessIssue, reportOptionalMemberAccess]
        case {"type": "date" | "datetime" | "time"}:
            assert isinstance(value, date | time | datetime | None)
            value = value.isoformat() if value else ""
        case {"type": "addressNL"}:
            assert isinstance(value, dict)
            value = value.copy()
            value.pop("secretStreetCity", None)

            # apply the more specific mappings rather than mapping the whole object
            if detailed_mappings := mapping.get("options"):
                return [
                    AssignmentSpec(
                        # the typeddict union of keys/values is lost when looping over them
                        destination=Path(*target_path_bits),  # pyright: ignore[reportGeneralTypeIssues]
                        value=_value,  # pyright: ignore[reportArgumentType]
                    )
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
                return AssignmentSpec(destination=target_path, value=value)  # pyright: ignore[reportArgumentType]

        case {"type": "file"}:
            assert attachment_urls is not None
            value = _transform_file_value(
                cast(FileComponent, component), attachment_urls
            )

        case {"type": "map"}:
            assert isinstance(value, dict)

        case {"type": "editgrid"} if attachment_urls is not None:
            assert isinstance(value, list)
            value = _transform_editgrid_value(
                cast(EditGridComponent, component),
                cast(list[JSONObject], value),
                attachment_urls=attachment_urls,
                key_prefix=variable_key,
            )
        case {"type": "selectboxes"}:
            assert isinstance(value, dict)
            if transform_to_list and variable_key in transform_to_list:
                value = [option for option, is_selected in value.items() if is_selected]
        case {"type": "partners"}:
            assert isinstance(value, list)

            for partner in value:
                assert isinstance(partner, dict)
                assert isinstance(partner["dateOfBirth"], date)
                partner["dateOfBirth"] = partner["dateOfBirth"].isoformat()

                # these are not relevant for the object (at least for now)
                partner.pop("dateOfBirthPrecision", None)
                partner.pop("__addedManually", None)
        case {"type": "children"}:
            assert isinstance(value, list)

            # these are not relevant for the object
            need_removal = (
                "dateOfBirthPrecision",
                "__id",
                "selected",
                "__addedManually",
            )

            updated = []
            for child in value:
                assert isinstance(child, dict)
                if child.get("selected") not in (None, True):
                    continue

                assert isinstance(child["dateOfBirth"], date)
                child["dateOfBirth"] = child["dateOfBirth"].isoformat()

                for attribute in need_removal:
                    child.pop(attribute, None)

                updated.append(child)

            value = updated

        # not a component or standard behaviour where no transformation is necessary
        case None | _:
            pass

    assert target_path is not None

    # We can "safely" cast to a JSONValue now that the value has been processed
    value = cast(JSONValue, value)
    return AssignmentSpec(destination=target_path, value=value)


def _transform_file_value(
    component: FileComponent,
    attachment_urls: dict[str, list[str]],
    key_prefix: str = "",
) -> str | list[str]:
    """
    Transform a single file component value according to the component configuration.
    """
    key = component["key"]
    multiple = component.get("multiple", False)

    # it's possible keys are missing because there are no uploads at all for the
    # component.
    data_path = f"{key_prefix}.{key}" if key_prefix else key
    upload_urls = attachment_urls.get(data_path, [])

    match upload_urls:
        # if there are no uploads and it's a single component -> normalize to empty string
        case [] if not multiple:
            return ""

        # if there's an upload and it's a single component -> return the single URL string
        case list() if upload_urls and not multiple:
            return upload_urls[0]

        # otherwise just return the list of upload URLs
        case list():
            assert multiple
            return upload_urls

        case _:
            assert_never(upload_urls)


def _transform_editgrid_value(
    component: EditGridComponent,
    value: list[JSONObject],
    attachment_urls: dict[str, list[str]],
    key_prefix: str,
) -> list[JSONObject]:
    nested_components = component["components"]

    items: list[JSONObject] = []

    # process file uploads inside (nested) repeating groups
    for index, item in enumerate(value):
        item_values = FormioData(item)

        for nested_component in nested_components:
            key = nested_component["key"]

            match nested_component:
                case {"type": "file"}:
                    item_values[key] = _transform_file_value(
                        cast(FileComponent, nested_component),
                        attachment_urls=attachment_urls,
                        key_prefix=f"{key_prefix}.{index}",
                    )
                case {"type": "editgrid"}:
                    nested_items = item_values[key]
                    assert isinstance(nested_items, list)
                    item_values[key] = _transform_editgrid_value(
                        cast(EditGridComponent, nested_component),
                        value=cast(list[JSONObject], nested_items),
                        attachment_urls=attachment_urls,
                        key_prefix=f"{key_prefix}.{index}.{key}",
                    )

        # Argument ``value`` is already a list of JSON objects, so we can cast here to
        # a JSON object
        items.append(cast(JSONObject, item_values.data))

    return items
