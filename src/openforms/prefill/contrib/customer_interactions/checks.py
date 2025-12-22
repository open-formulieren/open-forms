from django.utils.translation import gettext_lazy as _

from openforms.emails.digest import InvalidComponentConfiguration
from openforms.forms.models import Form
from openforms.variables.constants import FormVariableSources

from .plugin import PLUGIN_IDENTIFIER


def check_absent_user_variables_for_profile() -> list[InvalidComponentConfiguration]:
    """
    Check if `customerProfile` component with `shouldUpdateCustomerData = True` exists, but
    the related user variable with prefill configuration is not added.
    """
    invalid_configurations: list[InvalidComponentConfiguration] = []
    error_message = _(
        "The component is configured to require updates, but the prefill variable is missing"
    )

    for form in Form.objects.prefetch_related("formvariable_set").live():
        for component in form.iter_components():
            if component["type"] != "customerProfile":
                continue

            if not component["shouldUpdateCustomerData"]:
                continue

            component_key = component["key"]
            if not form.formvariable_set.filter(
                source=FormVariableSources.user_defined,
                prefill_plugin=PLUGIN_IDENTIFIER,
                prefill_options__profile_form_variable=component_key,
            ).exists():
                invalid_configurations.append(
                    InvalidComponentConfiguration(
                        form_id=form.id,
                        form_name=form.name,
                        component_key=component_key,
                        component_type=component["type"],
                        exception_message=error_message,
                    )
                )

    return invalid_configurations
