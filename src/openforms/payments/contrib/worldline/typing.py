from typing import TypedDict

from openforms.payments.contrib.worldline.models import WorldlineMerchant


class AmountOfMoney(TypedDict):
    currencyCode: str
    amount: int


class Order(TypedDict):
    amountOfMoney: AmountOfMoney


class CheckoutInput(TypedDict):
    returnUrl: str


class PaymentOptions(TypedDict):
    merchant: WorldlineMerchant
