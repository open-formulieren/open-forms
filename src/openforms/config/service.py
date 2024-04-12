from dataclasses import dataclass

from openforms.contrib.brk.checks import BRKValidatorCheck
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration


@dataclass
class BrokenConfiguration:
    config_name: str
    exception_message: str | None


def check_BRK_config_for_addressNl() -> str | None:
    live_forms = Form.objects.live()

    for form in live_forms:
        if form.form_uses_component("addressNL"):
            try:
                BRKValidatorCheck.check_config()
            except InvalidPluginConfiguration as e:
                return e.args[0]
            break

    return


def collect_broken_configurations() -> list[BrokenConfiguration]:
    check_BRK_configuration = check_BRK_config_for_addressNl()

    broken_configurations = []
    if check_BRK_configuration:
        broken_configurations.append(
            BrokenConfiguration(
                config_name="BRK Client", exception_message=check_BRK_configuration
            )
        )

    return broken_configurations
