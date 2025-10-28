import factory
import factory.fuzzy

from ..constants import PaymentStatus
from ..models import WorldlineMerchant, WorldlineWebhookConfiguration


class WorldlineMerchantFactory(factory.django.DjangoModelFactory):
    label = "Merchant"
    pspid = "merchant"
    api_key = "key"
    api_secret = "sekrit"

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineMerchant


class WorldlineWebhookConfigurationFactory(factory.django.DjangoModelFactory):
    pspid = factory.Sequence(lambda n: f"webhook-{n:03d}")
    webhook_key_id = factory.Faker("uuid4")
    webhook_key_secret = factory.Faker("pystr", min_chars=40, max_chars=40)

    class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
        model = WorldlineWebhookConfiguration


class AmountOfMoneyFactory(factory.DictFactory):
    amount = factory.Faker("pyint", min_value=1)
    currencyCode = "EUR"


class ReferencesFactory(factory.DictFactory):
    merchantReference = factory.Faker(
        "pystr_format", string_format="AcmeOrder####{{random_int}}"
    )
    paymentReference = factory.Faker("pystr_format", string_format="#{{random_int}}")


class CardFactory(factory.DictFactory):
    cardNumber = factory.Faker(
        "pystr_format", string_format="***********####{{random_int}}"
    )
    expiryDate = factory.Faker("pystr_format", string_format="####{{random_int}}")


class FraudResultsFactory(factory.DictFactory):
    avsResult = factory.Faker("pystr_format", string_format="#{{random_int}}")
    cvvResult = factory.Faker("pystr_format", string_format="#{{random_int}}")
    fraudServiceResult = "no-advice"


class ThreeDSecureResultsFactory(factory.DictFactory):
    authenticationAmount = factory.SubFactory(AmountOfMoneyFactory)


class CardPaymentMethodSpecificOutputFactory(factory.DictFactory):
    paymentProductId = factory.Faker("pyint")
    authorisationCode = factory.Faker("pyint")
    card = factory.SubFactory(CardFactory)
    fraudResults = factory.SubFactory(FraudResultsFactory)
    threeDSecureResults = factory.SubFactory(ThreeDSecureResultsFactory)


class PaymentOutputFactory(factory.DictFactory):
    amountOfMoney = factory.SubFactory(AmountOfMoneyFactory)
    references = factory.SubFactory(ReferencesFactory)
    paymentMethod = "card"
    cardPaymentMethodSpecificOutput = factory.SubFactory(
        CardPaymentMethodSpecificOutputFactory
    )


class StatusOutputFactory(factory.DictFactory):
    isCancellable = True
    statusCode = factory.Faker("pyint")
    statusCodeChangeDateTime = factory.Faker(
        "pystr_format", string_format="##############{{random_int}}"
    )
    isAuthorized = True


class PaymentRequestFactory(factory.DictFactory):
    id = factory.Faker(
        "pystr_format", string_format="##############################{{random_int}}"
    )

    paymentOutput = factory.SubFactory(PaymentOutputFactory)
    status = factory.fuzzy.FuzzyChoice(PaymentStatus.values)
    statusOutput = factory.SubFactory(StatusOutputFactory)


# see https://docs.connect.worldline-solutions.com/documentation/webhooks/event-structure/
class WebhookEventRequestFactory(factory.DictFactory):
    id = factory.Faker("uuid4")
    apiVersion = "v1"
    type = "payment.created"
    merchantId = factory.Faker("pyint")
    payment = factory.SubFactory(PaymentRequestFactory)
