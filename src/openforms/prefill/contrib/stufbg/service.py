from openforms.config.constants import FamilyMembersDataAPIChoices
from openforms.config.models import GlobalConfiguration
from openforms.forms.models import FormVariable
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.prefill.contrib.family_members.plugin import (
    PLUGIN_IDENTIFIER as FM_PLUGIN_IDENTIFIER,
)
from openforms.variables.constants import FormVariableSources
from stuf.stuf_bg.checks import check_config


def check_stufbg_config_for_partners() -> str:
    live_forms = Form.objects.live()

    global_config = GlobalConfiguration.get_solo()
    if global_config.family_members_data_api != FamilyMembersDataAPIChoices.stuf_bg:
        return ""

    fm_immutable_variables = FormVariable.objects.filter(
        source=FormVariableSources.user_defined,
        prefill_plugin=FM_PLUGIN_IDENTIFIER,
    ).exclude(prefill_options={})

    if fm_immutable_variables:
        for form in live_forms:
            components = form.iter_components()
            for component in components:
                if component["type"] == "partners":
                    try:
                        check_config()
                    except InvalidPluginConfiguration as e:
                        return e.args[0]

    return ""
