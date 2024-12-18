from glom import glom

from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration

from .checks import BRKValidatorCheck
from .models import BRKConfig
from .validators import BRK_ZAKELIJK_GERECHTIGD_VALIDATOR_ID


def check_brk_config_for_addressNL() -> str:
    live_forms = Form.objects.live()

    for form in live_forms:
        components = form.iter_components()
        for component in components:
            if (
                component["type"] == "addressNL"
                and (plugins := glom(component, "validate.plugins", default=[]))
                and BRK_ZAKELIJK_GERECHTIGD_VALIDATOR_ID in plugins
                and BRKConfig.get_solo().service
            ):
                try:
                    BRKValidatorCheck.check_config()
                except InvalidPluginConfiguration as e:
                    return e.args[0]

    return ""
