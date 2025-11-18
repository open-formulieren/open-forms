from django.utils.translation import gettext_lazy as _

from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.checks import check_config
from openforms.forms.models import FormVariable
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.variables.constants import FormVariableSources

from .plugin import PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER


def check_unmatched_variables() -> str:
    live_forms = Form.objects.live()

    fm_immutable_variables = FormVariable.objects.filter(
        source=FormVariableSources.user_defined,
        prefill_plugin=FM_PLUGIN_IDENTIFIER,
        form__in=live_forms,
    ).exclude(prefill_options={})

    if not fm_immutable_variables:
        return ""

    form_component_mappings = [
        {form.pk: component["key"]}
        for form in live_forms
        for component in form.iter_components()
        if component["type"] in ("partners", "children")
    ]

    unmatched = [
        variable.name
        for variable in fm_immutable_variables
        if {variable.form.id: variable.prefill_options["mutable_data_form_variable"]}
        not in form_component_mappings
    ]

    if unmatched:
        return _(
            "There is no component of type 'partners/children' connected to variables '{variables}'."
        ).format(variables=", ".join(unmatched))

    return ""


def check_hc_config_for_family_members() -> str:
    global_config = GlobalConfiguration.get_solo()
    if (
        global_config.family_members_data_api
        != FamilyMembersDataAPIChoices.haal_centraal
    ):
        return ""

    fm_immutable_variables = FormVariable.objects.filter(
        source=FormVariableSources.user_defined,
        prefill_plugin=FM_PLUGIN_IDENTIFIER,
    ).exclude(prefill_options={})

    if not fm_immutable_variables:
        return ""

    try:
        check_config()
    except InvalidPluginConfiguration as e:
        return e.args[0]

    return ""
