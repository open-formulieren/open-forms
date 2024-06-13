from openforms.contrib.kadaster.config_check import BAGCheck
from openforms.forms.models.form import Form
from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_bag_config_for_address_fields() -> str:
    # this combines the old functionality of deriving the city and streetname
    # via textbox, which is deprecated and will be removed, and the new one via
    # the addressNL component
    has_bag_usage = any(
        component.get("deriveCity")
        or component.get("deriveStreetName")
        or component.get("deriveAddress")
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
