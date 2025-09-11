from typing import NotRequired, TypedDict

from openforms.payments.base import Options

from .models import WorldlineMerchant


class AmountOfMoney(TypedDict):
    currencyCode: str
    amount: int


class References(TypedDict):
    merchantReference: str
    descriptor: str


class Order(TypedDict):
    amountOfMoney: AmountOfMoney
    references: References


class CheckoutInput(TypedDict):
    returnUrl: str
    variant: NotRequired[str]


class CheckoutDetails(TypedDict):
    RETURNMAC: str
    hostedCheckoutId: str


class PaymentOptions(Options):
    merchant: WorldlineMerchant
    _checkoutDetails: CheckoutDetails | None
    variant: str
    descriptor_template: str
