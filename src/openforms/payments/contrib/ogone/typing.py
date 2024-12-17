from typing import TypedDict

from .models import OgoneMerchant


class PaymentOptions(TypedDict):
    merchant_id: OgoneMerchant  # FIXME: key is badly named in the serializer
    title_template: str
    com_template: str
