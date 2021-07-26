import dataclasses
from typing import Mapping

from furl import furl

from openforms.payments.constants import UserAction
from openforms.payments.contrib.ogone.data import OgoneRequestParams
from openforms.payments.contrib.ogone.models import OgoneMerchant
from openforms.payments.contrib.ogone.signing import calculate_shasign


@dataclasses.dataclass
class PaymentInfo:
    type: str
    url: str = ""
    data: Mapping[str, str] = None
    method: str = ""


class OgoneClient:
    return_url_params = {
        # lets simplify some negatives into cancel
        "ACCEPTURL": UserAction.accept,
        "DECLINEURL": UserAction.cancel,
        "EXCEPTIONURL": UserAction.exception,
        "CANCELURL": UserAction.cancel,
        "BACKURL": UserAction.cancel,
    }

    def __init__(self, merchant: OgoneMerchant):
        self.merchant = merchant

    def get_payment_info(
        self,
        order_id: str,
        amount_cents: int,
        return_url: str,
        return_action_param: str,
        **extra_params
    ):
        # base params
        params = OgoneRequestParams(
            AMOUNT=amount_cents,
            CURRENCY="EUR",
            LANGUAGE="nl_NL",
            ORDERID=order_id,
            PSPID=self.merchant.pspid,
        )
        # add action variations to base return url
        url = furl(return_url)
        for p, action in self.return_url_params.items():
            url.args[return_action_param] = action
            setattr(params, p, url.url)

        # add any extra params
        for p, v in extra_params.items():
            setattr(params, p, v)

        # collect and sign
        data = params.get_dict()
        data["SHASIGN"] = calculate_shasign(
            data, self.merchant.sha_in_passphrase, self.merchant.hash_algorithm
        )
        # return info
        info = PaymentInfo(
            type="form",
            url=self.merchant.endpoint,
            data=data,
        )
        return info
