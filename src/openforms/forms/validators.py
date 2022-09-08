from typing import TYPE_CHECKING, Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from openforms.formio.variables import validate_configuration
from openforms.typing import JSONObject

if TYPE_CHECKING:
    from openforms.forms.models import FormDefinition


def validate_formio_js_schema(value: dict):
    """
    Validate that the passed in value conforms to FormIO.js JSON schema.

    So far, we haven't been able to find a formal description of the schema, so we're
    sticking to what the form builder outputs.
    """
    # very bare-bones checks
    if not isinstance(value, dict):
        raise ValidationError(
            _("Top-level value must be an Object."),
            code="invalid",
        )

    components = value.get("components")
    if components is None:
        raise ValidationError(
            _("Top-level key 'components' is missing."),
            code="invalid",
        )

    if not isinstance(components, list):
        raise ValidationError(
            _("The 'components' value must be a list of components."),
            code="invalid",
        )


def validate_not_deleted(form):
    if form._is_deleted:
        raise ValidationError(
            _("Form is deleted."),
            code="invalid",
        )


def validate_form_definition_is_reusable(
    form_definition: "FormDefinition",
    new_value: Optional[bool] = None,
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


def validate_template_expressions(configuration: JSONObject) -> None:
    """
    Validate that any template expressions in supported properties are correct.

    This runs syntax validation on template fragments inside Formio configuration
    objects.
    """
    errored_components = validate_configuration(configuration)
    if not errored_components:
        return

    all_errors = []

    for key, path in errored_components.items():
        component_path, field = path.rsplit(".", 1)
        err = ValidationError(
            _(
                "The component '{key}' (at JSON path '{path}') has template syntax "
                "errors in the field '{field}'."
            ).format(key=key, path=component_path, field=field),
            code="invalid-template-syntax",
        )
        all_errors.append(err)

    raise ValidationError(all_errors)
