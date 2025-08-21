from typing import TypedDict

from openforms.payments.constants import PaymentStatus


class AmountOfMoney(TypedDict):
    amount: int
    currencyCode: str


class References(TypedDict):
    merchantReference: str
    paymentReference: str


class Card(TypedDict):
    cardNumber: str
    expiryDate: str


class FraudResults(TypedDict):
    avsResult: str
    cvvResult: str
    fraudServiceResult: str


class ThreeDSecureResults(TypedDict):
    authenticationAmount: AmountOfMoney


class CardPaymentMethodSpecificOutput(TypedDict):
    paymentProductId: int
    authorisationCode: int
    card: Card
    fraudResults: FraudResults
    threeDSecureResults: ThreeDSecureResults


class PaymentOutput(TypedDict):
    amountOfMoney: AmountOfMoney
    references: References
    paymentMethod: str
    cardPaymentMethodSpecificOutput: CardPaymentMethodSpecificOutput


class StatusOutput(TypedDict):
    isCancellable: bool
    statusCode: int
    statusCodeChangeDateTime: str
    isAuthorized: bool


class PaymentRequest(TypedDict):
    id: str

    paymentOutput: PaymentOutput
    status: PaymentStatus
    statusOutput: StatusOutput


class WebhookEventRequest(TypedDict):
    id: str
    apiVersion: str
    type: str
    merchantId: str
    payment: PaymentRequest
