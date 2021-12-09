from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from openforms.appointments.contrib.jcc.models import JccConfig
from openforms.appointments.contrib.qmatic.models import QmaticConfig
from openforms.config.data import Entry
from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_configs():
    configs = [
        JccConfig.get_solo(),
        QmaticConfig.get_solo(),
    ]
    return [check_single_config(config) for config in configs]


def check_single_config(config):
    """
    re-implementation of part of the config-checks view:
    - the appointment module doesn't use a register, so we can't iterate available plugins
    - the configuration singletons create the plugin, and the plugin doesn't know about the singletons
    """
    entry = Entry(
        # we might not have any appointment backend at all
        name=_("Afspraken plugin: {config}").format(
            config=str(config._meta.verbose_name)
        ),
        actions=[
            (
                _("Configuration"),
                reverse(
                    f"admin:{config._meta.app_label}_{config._meta.model_name}_change",
                    args=(config.pk,),
                ),
            )
        ],
    )
    try:
        client = config.get_client()
    except Exception as e:
        entry.status = False
        entry.status_message = str(e)
    else:
        # we got something configured
        entry.name = client.get_label()
        entry.actions += client.get_config_actions()

        try:
            client.check_config()
        except InvalidPluginConfiguration as e:
            entry.status = False
            entry.status_message = e
        except NotImplementedError:
            entry.status = None
            entry.status_message = _("Not implemented")
        except Exception as e:
            entry.status = False
            entry.status_message = _("Internal error: {exception}").format(exception=e)
        else:
            entry.status = True
            entry.status_message = ""

    return entry
