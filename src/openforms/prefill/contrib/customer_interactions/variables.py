import structlog

from openforms.forms.models import FormVariable
from openforms.submissions.models import Submission
from openforms.variables.constants import FormVariableSources

from .plugin import PLUGIN_IDENTIFIER

logger = structlog.stdlib.get_logger(__name__)


def fetch_user_variable_from_profile_component(
    submission: Submission, profile_key: str
) -> FormVariable | None:
    """
    fetch user form variable configured for the profile component
    """
    try:
        prefill_form_variable = submission.form.formvariable_set.get(
            source=FormVariableSources.user_defined,
            prefill_plugin=PLUGIN_IDENTIFIER,
            prefill_options__profile_form_variable=profile_key,
        )
    except FormVariable.DoesNotExist:
        return None

    return prefill_form_variable
