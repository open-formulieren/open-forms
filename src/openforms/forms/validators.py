from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils.text import get_text_list
from django.utils.translation import gettext_lazy as _

from openforms.formio.service import (
    FormioConfigurationWrapper,
    get_branch_representation,
)
from openforms.formio.typing import Component, FormioConfiguration
from openforms.formio.variables import get_configuration_template_syntax_errors

if TYPE_CHECKING:
    from openforms.forms.models import FormDefinition


def validate_not_deleted(form):
    if form._is_deleted:
        raise ValidationError(
            _("Form is deleted."),
            code="invalid",
        )


def validate_form_definition_is_reusable(
    form_definition: FormDefinition,
    new_value: bool | None = None,
) -> None:
    """
    Validate the integrity of the ``is_reusable`` flag.

    ``is_reusable`` can only be switched from true to false if the form definition is used in less than
    two distinct forms.
    """
    new_value = new_value if new_value is not None else form_definition.is_reusable
    if new_value is False and form_definition.used_in.count() > 1:
        raise ValidationError(
            {
                "is_reusable": _(
                    "This form definition cannot be marked as 'not-reusable' as it is used in multiple existing forms."
                ),
            }
        )


def validate_template_expressions(configuration: FormioConfiguration) -> None:
    """
    Validate that any template expressions in supported properties are correct.

    This runs syntax validation on template fragments inside Formio configuration
    objects.
    """
    errors = get_configuration_template_syntax_errors(configuration)
    if not errors:
        return

    location_error_template = _(', at location "{location}"')
    error_template = _(
        'The component "{label}" (with key "{key}"{location}) has a problem in '
        'the field "{property}": there are template syntax errors in the expression.'
    )
    error_details: list[ValidationError] = []
    for error in errors:
        location = error.parents_representation
        error_message = error_template.format(
            label=error.label,
            key=error.key,
            location=location_error_template.format(location=location)
            if location
            else "",
            property=error.property_name,
        )
        error_details.append(
            ValidationError(
                error_message,
                code="invalid-template-syntax",
            )
        )

    raise ValidationError(error_details)


def validate_no_duplicate_keys(configuration: FormioConfiguration) -> None:
    duplicates = FormioConfigurationWrapper.get_duplicates(configuration)
    errors = [
        _('"{duplicate_key}" (in {paths})').format(
            duplicate_key=duplicate_key,
            paths=", ".join([get_branch_representation(branch) for branch in branches]),
        )
        for duplicate_key, branches in duplicates.items()
    ]
    if errors:
        raise ValidationError(
            _("Detected duplicate keys in configuration: {errors}").format(
                errors=get_text_list(errors, ", ")
            )
        )


def validate_no_duplicate_keys_across_steps(
    current_form_definition: FormDefinition,
    other_form_definitions: Sequence[FormDefinition],
):
    """
    Validate that there are no duplicate keys in a configuration.

    This is important in the case of repeating groups, because no variables are created
    for the components inside the repeating group, so there is no database constraint
    for the keys to be unique. However, non-unique keys cause problems in the case of
    file components.
    """
    component_parents: defaultdict[
        str,  # possibly duplicated component key
        list[
            tuple[
                Sequence[Component],  # tree branch from root to (duplicated) component
                FormDefinition,  # form definition the component is in
            ]
        ],
    ] = defaultdict(list)

    duplicate_keys = []
    for form_definition in [current_form_definition, *other_form_definitions]:
        # when validating accross multiple form definitions, each individual
        # configuration should already have been validated not to contain any duplicates
        config_wrapper = FormioConfigurationWrapper(form_definition.configuration)
        for component in config_wrapper:
            key = component["key"]
            branch = config_wrapper.get_branch(key)
            component_parents[key].append((branch, form_definition))
            if key not in duplicate_keys and len(component_parents[key]) > 1:
                duplicate_keys.append(key)

    if not duplicate_keys:
        return

    # Get readable path for duplicate components
    errors = []
    for duplicate_key in duplicate_keys:
        # If the duplicates are all in other steps, don't raise it here from this step
        if all(
            [
                form_definition != current_form_definition
                for _, form_definition in component_parents[duplicate_key]
            ]
        ):
            continue

        # The readable path is in format "prefix > parent component > child component"
        readable_paths = [
            get_branch_representation(branch, prefix=form_definition.name)
            for branch, form_definition in component_parents[duplicate_key]
        ]
        errors.append(
            _('"{duplicate_key}" (in {paths})').format(
                duplicate_key=duplicate_key, paths=", ".join(readable_paths)
            )
        )

    if errors:
        raise ValidationError(
            _("Detected duplicate keys in configuration: {errors}").format(
                errors=get_text_list(errors, ", ")
            )
        )
