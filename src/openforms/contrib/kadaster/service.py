from openforms.contrib.kadaster.config_check import BAGCheck
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_bag_config_for_address_fields() -> str:
    has_bag_usage = any(
        component.get("deriveCity") or component.get("deriveStreetName")
        for form in Form.objects.live()
        for component in form.iter_components()
    )

    if not has_bag_usage:
        return ""

    try:
        BAGCheck.check_config()
    except InvalidPluginConfiguration as e:
        return e.args[0]

    return ""
