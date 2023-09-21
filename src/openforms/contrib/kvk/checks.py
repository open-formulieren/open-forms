from django.urls import reverse
from django.utils.translation import ugettext as _

from openforms.config.data import Entry

from .client import NoServiceConfigured, get_client
from .models import KVKConfig


def check_kvk_remote_validator():
    entry = Entry(
        # we might not have any prefill backend at all
        name=_("Validation plugin config: {config}").format(config="KVK numbers"),
        actions=[
            (
                _("Configuration"),
                reverse(
                    "admin:kvk_kvkconfig_change",
                    args=(KVKConfig.singleton_instance_id,),
                ),
            )
        ],
    )
    check_kvk = "68750110"
    try:
        with get_client() as client:
            results = client.get_search_results({"kvkNummer": check_kvk})
    except NoServiceConfigured as exc:
        entry.status = None
        entry.error = str(exc)
    except Exception as exc:
        entry.status = False
        entry.error = str(exc)
    else:
        if not isinstance(results, dict):
            entry.status = False
            entry.error = _("Response not a dictionary")
            return entry

        items = results.get("resultaten")
        if not items or not isinstance(items, list):
            entry.status = False
            entry.error = _("Response does not contain results")
            return entry

        num = items[0].get("kvkNummer", None)
        if num != check_kvk:
            entry.status = False
            entry.error = _("Did not find kvkNummer='{kvk}' in results").format(
                kvk=check_kvk
            )
            return results

        entry.status = True

    return entry
