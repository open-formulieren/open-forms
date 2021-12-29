from django.urls import reverse
from django.utils.translation import ugettext as _

from zds_client import ClientError

from openforms.config.data import Entry
from openforms.contrib.kvk.client import KVKClientError, KVKSearchClient
from openforms.contrib.kvk.models import KVKConfig


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
        client = KVKSearchClient()
        results = client.query(kvkNummer=check_kvk)
    except KVKClientError as e:
        entry.status = None
        entry.status_message = _("Configuration error: {exception}").format(exception=e)
    except ClientError as e:
        e = e.__cause__ or e
        entry.status = None
        entry.status_message = _("Client error: {exception}").format(exception=e)
    except Exception as e:
        entry.status = False
        entry.status_message = _("Internal error: {exception}").format(exception=e)
    else:
        if not isinstance(results, dict):
            entry.status = False
            entry.status_message = _("Response not a dictionary")
            return entry
        items = results.get("resultaten")
        if not items or not isinstance(items, list):
            entry.status = False
            entry.status_message = _("Response does not contain results")
            return entry
        num = items[0].get("kvkNummer", None)
        if num != check_kvk:
            entry.status = False
            entry.status_message = _(
                "Did not find kvkNummer='{kvk}' in results"
            ).format(kvk=check_kvk)
            return results

        entry.status = True
        entry.status_message = ""

    return entry
