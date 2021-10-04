from furl import furl

from ...base import PaymentInfo
from ...constants import PaymentRequestType, UserAction
from .data import OgoneFeedbackParams, OgoneRequestParams
from .exceptions import InvalidSignature
from .models import OgoneMerchant
from .signing import calculate_sha_in, calculate_sha_out


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
    ) -> PaymentInfo:
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
        data["SHASIGN"] = calculate_sha_in(
            data, self.merchant.sha_in_passphrase, self.merchant.hash_algorithm
        )

        # return info
        info = PaymentInfo(
            type=PaymentRequestType.post,
            url=self.merchant.endpoint,
            data=data,
        )
        return info

    def get_validated_params(self, value_dict) -> OgoneFeedbackParams:
        # for verification check all incoming params
        sign = calculate_sha_out(
            value_dict,
            self.merchant.sha_out_passphrase,
            self.merchant.hash_algorithm,
        )
        if sign != value_dict.get("SHASIGN"):
            raise InvalidSignature("shasign mismatch")

        params = OgoneFeedbackParams.from_dict(value_dict)
        return params
