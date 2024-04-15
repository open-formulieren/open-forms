from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from openforms.contrib.brk.checks import BRKValidatorCheck
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration
from openforms.typing import StrOrPromise


@dataclass
class BrokenConfiguration:
    config_name: StrOrPromise
    exception_message: str | None


def check_brk_config_for_addressNL() -> str | None:
    live_forms = Form.objects.live()

    if any(form.has_component("addressNL") for form in live_forms):
        try:
            BRKValidatorCheck.check_config()
        except InvalidPluginConfiguration as e:
            return e.args[0]

    return


def collect_broken_configurations() -> list[BrokenConfiguration]:
    check_brk_configuration = check_brk_config_for_addressNL()

    broken_configurations = []
    if check_brk_configuration:
        broken_configurations.append(
            BrokenConfiguration(
                config_name=_("BRK Client"), exception_message=check_brk_configuration
            )
        )

    return broken_configurations
