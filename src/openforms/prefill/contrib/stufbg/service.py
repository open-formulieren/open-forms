from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.forms.models import FormVariable
from openforms.prefill.contrib.family_members.plugin import (
    PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER,
)
from openforms.variables.constants import FormVariableSources
from stuf.stuf_bg.checks import check_config
from stuf.stuf_bg.exceptions import InvalidPluginConfiguration


def check_stufbg_config_for_partners() -> str:
    global_config = GlobalConfiguration.get_solo()
    if global_config.family_members_data_api != FamilyMembersDataAPIChoices.stuf_bg:
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
