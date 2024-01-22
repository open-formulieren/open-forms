from typing import Any

from openforms.authentication.constants import AuthAttribute
from openforms.config.models import GlobalConfiguration
from openforms.submissions.models import Submission
from zgw_consumers_ext.api_client import build_client

from ..constants import DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER
from ..models import BRPPersonenRequestOptions, HaalCentraalConfig
from .brp import CLIENT_CLS_FOR_VERSION as BRP_CLIENT_CLS_FOR_VERSION, BRPClient


class NoServiceConfigured(RuntimeError):
    pass


def get_brp_client(submission: Submission | None = None, **kwargs: Any) -> BRPClient:
    """Get an instance of a BRP client.

    :param submission: the current submission in the context of the client usage.
        This submission will be used to fetch headers overrides.
    :param kwargs: additional kwargs to be passed to the client class.
    """

    config = HaalCentraalConfig.get_solo()
    global_config = GlobalConfiguration.get_solo()
    assert isinstance(config, HaalCentraalConfig)
    assert isinstance(global_config, GlobalConfiguration)
    if not (service := config.brp_personen_service):
        raise NoServiceConfigured("No BRP service configured!")

    if submission is not None:
        request_options = getattr(
            submission.form, "brp_personen_request_options", BRPPersonenRequestOptions()
        )
        if (
            submission.registrator
            and submission.registrator.attribute is AuthAttribute.employee_id
        ):
            gebruiker = submission.registrator.value
        else:
            gebruiker = DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER
    else:
        gebruiker = DEFAULT_HC_BRP_PERSONEN_GEBRUIKER_HEADER
        request_options = BRPPersonenRequestOptions()

    origin_oin = global_config.organization_oin
    doelbinding = (
        request_options.brp_personen_purpose_limitation_header_value
        or config.default_brp_personen_purpose_limitation_header_value
    )
    verwerking = (
        request_options.brp_personen_processing_header_value
        or config.default_brp_personen_processing_header_value
    )

    version = config.brp_personen_version
    ClientCls = BRP_CLIENT_CLS_FOR_VERSION.get(version)
    if ClientCls is None:
        raise RuntimeError(
            f"No suitable client class configured for API version {version}"
        )

    return build_client(
        service,
        client_factory=ClientCls,
        origin_oin=origin_oin,
        doelbinding=doelbinding,
        verwerking=verwerking,
        gebruiker=gebruiker,
        **kwargs,
    )
