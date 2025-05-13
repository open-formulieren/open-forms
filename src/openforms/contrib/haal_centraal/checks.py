from django.utils.translation import gettext_lazy as _

import requests

from openforms.contrib.haal_centraal.clients import NoServiceConfigured, get_brp_client
from openforms.plugins.exceptions import InvalidPluginConfiguration


def check_config():
    """
    Check if the admin configuration is valid.

    The purpose of this fuction is to simply check the connection to the
    service, so we are using dummy data and an endpoint which does not exist.
    We want to avoid calls to the national registration by using a (valid) BSN.
    """
    try:
        with get_brp_client() as client:
            client.make_config_test_request()
    # Possibly no service or (valid) version is set.
    except NoServiceConfigured as exc:
        raise InvalidPluginConfiguration(_("Service not selected")) from exc
    except RuntimeError as exc:
        msg = exc.args[0] if exc.args else str(exc)
        raise InvalidPluginConfiguration(msg) from exc
    # The request itself can error
    except requests.RequestException as exc:
        raise InvalidPluginConfiguration(
            _("Client error: {exception}").format(exception=exc)
        ) from exc
