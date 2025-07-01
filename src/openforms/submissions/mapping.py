import dataclasses
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any

from glom import Assign, glom

from openforms.submissions.models import Submission

NOT_SET = object()
SKIP = object()


@dataclasses.dataclass()
class FieldConf:
    # value from RegistrationAttribute
    attribute: str = ""

    # transform value (eg: dates/times etc)
    transform: Callable[[Any], Any] | None = None

    # support attributes from form
    form_field: str = ""

    # support attributes from submission
    submission_auth_info_attribute: str = ""

    # default value if data not found in submission
    default: Any = SKIP

    def __post_init__(self):
        assert not (
            self.attribute and (self.form_field or self.submission_auth_info_attribute)
        )
        assert not (self.form_field and self.submission_auth_info_attribute)
        assert self.attribute or self.form_field or self.submission_auth_info_attribute


type MappingConfig = Mapping[str, str | FieldConf]


def apply_data_mapping[T: MutableMapping[str, Any]](
    submission: Submission,
    mapping_config: MappingConfig,
    component_attribute: str,
    target_dict: T | None = None,
) -> T:
    """
    apply mapping to data and build new data structure based on mapped attributes on the formio component configuration

    example:
        # a component annotated with a meta-attribute.
        component = {
            "key": "firstname",
            "my_plugin_system.some_attribute": XYZ.persoon_voornaam,
        }

        # submitted data
        data = {
            "firstname": "Foo",
        }

        # Submission instance from a Form with a FormDefinition using the given component,
        #    and SubmissionStep(s) holding the given data
        submission = ...

        # the actual mapping sets a path into a nested dictionary and the meta-attribute
        mapping = {
            # map path into structure witha meta-attribute
            "person.name.first": XYZ.persoon_voornaam,

            # or for options use wrap it in FieldConf
            "person.name.first": FieldConf(XYZ.persoon_voornaam, ...=..),
        }

        # calling the mapping function with the submission, the mapping and the name of the component field
        result = apply_data_mapping(submission, mapping, "my_plugin_system.some_attribute")

        # output is the structure described by the keys in the mapping and values from the annotated components
        result == {
            "person": {
                "name": {
                    "first": "Foo",
                }
            }
        }

    """
    if target_dict is None:
        target_dict = dict()

    # build a lookup, also implicitly de-duplicates assigned attributes
    attr_key_lookup = dict()

    for component in submission.form.iter_components(recursive=True):
        key = component.get("key")
        attribute = glom(component, component_attribute, default=None)
        if key and attribute:
            attr_key_lookup[attribute] = key

    # grab submitted data
    data = submission.data

    for target_path, conf in mapping_config.items():
        if isinstance(conf, str):
            # upgrade for code simplicity
            conf = FieldConf(conf)

        # grab value
        value = NOT_SET
        if conf.form_field:
            value = getattr(submission.form, conf.form_field, NOT_SET)
        elif conf.submission_auth_info_attribute and submission.is_authenticated:
            if submission.auth_info.attribute == conf.submission_auth_info_attribute:
                value = submission.auth_info.value
        elif data_key := attr_key_lookup.get(conf.attribute):
            value = data.get(data_key, NOT_SET)

        if value is NOT_SET:
            value = conf.default
        if value is SKIP:
            continue

        if conf.transform:
            value = conf.transform(value)
            if value is SKIP:
                continue

        glom(target_dict, Assign(target_path, value, missing=dict))

    return target_dict


def get_unmapped_data(
    submission,
    mapping_config: Mapping[str, str | FieldConf],
    component_attribute: str,
):
    """
    companion to apply_data_mapping() returns data not mapped to RegistrationAttributes
    """
    data = submission.data

    attr_key_lookup = dict()

    for component in submission.form.iter_components(recursive=True):
        key = component.get("key")
        attribute = glom(component, component_attribute, default=None)
        if key and attribute:
            # NOTE we could delete from data here, BUT
            #  it would also remove fields that have the attribute but
            #  aren't setup in the actual mapping structure
            attr_key_lookup[attribute] = key

    for conf in mapping_config.values():
        if isinstance(conf, str):
            conf = FieldConf(conf)
        if data_key := attr_key_lookup.get(conf.attribute):
            data.pop(data_key, None)

    return data


def get_component(submission, registration_attribute: str, component_attribute: str):
    for component in submission.form.iter_components(recursive=True):
        attribute = glom(component, component_attribute, default=None)
        if attribute == registration_attribute:
            return component
